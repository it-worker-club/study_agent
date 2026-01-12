"""Coordinator agent for task routing and orchestration.

The coordinator agent is responsible for:
- Analyzing user input and identifying intent
- Routing requests to appropriate specialized agents
- Managing conversation flow and state transitions
- Requesting user clarification when needed
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional

from ..graph.state import AgentState, Message
from ..llm.vllm_client import VLLMClient, VLLMClientError
from ..utils.config import AgentConfig
from ..utils.error_handler import ErrorHandler
from ..utils.logger import get_logger


logger = get_logger(__name__)


class CoordinatorAgent:
    """
    Coordinator agent for managing task routing and orchestration.
    
    The coordinator analyzes user intent and routes tasks to specialized agents:
    - course_advisor: For course recommendations and inquiries
    - learning_planner: For creating learning plans
    - human_input: When user confirmation is needed
    - end: When the conversation is complete
    """
    
    # Prompt template for the coordinator
    PROMPT_TEMPLATE = """你是一个教育辅导系统的协调器。你的职责是：
1. 理解用户的需求和意图
2. 决定由哪个专业智能体处理任务
3. 在必要时请求用户确认

可用的智能体：
- course_advisor: 课程顾问，负责推荐和介绍课程
- learning_planner: 学习规划师，负责制定学习计划

当前对话历史：
{conversation_history}

用户最新输入：
{user_input}

用户画像：
- 背景：{user_background}
- 技能水平：{skill_level}
- 学习目标：{learning_goals}

请分析用户意图，并决定：
1. next_agent: 下一个执行的智能体（course_advisor/learning_planner/human_input/end）
2. current_task: 任务描述
3. requires_human_input: 是否需要用户确认（true/false）
4. response: 给用户的回复消息（如果需要）

以 JSON 格式返回决策，格式如下：
{{
    "next_agent": "course_advisor",
    "current_task": "推荐 Python 数据分析课程",
    "requires_human_input": false,
    "response": "好的，我来为您推荐一些 Python 数据分析的课程。"
}}

决策规则：
- 如果用户询问课程、想要课程推荐、或询问具体课程信息 → 选择 course_advisor
- 如果用户想要制定学习计划、需要学习路径规划 → 选择 learning_planner
- 如果用户的意图不明确或需要更多信息 → 选择 human_input 并设置 requires_human_input=true
- 如果用户表示结束对话、感谢或再见 → 选择 end
- 如果需要用户确认重要决策（如学习计划） → 设置 requires_human_input=true

请确保返回有效的 JSON 格式。"""
    
    def __init__(self, vllm_client: VLLMClient, config: AgentConfig):
        """
        Initialize coordinator agent.
        
        Args:
            vllm_client: vLLM client for LLM inference
            config: Agent-specific configuration
        """
        self.vllm_client = vllm_client
        self.config = config
        self.role = "coordinator"
        self.capabilities = [
            "intent_recognition",
            "task_routing",
            "conversation_management",
        ]
        
        logger.info(f"Initialized {self.role} agent with capabilities: {self.capabilities}")
    
    def _format_conversation_history(self, messages: list[Message], max_messages: int = 10) -> str:
        """
        Format conversation history for the prompt.
        
        Args:
            messages: List of conversation messages
            max_messages: Maximum number of recent messages to include
        
        Returns:
            Formatted conversation history string
        """
        if not messages:
            return "（暂无对话历史）"
        
        # Get recent messages
        recent_messages = messages[-max_messages:]
        
        formatted = []
        for msg in recent_messages:
            role_label = {
                "user": "用户",
                "assistant": "助手",
                "system": "系统",
            }.get(msg["role"], msg["role"])
            
            agent_info = f"[{msg['agent']}]" if msg.get("agent") else ""
            formatted.append(f"{role_label}{agent_info}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def _extract_user_input(self, messages: list[Message]) -> str:
        """
        Extract the latest user input from messages.
        
        Args:
            messages: List of conversation messages
        
        Returns:
            Latest user input text
        """
        # Find the last user message
        for msg in reversed(messages):
            if msg["role"] == "user":
                return msg["content"]
        
        return "（无用户输入）"
    
    def _build_prompt(self, state: AgentState) -> str:
        """
        Build the prompt for the coordinator.
        
        Args:
            state: Current agent state
        
        Returns:
            Formatted prompt string
        """
        conversation_history = self._format_conversation_history(state["messages"])
        user_input = self._extract_user_input(state["messages"])
        
        user_profile = state["user_profile"]
        user_background = user_profile.get("background") or "未知"
        skill_level = user_profile.get("skill_level") or "未知"
        learning_goals = ", ".join(user_profile.get("learning_goals", [])) or "未设置"
        
        prompt = self.PROMPT_TEMPLATE.format(
            conversation_history=conversation_history,
            user_input=user_input,
            user_background=user_background,
            skill_level=skill_level,
            learning_goals=learning_goals,
        )
        
        return prompt
    
    def _parse_decision(self, response: str) -> Dict[str, any]:
        """
        Parse the LLM response to extract routing decision.
        
        Args:
            response: Raw LLM response text
        
        Returns:
            Parsed decision dictionary
        
        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to find JSON in the response
            # Sometimes LLM adds extra text before/after JSON
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            decision = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["next_agent", "current_task"]
            for field in required_fields:
                if field not in decision:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate next_agent value
            valid_agents = ["course_advisor", "learning_planner", "human_input", "end"]
            if decision["next_agent"] not in valid_agents:
                logger.warning(
                    f"Invalid next_agent: {decision['next_agent']}, defaulting to human_input"
                )
                decision["next_agent"] = "human_input"
                decision["requires_human_input"] = True
            
            # Set defaults for optional fields
            decision.setdefault("requires_human_input", False)
            decision.setdefault("response", None)
            
            return decision
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.debug(f"Response text: {response}")
            raise ValueError(f"Invalid JSON in response: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing decision: {e}")
            raise ValueError(f"Failed to parse decision: {e}")
    
    async def analyze_and_route(self, state: AgentState) -> Dict[str, any]:
        """
        Analyze user intent and make routing decision.
        
        Args:
            state: Current agent state
        
        Returns:
            Routing decision dictionary with keys:
                - next_agent: Next agent to execute
                - current_task: Task description
                - requires_human_input: Whether human input is needed
                - response: Optional response message to user
        
        Raises:
            VLLMClientError: If LLM service fails
            ValueError: If response cannot be parsed
        """
        logger.info(f"Coordinator analyzing intent for conversation {state['conversation_id']}")
        
        # Build prompt
        prompt = self._build_prompt(state)
        
        # Call LLM
        try:
            response = await self.vllm_client.generate(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            logger.debug(f"LLM response: {response}")
            
            # Parse decision
            decision = self._parse_decision(response)
            
            logger.info(
                f"Routing decision: next_agent={decision['next_agent']}, "
                f"task={decision['current_task']}"
            )
            
            return decision
        
        except VLLMClientError as e:
            logger.error(f"LLM error in coordinator: {e}")
            raise
        
        except ValueError as e:
            logger.error(f"Failed to parse coordinator decision: {e}")
            # Return a safe default decision
            return {
                "next_agent": "human_input",
                "current_task": "需要用户澄清",
                "requires_human_input": True,
                "response": "抱歉，我不太确定如何帮助您。能否请您详细说明一下您的需求？",
            }
    
    def get_capabilities(self) -> list[str]:
        """
        Get agent capabilities.
        
        Returns:
            List of capability strings
        """
        return self.capabilities
    
    def get_role(self) -> str:
        """
        Get agent role.
        
        Returns:
            Role string
        """
        return self.role
