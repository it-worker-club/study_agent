"""Course Advisor agent for course recommendations and consultation.

The course advisor agent is responsible for:
- Searching for relevant courses on GeekTime using MCP Playwright
- Analyzing course content and matching with user needs
- Providing personalized course recommendations
- Retrieving detailed course information
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..graph.state import AgentState, CourseInfo, Message
from ..llm.vllm_client import VLLMClient, VLLMClientError
from ..tools.mcp_playwright import MCPPlaywrightClient, MCPPlaywrightError
from ..tools.web_search import WebSearchClient, WebSearchError
from ..utils.config import AgentConfig
from ..utils.error_handler import ErrorHandler
from ..utils.logger import get_logger


logger = get_logger(__name__)


class CourseAdvisorAgent:
    """
    Course advisor agent for providing course recommendations.
    
    The course advisor uses MCP Playwright to search GeekTime courses
    and web search to find supplementary learning resources. It analyzes
    user needs and provides personalized recommendations.
    """
    
    # Prompt template for the course advisor
    PROMPT_TEMPLATE = """你是一个专业的课程顾问。你的职责是根据用户的学习目标和背景推荐合适的课程。

用户画像：
- 背景：{user_background}
- 技能水平：{skill_level}
- 学习目标：{learning_goals}
- 可用时间：{time_availability}

当前任务：{current_task}

对话历史：
{conversation_history}

可用的课程信息：
{available_courses}

补充学习资源：
{web_resources}

请执行以下步骤：
1. 分析用户的学习目标和技能水平
2. 从可用课程中选择 3-5 门最合适的课程
3. 为每门课程提供详细的推荐理由，说明：
   - 为什么这门课程适合用户
   - 课程难度是否匹配用户水平
   - 课程内容如何帮助实现学习目标
4. 如果有补充资源，也可以提及

返回格式化的课程推荐，包括：
- 推荐课程列表（至少3门）
- 每门课程的推荐理由
- 学习建议

请用友好、专业的语气回复用户。"""
    
    # Tool selection prompt
    TOOL_SELECTION_PROMPT = """基于用户的需求，决定需要使用哪些工具来搜索课程信息。

用户需求：{user_request}
用户学习目标：{learning_goals}

可用工具：
1. search_geektime: 搜索极客时间课程（适合技术类课程）
2. web_search: 网络搜索补充资源（适合查找教程、文档、最佳实践）

请决定：
1. 需要使用哪些工具（可以多选）
2. 每个工具的搜索关键词

以 JSON 格式返回，格式如下：
{{
    "tools": [
        {{
            "name": "search_geektime",
            "query": "Python数据分析"
        }},
        {{
            "name": "web_search",
            "query": "Python数据分析教程"
        }}
    ]
}}

请确保返回有效的 JSON 格式。"""
    
    def __init__(
        self,
        vllm_client: VLLMClient,
        mcp_client: MCPPlaywrightClient,
        web_search_client: WebSearchClient,
        config: AgentConfig,
    ):
        """
        Initialize course advisor agent.
        
        Args:
            vllm_client: vLLM client for LLM inference
            mcp_client: MCP Playwright client for GeekTime access
            web_search_client: Web search client for supplementary resources
            config: Agent-specific configuration
        """
        self.vllm_client = vllm_client
        self.mcp_client = mcp_client
        self.web_search_client = web_search_client
        self.config = config
        self.role = "course_advisor"
        self.capabilities = [
            "course_search",
            "course_recommendation",
            "course_analysis",
            "web_resource_search",
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
        
        return "课程推荐"
    
    async def _select_tools(self, state: AgentState) -> List[Dict[str, str]]:
        """
        Select which tools to use based on user request.
        
        Args:
            state: Current agent state
        
        Returns:
            List of tool selections with queries
        """
        user_request = self._extract_user_request(state)
        learning_goals = ", ".join(state["user_profile"].get("learning_goals", []))
        
        prompt = self.TOOL_SELECTION_PROMPT.format(
            user_request=user_request,
            learning_goals=learning_goals,
        )
        
        try:
            response = await self.vllm_client.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more deterministic tool selection
                max_tokens=500,
            )
            
            # Parse JSON response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in tool selection response, using defaults")
                return self._get_default_tools(user_request)
            
            json_str = response[start_idx:end_idx]
            tool_selection = json.loads(json_str)
            
            tools = tool_selection.get("tools", [])
            if not tools:
                logger.warning("No tools selected, using defaults")
                return self._get_default_tools(user_request)
            
            logger.info(f"Selected tools: {[t['name'] for t in tools]}")
            return tools
        
        except Exception as e:
            logger.error(f"Error selecting tools: {e}")
            return self._get_default_tools(user_request)
    
    def _get_default_tools(self, user_request: str) -> List[Dict[str, str]]:
        """
        Get default tool selection.
        
        Args:
            user_request: User request text
        
        Returns:
            Default tool selections
        """
        return [
            {"name": "search_geektime", "query": user_request},
            {"name": "web_search", "query": f"{user_request} 学习资源"},
        ]
    
    async def _search_courses(self, tools: List[Dict[str, str]]) -> tuple[List[CourseInfo], List[Dict]]:
        """
        Search for courses using selected tools.
        
        Args:
            tools: List of tool selections
        
        Returns:
            Tuple of (course list, web resources list)
        """
        courses: List[CourseInfo] = []
        web_resources: List[Dict] = []
        
        for tool in tools:
            tool_name = tool.get("name")
            query = tool.get("query", "")
            
            if not query:
                continue
            
            try:
                if tool_name == "search_geektime":
                    logger.info(f"Searching GeekTime: {query}")
                    geektime_courses = self.mcp_client.search_geektime_courses(query)
                    courses.extend(geektime_courses)
                
                elif tool_name == "web_search":
                    logger.info(f"Searching web: {query}")
                    search_results = self.web_search_client.search(query, max_results=5)
                    web_resources.extend([r.to_dict() for r in search_results])
            
            except (MCPPlaywrightError, WebSearchError) as e:
                logger.error(f"Tool error ({tool_name}): {e}")
                # Continue with other tools even if one fails
                continue
        
        logger.info(f"Found {len(courses)} courses and {len(web_resources)} web resources")
        return courses, web_resources
    
    def _format_courses(self, courses: List[CourseInfo]) -> str:
        """
        Format course information for the prompt.
        
        Args:
            courses: List of course information
        
        Returns:
            Formatted course information string
        """
        if not courses:
            return "（暂无可用课程）"
        
        formatted = []
        for i, course in enumerate(courses, 1):
            formatted.append(
                f"{i}. {course['title']}\n"
                f"   - 难度：{course['difficulty']}\n"
                f"   - 时长：{course.get('duration', '未知')}\n"
                f"   - 评分：{course.get('rating', '未知')}\n"
                f"   - 描述：{course['description']}\n"
                f"   - 链接：{course['url']}"
            )
        
        return "\n\n".join(formatted)
    
    def _format_web_resources(self, resources: List[Dict]) -> str:
        """
        Format web resources for the prompt.
        
        Args:
            resources: List of web search results
        
        Returns:
            Formatted web resources string
        """
        if not resources:
            return "（暂无补充资源）"
        
        formatted = []
        for i, resource in enumerate(resources, 1):
            formatted.append(
                f"{i}. {resource['title']}\n"
                f"   - 来源：{resource['source']}\n"
                f"   - 描述：{resource['snippet']}\n"
                f"   - 链接：{resource['url']}"
            )
        
        return "\n\n".join(formatted)
    
    async def recommend_courses(self, state: AgentState) -> Dict[str, any]:
        """
        Analyze user needs and recommend courses.
        
        Args:
            state: Current agent state
        
        Returns:
            Recommendation result with courses and response message
        
        Raises:
            VLLMClientError: If LLM service fails
        """
        logger.info(f"Course advisor analyzing request for conversation {state['conversation_id']}")
        
        # Step 1: Select tools to use
        tools = await self._select_tools(state)
        
        # Step 2: Search for courses and resources
        courses, web_resources = await self._search_courses(tools)
        
        # Step 3: Build recommendation prompt
        user_profile = state["user_profile"]
        conversation_history = self._format_conversation_history(state["messages"])
        current_task = self._extract_user_request(state)
        
        prompt = self.PROMPT_TEMPLATE.format(
            user_background=user_profile.get("background") or "未知",
            skill_level=user_profile.get("skill_level") or "未知",
            learning_goals=", ".join(user_profile.get("learning_goals", [])) or "未设置",
            time_availability=user_profile.get("time_availability") or "未知",
            current_task=current_task,
            conversation_history=conversation_history,
            available_courses=self._format_courses(courses),
            web_resources=self._format_web_resources(web_resources),
        )
        
        # Step 4: Generate recommendation
        try:
            response = await self.vllm_client.generate(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            logger.info(f"Generated course recommendation (length={len(response)})")
            
            return {
                "courses": courses,
                "web_resources": web_resources,
                "response": response,
            }
        
        except VLLMClientError as e:
            logger.error(f"LLM error in course advisor: {e}")
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
