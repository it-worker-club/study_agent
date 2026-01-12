"""
Example demonstrating error handling in the education tutoring system.

This script shows how the error handling mechanism works across different
components and error scenarios.
"""

import asyncio
from datetime import datetime

from src.graph.helpers import create_initial_state
from src.graph.state import AgentState
from src.utils.error_handler import ErrorHandler, handle_vllm_service_failure
from src.llm.vllm_client import (
    VLLMConnectionError,
    VLLMTimeoutError,
    VLLMAPIError,
)
from src.tools.mcp_playwright import MCPPlaywrightError
from src.tools.web_search import WebSearchError


def print_state_messages(state: AgentState, title: str):
    """Print messages from state for demonstration"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Conversation ID: {state['conversation_id']}")
    print(f"Requires Human Input: {state['requires_human_input']}")
    print(f"\nMessages:")
    for i, msg in enumerate(state['messages'], 1):
        agent_info = f" [{msg.get('agent')}]" if msg.get('agent') else ""
        print(f"{i}. {msg['role']}{agent_info}: {msg['content']}")
    print(f"{'='*60}\n")


def demo_llm_errors():
    """Demonstrate LLM error handling"""
    print("\n" + "="*60)
    print("DEMO 1: LLM Error Handling")
    print("="*60)
    
    # Create initial state
    state = create_initial_state("demo-llm-errors")
    
    # 1. Connection Error
    print("\n1. Handling Connection Error:")
    connection_error = VLLMConnectionError("Failed to connect to vLLM server")
    state = ErrorHandler.handle_llm_error(connection_error, state)
    print_state_messages(state, "After Connection Error")
    
    # 2. Timeout Error
    print("\n2. Handling Timeout Error:")
    state = create_initial_state("demo-timeout")
    timeout_error = VLLMTimeoutError("Request timed out after 60 seconds")
    state = ErrorHandler.handle_llm_error(timeout_error, state)
    print_state_messages(state, "After Timeout Error")
    
    # 3. API Error
    print("\n3. Handling API Error:")
    state = create_initial_state("demo-api-error")
    api_error = VLLMAPIError("API returned 500 Internal Server Error")
    state = ErrorHandler.handle_llm_error(api_error, state)
    print_state_messages(state, "After API Error")


def demo_tool_errors():
    """Demonstrate tool error handling"""
    print("\n" + "="*60)
    print("DEMO 2: Tool Error Handling")
    print("="*60)
    
    # Create initial state
    state = create_initial_state("demo-tool-errors")
    
    # 1. MCP Playwright Error
    print("\n1. Handling MCP Playwright Error:")
    mcp_error = MCPPlaywrightError("Failed to navigate to GeekTime")
    state = ErrorHandler.handle_tool_error(mcp_error, "MCP Playwright", state)
    print_state_messages(state, "After MCP Playwright Error")
    
    # 2. Web Search Error
    print("\n2. Handling Web Search Error:")
    state = create_initial_state("demo-web-search-error")
    web_error = WebSearchError("Search API rate limit exceeded")
    state = ErrorHandler.handle_tool_error(web_error, "Web Search", state)
    print_state_messages(state, "After Web Search Error")


def demo_state_errors():
    """Demonstrate state management error handling"""
    print("\n" + "="*60)
    print("DEMO 3: State Management Error Handling")
    print("="*60)
    
    # Create a corrupted state
    state = create_initial_state("demo-state-error")
    state["messages"].append({
        "role": "user",
        "content": "我想学习 Python",
        "timestamp": datetime.now(),
        "agent": None,
    })
    
    print("\n1. Handling State Corruption:")
    state_error = Exception("State validation failed: missing required field")
    state = ErrorHandler.handle_state_error(state_error, state)
    print_state_messages(state, "After State Error (Reset to Safe State)")


def demo_routing_errors():
    """Demonstrate routing error handling"""
    print("\n" + "="*60)
    print("DEMO 4: Routing Error Handling")
    print("="*60)
    
    # Create initial state
    state = create_initial_state("demo-routing-error")
    state["messages"].append({
        "role": "user",
        "content": "这是一个模糊的请求",
        "timestamp": datetime.now(),
        "agent": None,
    })
    
    print("\n1. Handling Routing Decision Error:")
    routing_error = Exception("Unable to determine user intent")
    state = ErrorHandler.handle_routing_error(routing_error, state)
    print_state_messages(state, "After Routing Error (Request Clarification)")


def demo_error_recovery_logic():
    """Demonstrate error recovery decision logic"""
    print("\n" + "="*60)
    print("DEMO 5: Error Recovery Logic")
    print("="*60)
    
    # Test recoverable errors
    print("\n1. Testing Error Recoverability:")
    errors = [
        (VLLMConnectionError("test"), "VLLMConnectionError"),
        (VLLMTimeoutError("test"), "VLLMTimeoutError"),
        (ConnectionError("test"), "ConnectionError"),
        (TimeoutError("test"), "TimeoutError"),
        (VLLMAPIError("test"), "VLLMAPIError"),
        (ValueError("test"), "ValueError"),
    ]
    
    for error, name in errors:
        is_recoverable = ErrorHandler.is_recoverable_error(error)
        status = "✓ Recoverable" if is_recoverable else "✗ Not Recoverable"
        print(f"  {name}: {status}")
    
    # Test retry logic
    print("\n2. Testing Retry Decision Logic:")
    recoverable_error = VLLMConnectionError("test")
    non_recoverable_error = ValueError("test")
    
    print(f"\n  Recoverable Error (VLLMConnectionError):")
    for attempt in range(1, 5):
        should_retry = ErrorHandler.should_retry(recoverable_error, attempt, max_attempts=3)
        status = "→ Retry" if should_retry else "→ Give Up"
        print(f"    Attempt {attempt}: {status}")
    
    print(f"\n  Non-Recoverable Error (ValueError):")
    for attempt in range(1, 3):
        should_retry = ErrorHandler.should_retry(non_recoverable_error, attempt, max_attempts=3)
        status = "→ Retry" if should_retry else "→ Give Up"
        print(f"    Attempt {attempt}: {status}")


def demo_vllm_service_failure():
    """Demonstrate complete vLLM service failure handling"""
    print("\n" + "="*60)
    print("DEMO 6: Complete vLLM Service Failure")
    print("="*60)
    
    # Create initial state
    state = create_initial_state("demo-vllm-failure")
    state["messages"].append({
        "role": "user",
        "content": "我想学习机器学习",
        "timestamp": datetime.now(),
        "agent": None,
    })
    
    print("\n1. Handling Complete Service Unavailability:")
    state = handle_vllm_service_failure(state)
    print_state_messages(state, "After vLLM Service Failure")


def demo_error_context_preservation():
    """Demonstrate that error handling preserves important context"""
    print("\n" + "="*60)
    print("DEMO 7: Context Preservation During Error Handling")
    print("="*60)
    
    # Create state with context
    original_id = "demo-context-preservation"
    state = create_initial_state(original_id)
    state["user_profile"]["background"] = "软件工程师"
    state["user_profile"]["skill_level"] = "intermediate"
    state["user_profile"]["learning_goals"] = ["学习 Python", "掌握数据分析"]
    state["messages"].append({
        "role": "user",
        "content": "我想学习 Python 数据分析",
        "timestamp": datetime.now(),
        "agent": None,
    })
    
    print(f"\nOriginal State:")
    print(f"  Conversation ID: {state['conversation_id']}")
    print(f"  User Background: {state['user_profile']['background']}")
    print(f"  Skill Level: {state['user_profile']['skill_level']}")
    print(f"  Learning Goals: {state['user_profile']['learning_goals']}")
    print(f"  Message Count: {len(state['messages'])}")
    
    # Handle various errors and check context preservation
    print(f"\n1. After LLM Error:")
    error = VLLMConnectionError("test")
    result_state = ErrorHandler.handle_llm_error(error, state.copy())
    print(f"  Conversation ID Preserved: {result_state['conversation_id'] == original_id}")
    print(f"  User Profile Preserved: {result_state['user_profile'] == state['user_profile']}")
    print(f"  Messages Preserved: {len(result_state['messages']) > len(state['messages'])}")
    
    print(f"\n2. After Tool Error:")
    error = MCPPlaywrightError("test")
    result_state = ErrorHandler.handle_tool_error(error, "test_tool", state.copy())
    print(f"  Conversation ID Preserved: {result_state['conversation_id'] == original_id}")
    print(f"  User Profile Preserved: {result_state['user_profile'] == state['user_profile']}")
    
    print(f"\n3. After State Error (Reset):")
    error = Exception("state corrupted")
    result_state = ErrorHandler.handle_state_error(error, state.copy())
    print(f"  Conversation ID Preserved: {result_state['conversation_id'] == original_id}")
    print(f"  State Reset to Safe: {len(result_state['messages']) >= 1}")
    print(f"  Has Error Message: {'重置对话' in result_state['messages'][-1]['content']}")


def main():
    """Run all error handling demonstrations"""
    print("\n" + "="*60)
    print("ERROR HANDLING DEMONSTRATION")
    print("Education Tutoring System")
    print("="*60)
    
    # Run all demos
    demo_llm_errors()
    demo_tool_errors()
    demo_state_errors()
    demo_routing_errors()
    demo_error_recovery_logic()
    demo_vllm_service_failure()
    demo_error_context_preservation()
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)
    print("\nKey Takeaways:")
    print("1. ✓ All errors are handled gracefully with user-friendly messages")
    print("2. ✓ Error handling preserves conversation context and state")
    print("3. ✓ Recoverable errors can be retried automatically")
    print("4. ✓ Tool failures trigger fallback mechanisms")
    print("5. ✓ State corruption triggers safe state reset")
    print("6. ✓ Routing errors request user clarification")
    print("7. ✓ Complete service failures are properly communicated")
    print("\n")


if __name__ == "__main__":
    main()
