"""Performance monitoring and metrics collection for the education tutoring system

This module provides utilities for tracking and logging performance metrics
such as LLM call latency, tool execution time, and conversation statistics.
"""

import functools
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from src.utils.logger import get_logger


logger = get_logger(__name__)


class PerformanceMonitor:
    """Tracks and logs performance metrics for the system"""
    
    def __init__(self):
        """Initialize the performance monitor"""
        self.metrics: Dict[str, list] = {
            "llm_calls": [],
            "tool_executions": [],
            "node_executions": [],
            "conversations": [],
        }
    
    def record_llm_call(
        self,
        agent_name: str,
        duration: float,
        tokens: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """
        Record an LLM API call metric.
        
        Args:
            agent_name: Name of the agent making the call
            duration: Call duration in seconds
            tokens: Number of tokens generated (if available)
            success: Whether the call succeeded
            error: Error message if call failed
        """
        metric = {
            "timestamp": datetime.now(),
            "agent": agent_name,
            "duration": duration,
            "tokens": tokens,
            "success": success,
            "error": error,
        }
        
        self.metrics["llm_calls"].append(metric)
        
        # Log the metric
        if success:
            logger.info(
                f"LLM call completed - Agent: {agent_name}, "
                f"Duration: {duration:.2f}s, Tokens: {tokens or 'N/A'}"
            )
        else:
            logger.error(
                f"LLM call failed - Agent: {agent_name}, "
                f"Duration: {duration:.2f}s, Error: {error}"
            )
    
    def record_tool_execution(
        self,
        tool_name: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """
        Record a tool execution metric.
        
        Args:
            tool_name: Name of the tool
            duration: Execution duration in seconds
            success: Whether the execution succeeded
            error: Error message if execution failed
        """
        metric = {
            "timestamp": datetime.now(),
            "tool": tool_name,
            "duration": duration,
            "success": success,
            "error": error,
        }
        
        self.metrics["tool_executions"].append(metric)
        
        # Log the metric
        if success:
            logger.info(
                f"Tool execution completed - Tool: {tool_name}, "
                f"Duration: {duration:.2f}s"
            )
        else:
            logger.error(
                f"Tool execution failed - Tool: {tool_name}, "
                f"Duration: {duration:.2f}s, Error: {error}"
            )
    
    def record_node_execution(
        self,
        node_name: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """
        Record a graph node execution metric.
        
        Args:
            node_name: Name of the node
            duration: Execution duration in seconds
            success: Whether the execution succeeded
            error: Error message if execution failed
        """
        metric = {
            "timestamp": datetime.now(),
            "node": node_name,
            "duration": duration,
            "success": success,
            "error": error,
        }
        
        self.metrics["node_executions"].append(metric)
        
        # Log the metric
        if success:
            logger.debug(
                f"Node execution completed - Node: {node_name}, "
                f"Duration: {duration:.2f}s"
            )
        else:
            logger.error(
                f"Node execution failed - Node: {node_name}, "
                f"Duration: {duration:.2f}s, Error: {error}"
            )
    
    def record_conversation(
        self,
        conversation_id: str,
        user_id: str,
        duration: float,
        message_count: int,
        success: bool = True,
    ):
        """
        Record a conversation session metric.
        
        Args:
            conversation_id: Conversation identifier
            user_id: User identifier
            duration: Total conversation duration in seconds
            message_count: Number of messages exchanged
            success: Whether the conversation completed successfully
        """
        metric = {
            "timestamp": datetime.now(),
            "conversation_id": conversation_id,
            "user_id": user_id,
            "duration": duration,
            "message_count": message_count,
            "success": success,
        }
        
        self.metrics["conversations"].append(metric)
        
        # Log the metric
        logger.info(
            f"Conversation completed - ID: {conversation_id}, "
            f"User: {user_id}, Duration: {duration:.2f}s, "
            f"Messages: {message_count}, Success: {success}"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all collected metrics.
        
        Returns:
            Dictionary containing metric summaries
        """
        summary = {}
        
        # LLM call statistics
        llm_calls = self.metrics["llm_calls"]
        if llm_calls:
            successful_calls = [c for c in llm_calls if c["success"]]
            summary["llm_calls"] = {
                "total": len(llm_calls),
                "successful": len(successful_calls),
                "failed": len(llm_calls) - len(successful_calls),
                "avg_duration": sum(c["duration"] for c in successful_calls) / len(successful_calls) if successful_calls else 0,
                "total_tokens": sum(c["tokens"] for c in successful_calls if c["tokens"]) if successful_calls else 0,
            }
        
        # Tool execution statistics
        tool_executions = self.metrics["tool_executions"]
        if tool_executions:
            successful_tools = [t for t in tool_executions if t["success"]]
            summary["tool_executions"] = {
                "total": len(tool_executions),
                "successful": len(successful_tools),
                "failed": len(tool_executions) - len(successful_tools),
                "avg_duration": sum(t["duration"] for t in successful_tools) / len(successful_tools) if successful_tools else 0,
            }
        
        # Node execution statistics
        node_executions = self.metrics["node_executions"]
        if node_executions:
            successful_nodes = [n for n in node_executions if n["success"]]
            summary["node_executions"] = {
                "total": len(node_executions),
                "successful": len(successful_nodes),
                "failed": len(node_executions) - len(successful_nodes),
                "avg_duration": sum(n["duration"] for n in successful_nodes) / len(successful_nodes) if successful_nodes else 0,
            }
        
        # Conversation statistics
        conversations = self.metrics["conversations"]
        if conversations:
            successful_convs = [c for c in conversations if c["success"]]
            summary["conversations"] = {
                "total": len(conversations),
                "successful": len(successful_convs),
                "avg_duration": sum(c["duration"] for c in successful_convs) / len(successful_convs) if successful_convs else 0,
                "avg_messages": sum(c["message_count"] for c in successful_convs) / len(successful_convs) if successful_convs else 0,
            }
        
        return summary
    
    def log_summary(self):
        """Log a summary of all collected metrics"""
        summary = self.get_summary()
        
        logger.info("="*60)
        logger.info("Performance Metrics Summary")
        logger.info("="*60)
        
        for category, stats in summary.items():
            logger.info(f"\n{category.upper()}:")
            for key, value in stats.items():
                if isinstance(value, float):
                    logger.info(f"  {key}: {value:.2f}")
                else:
                    logger.info(f"  {key}: {value}")
        
        logger.info("="*60)


# Global performance monitor instance
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return _monitor


@contextmanager
def monitor_llm_call(agent_name: str):
    """
    Context manager for monitoring LLM API calls.
    
    Args:
        agent_name: Name of the agent making the call
    
    Yields:
        Dictionary to store call metadata (tokens, etc.)
    
    Example:
        >>> with monitor_llm_call("coordinator") as call_info:
        ...     response = llm_client.call(prompt)
        ...     call_info["tokens"] = response.usage.total_tokens
    """
    start_time = time.time()
    call_info = {"tokens": None, "error": None}
    
    try:
        yield call_info
        duration = time.time() - start_time
        _monitor.record_llm_call(
            agent_name=agent_name,
            duration=duration,
            tokens=call_info.get("tokens"),
            success=True,
        )
    except Exception as e:
        duration = time.time() - start_time
        _monitor.record_llm_call(
            agent_name=agent_name,
            duration=duration,
            success=False,
            error=str(e),
        )
        raise


@contextmanager
def monitor_tool_execution(tool_name: str):
    """
    Context manager for monitoring tool executions.
    
    Args:
        tool_name: Name of the tool
    
    Example:
        >>> with monitor_tool_execution("search_geektime_courses"):
        ...     results = search_tool.execute(query)
    """
    start_time = time.time()
    
    try:
        yield
        duration = time.time() - start_time
        _monitor.record_tool_execution(
            tool_name=tool_name,
            duration=duration,
            success=True,
        )
    except Exception as e:
        duration = time.time() - start_time
        _monitor.record_tool_execution(
            tool_name=tool_name,
            duration=duration,
            success=False,
            error=str(e),
        )
        raise


@contextmanager
def monitor_node_execution(node_name: str):
    """
    Context manager for monitoring graph node executions.
    
    Args:
        node_name: Name of the node
    
    Example:
        >>> with monitor_node_execution("coordinator"):
        ...     result = coordinator_node(state)
    """
    start_time = time.time()
    
    try:
        yield
        duration = time.time() - start_time
        _monitor.record_node_execution(
            node_name=node_name,
            duration=duration,
            success=True,
        )
    except Exception as e:
        duration = time.time() - start_time
        _monitor.record_node_execution(
            node_name=node_name,
            duration=duration,
            success=False,
            error=str(e),
        )
        raise


def monitor_function(metric_type: str = "node"):
    """
    Decorator for monitoring function execution time.
    
    Args:
        metric_type: Type of metric to record ("node", "tool", or "llm")
    
    Example:
        >>> @monitor_function(metric_type="node")
        ... def coordinator_node(state):
        ...     # node implementation
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if metric_type == "node":
                    _monitor.record_node_execution(func.__name__, duration, success=True)
                elif metric_type == "tool":
                    _monitor.record_tool_execution(func.__name__, duration, success=True)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                if metric_type == "node":
                    _monitor.record_node_execution(func.__name__, duration, success=False, error=str(e))
                elif metric_type == "tool":
                    _monitor.record_tool_execution(func.__name__, duration, success=False, error=str(e))
                
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if metric_type == "node":
                    _monitor.record_node_execution(func.__name__, duration, success=True)
                elif metric_type == "tool":
                    _monitor.record_tool_execution(func.__name__, duration, success=True)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                if metric_type == "node":
                    _monitor.record_node_execution(func.__name__, duration, success=False, error=str(e))
                elif metric_type == "tool":
                    _monitor.record_tool_execution(func.__name__, duration, success=False, error=str(e))
                
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
