"""Unit tests for error handler"""

import pytest
from datetime import datetime

from src.utils.error_handler import ErrorHandler, handle_vllm_service_failure
from src.llm.vllm_client import (
    VLLMConnectionError,
    VLLMAPIError,
    VLLMTimeoutError,
)
from src.graph.state import AgentState
from src.graph.helpers import create_initial_state


@pytest.fixture
def test_state():
    """Create a test state"""
    return create_initial_state("test-conversation-123")


def test_handle_llm_connection_error(test_state):
    """Test handling of LLM connection errors"""
    error = VLLMConnectionError("Connection failed")
    
    result_state = ErrorHandler.handle_llm_error(error, test_state)
    
    # Check that error message was added
    assert len(result_state["messages"]) > 0
    last_message = result_state["messages"][-1]
    assert "无法连接" in last_message["content"]
    assert last_message["agent"] == "system"
    
    # Check that human input is required
    assert result_state["requires_human_input"] is True


def test_handle_llm_timeout_error(test_state):
    """Test handling of LLM timeout errors"""
    error = VLLMTimeoutError("Request timed out")
    
    result_state = ErrorHandler.handle_llm_error(error, test_state)
    
    # Check that error message was added
    last_message = result_state["messages"][-1]
    assert "超时" in last_message["content"]
    assert result_state["requires_human_input"] is True


def test_handle_llm_api_error(test_state):
    """Test handling of LLM API errors"""
    error = VLLMAPIError("API error occurred")
    
    result_state = ErrorHandler.handle_llm_error(error, test_state)
    
    # Check that error message was added
    last_message = result_state["messages"][-1]
    assert "遇到了问题" in last_message["content"]
    assert result_state["requires_human_input"] is True


def test_handle_tool_error(test_state):
    """Test handling of tool execution errors"""
    error = Exception("Tool failed")
    tool_name = "MCP Playwright"
    
    result_state = ErrorHandler.handle_tool_error(error, tool_name, test_state)
    
    # Check that fallback message was added
    last_message = result_state["messages"][-1]
    assert tool_name in last_message["content"]
    assert "备用方案" in last_message["content"]


def test_handle_state_error(test_state):
    """Test handling of state management errors"""
    error = Exception("State corrupted")
    
    result_state = ErrorHandler.handle_state_error(error, test_state)
    
    # Check that safe state was created
    assert result_state is not None
    assert "messages" in result_state
    
    # Check that error message was added
    last_message = result_state["messages"][-1]
    assert "重置对话" in last_message["content"]


def test_handle_routing_error(test_state):
    """Test handling of routing errors"""
    error = Exception("Routing failed")
    
    result_state = ErrorHandler.handle_routing_error(error, test_state)
    
    # Check that clarification message was added
    last_message = result_state["messages"][-1]
    assert "不太确定" in last_message["content"]
    assert "1." in last_message["content"]  # Options listed
    assert result_state["requires_human_input"] is True


def test_handle_generic_error(test_state):
    """Test handling of generic errors"""
    error = Exception("Unexpected error")
    context = "test_component"
    
    result_state = ErrorHandler.handle_generic_error(error, test_state, context)
    
    # Check that generic error message was added
    last_message = result_state["messages"][-1]
    assert "意外错误" in last_message["content"]
    assert result_state["requires_human_input"] is True


def test_is_recoverable_error():
    """Test error recoverability detection"""
    # Recoverable errors
    assert ErrorHandler.is_recoverable_error(VLLMConnectionError("test"))
    assert ErrorHandler.is_recoverable_error(VLLMTimeoutError("test"))
    assert ErrorHandler.is_recoverable_error(ConnectionError("test"))
    assert ErrorHandler.is_recoverable_error(TimeoutError("test"))
    
    # Non-recoverable errors
    assert not ErrorHandler.is_recoverable_error(VLLMAPIError("test"))
    assert not ErrorHandler.is_recoverable_error(ValueError("test"))
    assert not ErrorHandler.is_recoverable_error(Exception("test"))


def test_should_retry():
    """Test retry decision logic"""
    recoverable_error = VLLMConnectionError("test")
    non_recoverable_error = ValueError("test")
    
    # Should retry recoverable errors within limit
    assert ErrorHandler.should_retry(recoverable_error, 1, 3)
    assert ErrorHandler.should_retry(recoverable_error, 2, 3)
    
    # Should not retry at max attempts
    assert not ErrorHandler.should_retry(recoverable_error, 3, 3)
    assert not ErrorHandler.should_retry(recoverable_error, 4, 3)
    
    # Should not retry non-recoverable errors
    assert not ErrorHandler.should_retry(non_recoverable_error, 1, 3)


def test_handle_vllm_service_failure(test_state):
    """Test handling of complete vLLM service failure"""
    result_state = handle_vllm_service_failure(test_state)
    
    # Check that service unavailable message was added
    last_message = result_state["messages"][-1]
    assert "不可用" in last_message["content"]
    assert "服务器维护" in last_message["content"]
    assert result_state["requires_human_input"] is True


def test_error_handler_preserves_conversation_id(test_state):
    """Test that error handlers preserve conversation ID"""
    original_id = test_state["conversation_id"]
    error = Exception("test error")
    
    # Test various error handlers
    result1 = ErrorHandler.handle_llm_error(error, test_state.copy())
    assert result1["conversation_id"] == original_id
    
    result2 = ErrorHandler.handle_tool_error(error, "test_tool", test_state.copy())
    assert result2["conversation_id"] == original_id
    
    result3 = ErrorHandler.handle_routing_error(error, test_state.copy())
    assert result3["conversation_id"] == original_id
