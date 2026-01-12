"""Example of creating and using the LangGraph graph.

This example demonstrates:
1. Creating the graph with and without checkpointer
2. Initializing agents
3. Running a conversation through the graph
4. Using checkpointer for conversation persistence
"""

import asyncio
from datetime import datetime

from src.graph import (
    create_graph,
    create_graph_with_config,
    create_initial_state,
    initialize_agents,
    add_message,
)
from src.llm.vllm_client import VLLMClient
from src.utils.config import get_config
from src.utils.logger import setup_logger


async def example_without_checkpointer():
    """Example: Create and use graph without persistence."""
    print("\n=== Example 1: Graph without Checkpointer ===\n")
    
    # Load configuration
    config = get_config()
    
    # Setup logger
    logger = setup_logger("graph_example", level="INFO")
    
    # Initialize vLLM client
    vllm_client = VLLMClient(
        api_base=config.vllm.api_base,
        api_key=config.vllm.api_key,
        model_name=config.vllm.model_name,
        temperature=config.vllm.temperature,
        max_tokens=config.vllm.max_tokens,
        timeout=config.vllm.timeout,
    )
    
    # Initialize agents (must be done before using the graph)
    initialize_agents(config, vllm_client)
    logger.info("Agents initialized")
    
    # Create graph without checkpointer
    graph = create_graph(checkpointer=None, max_loop_count=10)
    logger.info("Graph created without checkpointer")
    
    # Create initial state
    state = create_initial_state(
        conversation_id="example-conversation-1",
        user_id="user-123",
    )
    
    # Add user message
    state = add_message(
        state,
        role="user",
        content="我想学习 Python 数据分析，请推荐一些课程。",
        agent=None,
    )
    
    logger.info("Starting conversation...")
    
    # Run the graph
    # Note: Without checkpointer, the conversation is not persisted
    result = graph.invoke(state)
    
    # Print results
    print("\nConversation completed!")
    print(f"Total messages: {len(result['messages'])}")
    print(f"Loop count: {result['loop_count']}")
    print(f"Is complete: {result['is_complete']}")
    print(f"Courses found: {len(result['course_candidates'])}")
    
    # Print last few messages
    print("\nLast 3 messages:")
    for msg in result["messages"][-3:]:
        print(f"  [{msg['role']}] ({msg.get('agent', 'N/A')}): {msg['content'][:100]}...")


async def example_with_checkpointer():
    """Example: Create and use graph with persistence."""
    print("\n=== Example 2: Graph with Checkpointer ===\n")
    
    # Load configuration
    config = get_config()
    
    # Setup logger
    logger = setup_logger("graph_example", level="INFO")
    
    # Initialize vLLM client
    vllm_client = VLLMClient(
        api_base=config.vllm.api_base,
        api_key=config.vllm.api_key,
        model_name=config.vllm.model_name,
        temperature=config.vllm.temperature,
        max_tokens=config.vllm.max_tokens,
        timeout=config.vllm.timeout,
    )
    
    # Initialize agents
    initialize_agents(config, vllm_client)
    logger.info("Agents initialized")
    
    # Create checkpointer for conversation persistence
    # Note: This requires langgraph.checkpoint.sqlite to be installed
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        
        # Create SQLite checkpointer
        checkpointer = SqliteSaver.from_conn_string("data/checkpoints.db")
        logger.info("Checkpointer created with SQLite backend")
        
        # Create graph with checkpointer
        graph = create_graph(checkpointer=checkpointer, max_loop_count=10)
        logger.info("Graph created with checkpointer")
        
        # Create initial state
        thread_id = "example-thread-1"
        state = create_initial_state(
            conversation_id=thread_id,
            user_id="user-456",
        )
        
        # Add user message
        state = add_message(
            state,
            role="user",
            content="我想学习机器学习，我是初学者。",
            agent=None,
        )
        
        logger.info("Starting conversation with persistence...")
        
        # Run the graph with thread_id for persistence
        # The thread_id allows us to resume the conversation later
        config_dict = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(state, config=config_dict)
        
        # Print results
        print("\nConversation completed and persisted!")
        print(f"Thread ID: {thread_id}")
        print(f"Total messages: {len(result['messages'])}")
        print(f"Loop count: {result['loop_count']}")
        print(f"Is complete: {result['is_complete']}")
        
        # Demonstrate resuming conversation
        print("\n--- Resuming conversation from checkpoint ---")
        
        # Add another user message to the result state
        result = add_message(
            result,
            role="user",
            content="请给我制定一个学习计划。",
            agent=None,
        )
        
        # Reset completion flag to continue
        result["is_complete"] = False
        result["next_agent"] = "coordinator"
        
        # Resume the conversation
        result2 = graph.invoke(result, config=config_dict)
        
        print(f"\nConversation resumed!")
        print(f"Total messages now: {len(result2['messages'])}")
        print(f"Learning plan created: {result2['learning_plan'] is not None}")
        
    except ImportError:
        logger.error("langgraph.checkpoint.sqlite not available")
        print("Error: langgraph.checkpoint.sqlite is required for this example")
        print("Install with: pip install langgraph[sqlite]")


async def example_with_config():
    """Example: Create graph using system configuration."""
    print("\n=== Example 3: Graph with System Config ===\n")
    
    # Load configuration
    config = get_config()
    
    # Setup logger
    logger = setup_logger("graph_example", level="INFO")
    
    # Initialize vLLM client
    vllm_client = VLLMClient(
        api_base=config.vllm.api_base,
        api_key=config.vllm.api_key,
        model_name=config.vllm.model_name,
        temperature=config.vllm.temperature,
        max_tokens=config.vllm.max_tokens,
        timeout=config.vllm.timeout,
    )
    
    # Initialize agents
    initialize_agents(config, vllm_client)
    logger.info("Agents initialized")
    
    # Create graph using config (convenience function)
    # This automatically extracts max_loop_count from config
    graph = create_graph_with_config(config, checkpointer=None)
    logger.info(f"Graph created with max_loop_count from config: {config.system.max_loop_count}")
    
    # Create initial state
    state = create_initial_state()
    
    # Add user message
    state = add_message(
        state,
        role="user",
        content="你好，我想了解一下你能帮我做什么？",
        agent=None,
    )
    
    logger.info("Starting conversation...")
    
    # Run the graph
    result = graph.invoke(state)
    
    # Print results
    print("\nConversation completed!")
    print(f"Coordinator response: {result['messages'][-1]['content'][:200]}...")


async def example_streaming():
    """Example: Stream graph execution step by step."""
    print("\n=== Example 4: Streaming Graph Execution ===\n")
    
    # Load configuration
    config = get_config()
    
    # Setup logger
    logger = setup_logger("graph_example", level="INFO")
    
    # Initialize vLLM client
    vllm_client = VLLMClient(
        api_base=config.vllm.api_base,
        api_key=config.vllm.api_key,
        model_name=config.vllm.model_name,
        temperature=config.vllm.temperature,
        max_tokens=config.vllm.max_tokens,
        timeout=config.vllm.timeout,
    )
    
    # Initialize agents
    initialize_agents(config, vllm_client)
    logger.info("Agents initialized")
    
    # Create graph
    graph = create_graph(checkpointer=None, max_loop_count=10)
    logger.info("Graph created")
    
    # Create initial state
    state = create_initial_state()
    
    # Add user message
    state = add_message(
        state,
        role="user",
        content="推荐一些 Python 课程。",
        agent=None,
    )
    
    logger.info("Starting streaming execution...")
    
    # Stream the graph execution
    # This allows us to see each node execution as it happens
    print("\nStreaming node executions:")
    for i, step in enumerate(graph.stream(state), 1):
        node_name = list(step.keys())[0]
        node_state = step[node_name]
        
        print(f"\nStep {i}: {node_name}")
        print(f"  Messages: {len(node_state['messages'])}")
        print(f"  Next agent: {node_state.get('next_agent')}")
        print(f"  Loop count: {node_state['loop_count']}")
        
        if node_state.get("is_complete"):
            print("  Status: COMPLETE")
            break


def main():
    """Run all examples."""
    print("=" * 60)
    print("LangGraph Graph Usage Examples")
    print("=" * 60)
    
    # Note: These examples require a running vLLM server
    # Make sure to configure config/system_config.yaml with correct vLLM endpoint
    
    try:
        # Run examples
        asyncio.run(example_without_checkpointer())
        asyncio.run(example_with_checkpointer())
        asyncio.run(example_with_config())
        asyncio.run(example_streaming())
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nMake sure:")
        print("1. vLLM server is running and accessible")
        print("2. config/system_config.yaml is properly configured")
        print("3. All dependencies are installed")


if __name__ == "__main__":
    main()
