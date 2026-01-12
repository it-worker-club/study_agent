"""Tool manager with error handling and fallback mechanisms"""

import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

from ..graph.state import CourseInfo, AgentState
from ..utils.logger import get_logger
from ..utils.config import Config
from ..utils.error_handler import ErrorHandler

from .mcp_playwright import (
    MCPPlaywrightClient,
    MCPPlaywrightError,
    create_mcp_playwright_client,
)
from .web_search import (
    WebSearchClient,
    WebSearchError,
    WebSearchResult,
    create_web_search_client,
    parse_search_results,
)

logger = get_logger(__name__)


class ToolType(Enum):
    """Tool types"""
    MCP_PLAYWRIGHT = "mcp_playwright"
    WEB_SEARCH = "web_search"


class ToolExecutionResult:
    """Result of tool execution"""
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[Exception] = None,
        fallback_used: bool = False,
        tool_name: str = "",
    ):
        """
        Initialize tool execution result.
        
        Args:
            success: Whether execution succeeded
            data: Result data
            error: Error if execution failed
            fallback_used: Whether fallback was used
            tool_name: Name of the tool
        """
        self.success = success
        self.data = data
        self.error = error
        self.fallback_used = fallback_used
        self.tool_name = tool_name
        self.timestamp = datetime.now()
    
    def __repr__(self) -> str:
        status = "success" if self.success else "failed"
        fallback = " (fallback)" if self.fallback_used else ""
        return f"ToolExecutionResult({self.tool_name}: {status}{fallback})"


class ToolManager:
    """
    Manages all external tools with error handling and fallback mechanisms.
    
    Provides a unified interface for tool execution with:
    - Automatic retry on transient failures
    - Fallback to alternative tools
    - Error logging and reporting
    - Graceful degradation
    """
    
    def __init__(self, config: Config):
        """
        Initialize tool manager.
        
        Args:
            config: System configuration
        """
        self.config = config
        
        # Initialize tool clients
        self.mcp_client: Optional[MCPPlaywrightClient] = None
        self.web_search_client: Optional[WebSearchClient] = None
        
        # Initialize clients if enabled
        if config.mcp.playwright_enabled:
            try:
                self.mcp_client = create_mcp_playwright_client(config.mcp)
                logger.info("MCP Playwright client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize MCP Playwright client: {e}")
        
        if config.web_search.enabled:
            try:
                self.web_search_client = create_web_search_client(config.web_search)
                logger.info("Web search client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize web search client: {e}")
        
        # Track tool availability
        self.tool_availability = {
            ToolType.MCP_PLAYWRIGHT: self.mcp_client is not None,
            ToolType.WEB_SEARCH: self.web_search_client is not None,
        }
        
        logger.info(f"Tool manager initialized: {self.tool_availability}")
    
    def search_courses(
        self,
        query: str,
        use_fallback: bool = True,
    ) -> ToolExecutionResult:
        """
        Search for courses with fallback support.
        
        Primary: MCP Playwright (GeekTime)
        Fallback: Web search
        
        Args:
            query: Search query
            use_fallback: Whether to use fallback on failure
        
        Returns:
            Tool execution result with course list
        """
        logger.info(f"Searching courses: query='{query}'")
        
        # Try primary tool: MCP Playwright
        if self.mcp_client and self.tool_availability[ToolType.MCP_PLAYWRIGHT]:
            try:
                courses = self._execute_with_retry(
                    lambda: self.mcp_client.search_geektime_courses(query),
                    tool_name="MCP Playwright",
                )
                
                return ToolExecutionResult(
                    success=True,
                    data=courses,
                    tool_name="MCP Playwright",
                )
            
            except Exception as e:
                logger.warning(f"MCP Playwright search failed: {e}")
                
                # Mark tool as temporarily unavailable
                self.tool_availability[ToolType.MCP_PLAYWRIGHT] = False
                
                # Try fallback if enabled
                if use_fallback:
                    return self._search_courses_fallback(query, e)
                else:
                    return ToolExecutionResult(
                        success=False,
                        error=e,
                        tool_name="MCP Playwright",
                    )
        
        # If primary tool not available, use fallback directly
        elif use_fallback:
            logger.info("MCP Playwright not available, using fallback")
            return self._search_courses_fallback(query, None)
        
        else:
            return ToolExecutionResult(
                success=False,
                error=Exception("MCP Playwright not available and fallback disabled"),
                tool_name="MCP Playwright",
            )
    
    def _search_courses_fallback(
        self,
        query: str,
        primary_error: Optional[Exception],
    ) -> ToolExecutionResult:
        """
        Fallback course search using web search.
        
        Args:
            query: Search query
            primary_error: Error from primary tool
        
        Returns:
            Tool execution result
        """
        logger.info(f"Using fallback for course search: query='{query}'")
        
        if not self.web_search_client or not self.tool_availability[ToolType.WEB_SEARCH]:
            return ToolExecutionResult(
                success=False,
                error=Exception("No fallback tool available"),
                tool_name="Web Search (fallback)",
            )
        
        try:
            # Search for courses using web search
            search_query = f"{query} 在线课程"
            results = self._execute_with_retry(
                lambda: self.web_search_client.search(search_query),
                tool_name="Web Search",
            )
            
            # Convert web search results to course format
            courses = self._convert_search_to_courses(results)
            
            return ToolExecutionResult(
                success=True,
                data=courses,
                fallback_used=True,
                tool_name="Web Search (fallback)",
            )
        
        except Exception as e:
            logger.error(f"Fallback search also failed: {e}")
            
            # Return empty results with error
            return ToolExecutionResult(
                success=False,
                error=e,
                fallback_used=True,
                tool_name="Web Search (fallback)",
            )
    
    def get_course_details(self, url: str) -> ToolExecutionResult:
        """
        Get detailed course information.
        
        Args:
            url: Course URL
        
        Returns:
            Tool execution result with course details
        """
        logger.info(f"Getting course details: url={url}")
        
        if not self.mcp_client or not self.tool_availability[ToolType.MCP_PLAYWRIGHT]:
            return ToolExecutionResult(
                success=False,
                error=Exception("MCP Playwright not available"),
                tool_name="MCP Playwright",
            )
        
        try:
            course = self._execute_with_retry(
                lambda: self.mcp_client.get_course_details(url),
                tool_name="MCP Playwright",
            )
            
            return ToolExecutionResult(
                success=True,
                data=course,
                tool_name="MCP Playwright",
            )
        
        except Exception as e:
            logger.error(f"Failed to get course details: {e}")
            
            return ToolExecutionResult(
                success=False,
                error=e,
                tool_name="MCP Playwright",
            )
    
    def search_web(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> ToolExecutionResult:
        """
        Search the web for information.
        
        Args:
            query: Search query
            max_results: Maximum results
        
        Returns:
            Tool execution result with search results
        """
        logger.info(f"Searching web: query='{query}'")
        
        if not self.web_search_client or not self.tool_availability[ToolType.WEB_SEARCH]:
            return ToolExecutionResult(
                success=False,
                error=Exception("Web search not available"),
                tool_name="Web Search",
            )
        
        try:
            results = self._execute_with_retry(
                lambda: self.web_search_client.search(query, max_results),
                tool_name="Web Search",
            )
            
            return ToolExecutionResult(
                success=True,
                data=results,
                tool_name="Web Search",
            )
        
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            
            return ToolExecutionResult(
                success=False,
                error=e,
                tool_name="Web Search",
            )
    
    def search_learning_resources(
        self,
        topic: str,
        skill_level: Optional[str] = None,
    ) -> ToolExecutionResult:
        """
        Search for learning resources on a topic.
        
        Args:
            topic: Learning topic
            skill_level: User's skill level
        
        Returns:
            Tool execution result with learning resources
        """
        logger.info(f"Searching learning resources: topic='{topic}', level={skill_level}")
        
        if not self.web_search_client or not self.tool_availability[ToolType.WEB_SEARCH]:
            return ToolExecutionResult(
                success=False,
                error=Exception("Web search not available"),
                tool_name="Web Search",
            )
        
        try:
            results = self._execute_with_retry(
                lambda: self.web_search_client.search_learning_resources(topic, skill_level),
                tool_name="Web Search",
            )
            
            return ToolExecutionResult(
                success=True,
                data=results,
                tool_name="Web Search",
            )
        
        except Exception as e:
            logger.error(f"Learning resource search failed: {e}")
            
            return ToolExecutionResult(
                success=False,
                error=e,
                tool_name="Web Search",
            )
    
    def _execute_with_retry(
        self,
        func: Callable,
        tool_name: str,
        max_attempts: int = 2,
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            tool_name: Name of the tool
            max_attempts: Maximum retry attempts
        
        Returns:
            Function result
        
        Raises:
            Exception: If all attempts fail
        """
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=5),
            reraise=True,
        )
        def _wrapped():
            return func()
        
        try:
            return _wrapped()
        except RetryError as e:
            logger.error(f"All retry attempts failed for {tool_name}: {e}")
            raise e.last_attempt.exception()
    
    def _convert_search_to_courses(
        self,
        search_results: List[WebSearchResult],
    ) -> List[CourseInfo]:
        """
        Convert web search results to course format.
        
        Args:
            search_results: Web search results
        
        Returns:
            List of course information
        """
        courses: List[CourseInfo] = []
        
        for result in search_results:
            course: CourseInfo = {
                "title": result.title,
                "url": result.url,
                "description": result.snippet,
                "difficulty": "intermediate",  # Default difficulty
                "duration": None,
                "rating": None,
                "source": "web_search",
            }
            courses.append(course)
        
        return courses
    
    def handle_tool_error_in_state(
        self,
        result: ToolExecutionResult,
        state: AgentState,
    ) -> AgentState:
        """
        Handle tool error by updating agent state.
        
        Args:
            result: Tool execution result
            state: Current agent state
        
        Returns:
            Updated agent state
        """
        if result.success:
            return state
        
        # Use error handler to update state
        return ErrorHandler.handle_tool_error(
            result.error,
            result.tool_name,
            state,
        )
    
    def get_tool_status(self) -> Dict[str, bool]:
        """
        Get current status of all tools.
        
        Returns:
            Dictionary of tool availability
        """
        return {
            "mcp_playwright": self.tool_availability[ToolType.MCP_PLAYWRIGHT],
            "web_search": self.tool_availability[ToolType.WEB_SEARCH],
        }
    
    def reset_tool_availability(self) -> None:
        """Reset tool availability flags (for retry after recovery)"""
        self.tool_availability[ToolType.MCP_PLAYWRIGHT] = self.mcp_client is not None
        self.tool_availability[ToolType.WEB_SEARCH] = self.web_search_client is not None
        
        logger.info(f"Tool availability reset: {self.tool_availability}")


def create_tool_manager(config: Config) -> ToolManager:
    """
    Factory function to create tool manager.
    
    Args:
        config: System configuration
    
    Returns:
        Initialized tool manager
    """
    return ToolManager(config)
