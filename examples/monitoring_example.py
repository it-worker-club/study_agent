"""Example demonstrating the performance monitoring system

This example shows how to use the monitoring utilities to track
LLM calls, tool executions, and node executions.
"""

import asyncio
import time
from src.utils.monitoring import (
    get_monitor,
    monitor_llm_call,
    monitor_tool_execution,
    monitor_node_execution,
    monitor_function,
)
from src.utils.logger import setup_logger


# Example 1: Using context managers for monitoring
async def example_context_managers():
    """Demonstrate monitoring with context managers"""
    print("\n" + "="*60)
    print("Example 1: Context Manager Monitoring")
    print("="*60 + "\n")
    
    # Monitor an LLM call
    with monitor_llm_call("coordinator") as call_info:
        # Simulate LLM API call
        time.sleep(0.5)
        call_info["tokens"] = 150
        print("Simulated LLM call completed")
    
    # Monitor a tool execution
    with monitor_tool_execution("search_geektime_courses"):
        # Simulate tool execution
        time.sleep(0.3)
        print("Simulated tool execution completed")
    
    # Monitor a node execution
    with monitor_node_execution("course_advisor"):
        # Simulate node processing
        time.sleep(0.2)
        print("Simulated node execution completed")


# Example 2: Using decorators for monitoring
@monitor_function(metric_type="node")
def example_node_function():
    """Example node function with monitoring decorator"""
    time.sleep(0.1)
    return {"status": "success"}


@monitor_function(metric_type="tool")
async def example_tool_function():
    """Example async tool function with monitoring decorator"""
    await asyncio.sleep(0.15)
    return {"results": ["course1", "course2"]}


async def example_decorators():
    """Demonstrate monitoring with decorators"""
    print("\n" + "="*60)
    print("Example 2: Decorator Monitoring")
    print("="*60 + "\n")
    
    # Call decorated functions
    result1 = example_node_function()
    print(f"Node function result: {result1}")
    
    result2 = await example_tool_function()
    print(f"Tool function result: {result2}")


# Example 3: Recording conversation metrics
async def example_conversation_metrics():
    """Demonstrate recording conversation metrics"""
    print("\n" + "="*60)
    print("Example 3: Conversation Metrics")
    print("="*60 + "\n")
    
    monitor = get_monitor()
    
    # Simulate a conversation
    conversation_id = "conv_123"
    user_id = "user_456"
    
    # Record conversation
    monitor.record_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        duration=45.5,
        message_count=12,
        success=True,
    )
    
    print(f"Recorded conversation: {conversation_id}")


# Example 4: Error handling with monitoring
async def example_error_handling():
    """Demonstrate monitoring with error handling"""
    print("\n" + "="*60)
    print("Example 4: Error Handling")
    print("="*60 + "\n")
    
    # Successful execution
    try:
        with monitor_llm_call("test_agent") as call_info:
            time.sleep(0.1)
            call_info["tokens"] = 100
            print("Successful LLM call")
    except Exception as e:
        print(f"Error: {e}")
    
    # Failed execution
    try:
        with monitor_tool_execution("failing_tool"):
            time.sleep(0.1)
            raise ValueError("Simulated tool failure")
    except ValueError as e:
        print(f"Caught expected error: {e}")


# Example 5: Getting and displaying metrics summary
async def example_metrics_summary():
    """Demonstrate getting metrics summary"""
    print("\n" + "="*60)
    print("Example 5: Metrics Summary")
    print("="*60 + "\n")
    
    monitor = get_monitor()
    
    # Get summary
    summary = monitor.get_summary()
    
    print("Performance Metrics Summary:")
    print("-" * 60)
    
    for category, stats in summary.items():
        print(f"\n{category.upper()}:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
    
    print("\n" + "-" * 60)
    
    # Also log the summary
    print("\nLogging summary to logger...")
    monitor.log_summary()


async def main():
    """Run all examples"""
    # Setup logger
    logger = setup_logger(
        name="monitoring_example",
        level="INFO",
    )
    
    print("\n" + "="*60)
    print("Performance Monitoring Examples")
    print("="*60)
    
    # Run examples
    await example_context_managers()
    await example_decorators()
    await example_conversation_metrics()
    await example_error_handling()
    await example_metrics_summary()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
