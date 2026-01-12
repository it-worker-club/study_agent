"""Unified error handling for the education tutoring system"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from ..graph.state import AgentState, Message
from .logger import get_logger

if TYPE_CHECKING:
    from ..llm.vllm_client import (
        VLLMClientError,
        VLLMConnectionError,
        VLLMAPIError,
        VLLMTimeoutError,
    )


logger = get_logger(__name__)


class ErrorHandler:
    """
    Unified error handler for the tutoring system.
    
    Provides consistent error handling across all components:
    - LLM service errors
    - Tool execution errors
    - State management errors
    - Routing errors
    """
    
    @staticmethod
    def handle_llm_error(error: Exception, state: AgentState) -> AgentState:
        """
        Handle LLM service errors.
        
        Args:
            error: The exception that occurred
            state: Current agent state
        
        Returns:
            Updated state with error message
        """
        logger.error(f"LLM Error: {error}")
        
        # Determine user-friendly error message based on error type
        error_type = type(error).__name__
        
        if "Connection" in error_type:
            user_message = "抱歉，无法连接到 AI 服务。请检查网络连接或稍后再试。"
        elif "Timeout" in error_type:
            user_message = "抱歉，AI 服务响应超时。请稍后再试。"
        elif "API" in error_type:
            user_message = "抱歉，AI 服务遇到了问题。请稍后再试。"
        else:
            user_message = "抱歉，AI 服务暂时不可用。请稍后再试。"
        
        # Add error message to state
        error_message: Message = {
            "role": "assistant",
            "content": user_message,
            "timestamp": datetime.now(),
            "agent": "system",
        }
        state["messages"].append(error_message)
        
        # Mark that human input is needed
        state["requires_human_input"] = True
        
        # Log detailed error for debugging
        logger.error(
            f"LLM error details: type={type(error).__name__}, "
            f"message={str(error)}, conversation_id={state.get('conversation_id')}"
        )
        
        return state
    
    @staticmethod
    def handle_tool_error(
        error: Exception,
        tool_name: str,
        state: AgentState,
    ) -> AgentState:
        """
        Handle tool execution errors.
        
        Args:
            error: The exception that occurred
            tool_name: Name of the tool that failed
            state: Current agent state
        
        Returns:
            Updated state with fallback message
        """
        logger.error(f"Tool Error ({tool_name}): {error}")
        
        # Provide fallback message
        fallback_message = (
            f"无法访问 {tool_name} 工具，将使用备用方案为您服务。"
            "部分功能可能受限，但我会尽力帮助您。"
        )
        
        error_message: Message = {
            "role": "assistant",
            "content": fallback_message,
            "timestamp": datetime.now(),
            "agent": "system",
        }
        state["messages"].append(error_message)
        
        # Log detailed error for debugging
        logger.error(
            f"Tool error details: tool={tool_name}, type={type(error).__name__}, "
            f"message={str(error)}, conversation_id={state.get('conversation_id')}"
        )
        
        return state
    
    @staticmethod
    def handle_state_error(error: Exception, state: AgentState) -> AgentState:
        """
        Handle state management errors.
        
        Args:
            error: The exception that occurred
            state: Current agent state (may be corrupted)
        
        Returns:
            Safe state with error message
        """
        logger.error(f"State Error: {error}")
        
        # Try to preserve conversation_id if possible
        conversation_id = state.get("conversation_id", "unknown")
        
        # Create a safe minimal state
        from ..graph.helpers import create_initial_state
        
        try:
            safe_state = create_initial_state(conversation_id)
        except Exception as e:
            logger.error(f"Failed to create safe state: {e}")
            # Create absolute minimal state
            safe_state = AgentState(
                messages=[],
                conversation_id=conversation_id,
                user_profile={
                    "user_id": "unknown",
                    "background": None,
                    "skill_level": None,
                    "learning_goals": [],
                    "time_availability": None,
                    "preferences": {},
                },
                current_task=None,
                next_agent=None,
                course_candidates=[],
                learning_plan=None,
                requires_human_input=False,
                human_feedback=None,
                loop_count=0,
                is_complete=False,
            )
        
        # Add error message
        error_message: Message = {
            "role": "assistant",
            "content": "系统遇到了一些问题，已重置对话。请重新开始。",
            "timestamp": datetime.now(),
            "agent": "system",
        }
        safe_state["messages"].append(error_message)
        
        # Log detailed error for debugging
        logger.error(
            f"State error details: type={type(error).__name__}, "
            f"message={str(error)}, conversation_id={conversation_id}"
        )
        
        return safe_state
    
    @staticmethod
    def handle_routing_error(error: Exception, state: AgentState) -> AgentState:
        """
        Handle routing decision errors.
        
        Args:
            error: The exception that occurred
            state: Current agent state
        
        Returns:
            Updated state requesting user clarification
        """
        logger.error(f"Routing Error: {error}")
        
        # Request user clarification
        clarification_message = (
            "抱歉，我不太确定如何帮助您。您是想要：\n"
            "1. 咨询课程推荐\n"
            "2. 制定学习计划\n"
            "3. 其他问题\n\n"
            "请告诉我您的需求，我会尽力帮助您。"
        )
        
        error_message: Message = {
            "role": "assistant",
            "content": clarification_message,
            "timestamp": datetime.now(),
            "agent": "coordinator",
        }
        state["messages"].append(error_message)
        
        # Mark that human input is needed
        state["requires_human_input"] = True
        
        # Log detailed error for debugging
        logger.error(
            f"Routing error details: type={type(error).__name__}, "
            f"message={str(error)}, conversation_id={state.get('conversation_id')}"
        )
        
        return state
    
    @staticmethod
    def handle_generic_error(
        error: Exception,
        state: AgentState,
        context: Optional[str] = None,
    ) -> AgentState:
        """
        Handle generic/unexpected errors.
        
        Args:
            error: The exception that occurred
            state: Current agent state
            context: Optional context about where the error occurred
        
        Returns:
            Updated state with generic error message
        """
        context_str = f" ({context})" if context else ""
        logger.error(f"Generic Error{context_str}: {error}")
        
        # Generic error message
        error_message: Message = {
            "role": "assistant",
            "content": "抱歉，系统遇到了意外错误。请稍后再试或联系技术支持。",
            "timestamp": datetime.now(),
            "agent": "system",
        }
        state["messages"].append(error_message)
        
        # Mark that human input is needed
        state["requires_human_input"] = True
        
        # Log detailed error for debugging
        logger.error(
            f"Generic error details: type={type(error).__name__}, "
            f"message={str(error)}, context={context}, "
            f"conversation_id={state.get('conversation_id')}"
        )
        
        return state
    
    @staticmethod
    def is_recoverable_error(error: Exception) -> bool:
        """
        Determine if an error is recoverable.
        
        Args:
            error: The exception to check
        
        Returns:
            True if error is recoverable, False otherwise
        """
        # Connection and timeout errors are typically recoverable
        error_type = type(error).__name__
        
        recoverable_patterns = ["Connection", "Timeout", "ConnectionError", "TimeoutError"]
        
        return any(pattern in error_type for pattern in recoverable_patterns)
    
    @staticmethod
    def should_retry(error: Exception, attempt: int, max_attempts: int = 3) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (1-indexed)
            max_attempts: Maximum number of attempts
        
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if max attempts reached
        if attempt >= max_attempts:
            return False
        
        # Only retry recoverable errors
        return ErrorHandler.is_recoverable_error(error)
    
    @staticmethod
    def log_error_metrics(
        error: Exception,
        component: str,
        state: Optional[AgentState] = None,
    ) -> None:
        """
        Log error metrics for monitoring.
        
        Args:
            error: The exception that occurred
            component: Component where error occurred
            state: Optional agent state for context
        """
        metrics = {
            "error_type": type(error).__name__,
            "component": component,
            "conversation_id": state.get("conversation_id") if state else None,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"Error metrics: {metrics}")


def handle_vllm_service_failure(state: AgentState) -> AgentState:
    """
    Handle vLLM service unavailability.
    
    This is a convenience function for handling the specific case
    where the vLLM service is completely unavailable.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with service unavailable message
    """
    logger.error("vLLM service is unavailable")
    
    error_message: Message = {
        "role": "assistant",
        "content": (
            "抱歉，AI 服务当前不可用。\n"
            "这可能是由于：\n"
            "1. 服务器维护\n"
            "2. 网络连接问题\n"
            "3. 服务暂时过载\n\n"
            "请稍后再试，或联系系统管理员。"
        ),
        "timestamp": datetime.now(),
        "agent": "system",
    }
    state["messages"].append(error_message)
    state["requires_human_input"] = True
    
    return state
