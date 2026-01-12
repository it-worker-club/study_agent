"""Learning Planner agent for creating personalized learning plans.

The learning planner agent is responsible for:
- Creating structured learning plans based on user goals
- Breaking down goals into achievable milestones
- Estimating time requirements for each learning phase
- Incorporating recommended courses into learning plans
- Adjusting plans based on user progress
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..graph.state import AgentState, CourseInfo, LearningPlan, Message
from ..llm.vllm_client import VLLMClient, VLLMClientError
from ..tools.web_search import WebSearchClient, WebSearchError
from ..utils.config import AgentConfig
from ..utils.error_handler import ErrorHandler
from ..utils.logger import get_logger


logger = get_logger(__name__)


class LearningPlannerAgent:
    """
    Learning planner agent for creating personalized learning plans.
    
    The learning planner analyzes user goals, available time, and skill level
    to create structured learning plans with milestones, time estimates, and
    recommended courses. It can also search for learning paths and best practices.
    """
    
    # Prompt template for the learning planner
    PROMPT_TEMPLATE = """你是一个专业的学习规划师。你的职责是为用户制定个性化的学习计划。

用户信息：
- 学习目标：{learning_goals}
- 可用时间：{time_availability}
- 当前水平：{skill_level}
- 技术背景：{user_background}

当前任务：{current_task}

对话历史：
{conversation_history}

推荐课程：
{recommended_courses}

学习路径参考资料：
{learning_resources}

请制定一个结构化的学习计划，包括：

1. **学习路径**：将目标分解为 3-5 个里程碑
2. **每个里程碑包含**：
   - 学习内容：具体要学习的知识点和技能
   - 推荐课程：从推荐课程中选择合适的课程（如果有）
   - 预计时间：完成该里程碑需要的时间
   - 验收标准：如何判断该里程碑已完成
   - 学习建议：学习方法和注意事项

3. **总体时间估算**：完成整个学习计划的预计时间

4. **学习建议**：
   - 学习顺序和优先级
   - 如何平衡理论和实践
   - 如何检验学习效果

请以 JSON 格式返回学习计划，格式如下：
{{
    "goal": "学习目标描述",
    "milestones": [
        {{
            "title": "里程碑1标题",
            "content": "学习内容描述",
            "courses": ["课程1标题", "课程2标题"],
            "estimated_time": "2-3周",
            "acceptance_criteria": "验收标准描述",
            "tips": "学习建议"
        }},
        ...
    ],
    "estimated_duration": "总体预计时间",
    "learning_advice": "整体学习建议",
    "summary": "给用户的友好总结和鼓励"
}}

请确保：
1. 里程碑之间有清晰的递进关系
2. 时间估算考虑用户的可用时间
3. 难度适配用户的当前水平
4. 提供具体可执行的建议

请返回有效的 JSON 格式。"""
    
    # Web search prompt for learning resources
    SEARCH_PROMPT = """基于用户的学习目标，决定需要搜索哪些学习路径和最佳实践资料。

学习目标：{learning_goals}
技能水平：{skill_level}

请决定搜索关键词，用于查找：
1. 学习路径和路线图
2. 最佳实践和学习方法
3. 技能树和知识体系

以 JSON 格式返回，格式如下：
{{
    "queries": [
        "Python数据分析学习路径",
        "数据分析技能树"
    ]
}}

请确保返回有效的 JSON 格式。"""
    
    def __init__(
        self,
        vllm_client: VLLMClient,
        web_search_client: WebSearchClient,
        config: AgentConfig,
    ):
        """
        Initialize learning planner agent.
        
        Args:
            vllm_client: vLLM client for LLM inference
            web_search_client: Web search client for learning resources
            config: Agent-specific configuration
        """
        self.vllm_client = vllm_client
        self.web_search_client = web_search_client
        self.config = config
        self.role = "learning_planner"
        self.capabilities = [
            "learning_plan_creation",
            "milestone_planning",
            "time_estimation",
            "learning_path_research",
        ]
        
        logger.info(f"Initialized {self.role} agent with capabilities: {self.capabilities}")
    
    def _format_conversation_history(self, messages: List[Message], max_messages: int = 5) -> str:
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
            
            formatted.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def _extract_user_request(self, state: AgentState) -> str:
        """
        Extract user request from state.
        
        Args:
            state: Current agent state
        
        Returns:
            User request text
        """
        # Use current_task if available
        if state.get("current_task"):
            return state["current_task"]
        
        # Otherwise, get the last user message
        for msg in reversed(state["messages"]):
            if msg["role"] == "user":
                return msg["content"]
        
        return "制定学习计划"
    
    async def _search_learning_resources(self, state: AgentState) -> List[Dict]:
        """
        Search for learning paths and best practices.
        
        Args:
            state: Current agent state
        
        Returns:
            List of web search results
        """
        user_profile = state["user_profile"]
        learning_goals = ", ".join(user_profile.get("learning_goals", []))
        skill_level = user_profile.get("skill_level", "未知")
        
        # Generate search queries using LLM
        prompt = self.SEARCH_PROMPT.format(
            learning_goals=learning_goals,
            skill_level=skill_level,
        )
        
        try:
            response = await self.vllm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=300,
            )
            
            # Parse JSON response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in search query response, using defaults")
                queries = [f"{learning_goals} 学习路径", f"{learning_goals} 最佳实践"]
            else:
                json_str = response[start_idx:end_idx]
                search_data = json.loads(json_str)
                queries = search_data.get("queries", [f"{learning_goals} 学习路径"])
        
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            queries = [f"{learning_goals} 学习路径", f"{learning_goals} 最佳实践"]
        
        # Search for learning resources
        all_resources = []
        for query in queries[:3]:  # Limit to 3 queries
            try:
                logger.info(f"Searching for learning resources: {query}")
                results = self.web_search_client.search(query, max_results=3)
                all_resources.extend([r.to_dict() for r in results])
            except WebSearchError as e:
                logger.error(f"Web search error: {e}")
                continue
        
        logger.info(f"Found {len(all_resources)} learning resources")
        return all_resources
    
    def _format_courses(self, courses: List[CourseInfo]) -> str:
        """
        Format course information for the prompt.
        
        Args:
            courses: List of course information
        
        Returns:
            Formatted course information string
        """
        if not courses:
            return "（暂无推荐课程）"
        
        formatted = []
        for i, course in enumerate(courses, 1):
            formatted.append(
                f"{i}. {course['title']}\n"
                f"   - 难度：{course['difficulty']}\n"
                f"   - 时长：{course.get('duration', '未知')}\n"
                f"   - 描述：{course['description']}"
            )
        
        return "\n\n".join(formatted)
    
    def _format_learning_resources(self, resources: List[Dict]) -> str:
        """
        Format learning resources for the prompt.
        
        Args:
            resources: List of web search results
        
        Returns:
            Formatted learning resources string
        """
        if not resources:
            return "（暂无参考资料）"
        
        formatted = []
        for i, resource in enumerate(resources, 1):
            formatted.append(
                f"{i}. {resource['title']}\n"
                f"   - 来源：{resource['source']}\n"
                f"   - 描述：{resource['snippet']}"
            )
        
        return "\n\n".join(formatted)
    
    def _parse_learning_plan(self, response: str, state: AgentState) -> LearningPlan:
        """
        Parse the LLM response to extract learning plan.
        
        Args:
            response: Raw LLM response text
            state: Current agent state
        
        Returns:
            Parsed learning plan
        
        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to find JSON in the response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            plan_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["goal", "milestones", "estimated_duration"]
            for field in required_fields:
                if field not in plan_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create LearningPlan object
            learning_plan: LearningPlan = {
                "goal": plan_data["goal"],
                "milestones": plan_data["milestones"],
                "recommended_courses": state["course_candidates"],
                "estimated_duration": plan_data["estimated_duration"],
                "created_at": datetime.now(),
                "status": "draft",
            }
            
            return learning_plan
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.debug(f"Response text: {response}")
            raise ValueError(f"Invalid JSON in response: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing learning plan: {e}")
            raise ValueError(f"Failed to parse learning plan: {e}")
    
    async def create_learning_plan(self, state: AgentState) -> Dict[str, any]:
        """
        Create a personalized learning plan for the user.
        
        Args:
            state: Current agent state
        
        Returns:
            Result with learning plan and response message
        
        Raises:
            VLLMClientError: If LLM service fails
        """
        logger.info(f"Learning planner creating plan for conversation {state['conversation_id']}")
        
        # Step 1: Search for learning resources
        learning_resources = await self._search_learning_resources(state)
        
        # Step 2: Build planning prompt
        user_profile = state["user_profile"]
        conversation_history = self._format_conversation_history(state["messages"])
        current_task = self._extract_user_request(state)
        
        prompt = self.PROMPT_TEMPLATE.format(
            learning_goals=", ".join(user_profile.get("learning_goals", [])) or "未设置",
            time_availability=user_profile.get("time_availability") or "未知",
            skill_level=user_profile.get("skill_level") or "未知",
            user_background=user_profile.get("background") or "未知",
            current_task=current_task,
            conversation_history=conversation_history,
            recommended_courses=self._format_courses(state["course_candidates"]),
            learning_resources=self._format_learning_resources(learning_resources),
        )
        
        # Step 3: Generate learning plan
        try:
            response = await self.vllm_client.generate(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            logger.info(f"Generated learning plan (length={len(response)})")
            
            # Step 4: Parse learning plan
            learning_plan = self._parse_learning_plan(response, state)
            
            # Step 5: Extract summary for user message
            # Try to get the summary from the JSON response
            try:
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                json_str = response[start_idx:end_idx]
                plan_data = json.loads(json_str)
                user_message = plan_data.get("summary", response)
            except:
                user_message = response
            
            return {
                "learning_plan": learning_plan,
                "learning_resources": learning_resources,
                "response": user_message,
            }
        
        except VLLMClientError as e:
            logger.error(f"LLM error in learning planner: {e}")
            raise
    
    def get_capabilities(self) -> List[str]:
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
