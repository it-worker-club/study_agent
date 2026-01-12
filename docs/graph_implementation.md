# LangGraph Graph Implementation

## Overview

This document describes the implementation of the LangGraph StateGraph for the education tutoring system. The graph orchestrates multi-agent conversations using a Supervisor pattern where a coordinator agent routes tasks to specialized agents.

## Architecture

### Graph Structure

```
┌─────────┐
│  Entry  │
└────┬────┘
     │
     ▼
┌────────────┐
│Coordinator │◄─────────┐
└─────┬──────┘          │
      │                 │
      ├─────────────────┤
      │                 │
      ▼                 │
┌──────────────┐        │
│Conditional   │        │
│   Router     │        │
└──┬───┬───┬───┘        │
   │   │   │            │
   ▼   ▼   ▼            │
┌──────┐ ┌──────┐ ┌────┴────┐
│Course│ │Learn.│ │  Human  │
│Advis.│ │Plann.│ │  Input  │
└───┬──┘ └───┬──┘ └────┬────┘
    │        │         │
    └────────┴─────────┘
             │
             ▼
        ┌────────┐
        │  End   │
        └────────┘
```

### Node Descriptions

1. **Entry Node** (`entry_node`)
   - First node executed in the graph
   - Initializes conversation state
   - Routes to coordinator

2. **Coordinator Node** (`coordinator_node`)
   - Analyzes user intent using LLM
   - Makes routing decisions
   - Updates state with next_agent and current_task
   - Handles loop count management

3. **Course Advisor Node** (`course_advisor_node`)
   - Searches GeekTime courses via MCP Playwright
   - Searches web resources
   - Analyzes and recommends courses
   - Updates state with course_candidates

4. **Learning Planner Node** (`learning_planner_node`)
   - Creates structured learning plans
   - Breaks down goals into milestones
   - Incorporates recommended courses
   - Updates state with learning_plan

5. **Human Input Node** (`human_input_node`)
   - Handles user feedback and approvals
   - Processes learning plan approvals
   - Processes course recommendation feedback
   - Supports user interruption at any point

6. **End Node** (`end_node`)
   - Finalizes conversation
   - Marks state as complete
   - Adds farewell message

### Routing Logic

The graph uses conditional routing implemented in the `route_next()` function:

```python
def route_next(state: AgentState, max_loop_count: int = 10) -> str:
    # 1. Check loop count (prevent infinite loops)
    if state["loop_count"] > max_loop_count:
        return "end"
    
    # 2. Check if complete
    if state["is_complete"]:
        return "end"
    
    # 3. Check if human input required
    if state["requires_human_input"]:
        return "human_input"
    
    # 4. Route based on next_agent
    next_agent = state.get("next_agent")
    if next_agent in valid_agents:
        return next_agent
    
    # 5. Default to end
    return "end"
```

## Usage

### Basic Usage (No Persistence)

```python
from src.graph import create_graph, initialize_agents, create_initial_state, add_message
from src.llm.vllm_client import VLLMClient
from src.utils.config import get_config

# Load config and initialize
config = get_config()
vllm_client = VLLMClient(...)
initialize_agents(config, vllm_client)

# Create graph
graph = create_graph(checkpointer=None)

# Create initial state
state = create_initial_state()
state = add_message(state, role="user", content="我想学习 Python", agent=None)

# Run graph
result = graph.invoke(state)
```

### With Persistence (Checkpointer)

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Create checkpointer
checkpointer = SqliteSaver.from_conn_string("data/checkpoints.db")

# Create graph with checkpointer
graph = create_graph(checkpointer=checkpointer)

# Run with thread_id for persistence
thread_id = "conversation-123"
config = {"configurable": {"thread_id": thread_id}}
result = graph.invoke(state, config=config)

# Resume conversation later
result = add_message(result, role="user", content="继续", agent=None)
result = graph.invoke(result, config=config)
```

### Streaming Execution

```python
# Stream node executions
for step in graph.stream(state):
    node_name = list(step.keys())[0]
    node_state = step[node_name]
    print(f"Executed: {node_name}")
    print(f"Next: {node_state.get('next_agent')}")
```

## Configuration

### Graph Parameters

- **checkpointer**: Optional `BaseCheckpointSaver` for conversation persistence
  - If provided, enables conversation history and state recovery
  - Recommended: `SqliteSaver` for local development
  - Can use other backends (PostgreSQL, Redis, etc.)

- **max_loop_count**: Maximum routing loops before termination
  - Default: 10
  - Prevents infinite loops
  - Can be configured via `config.system.max_loop_count`

### System Configuration

```yaml
# config/system_config.yaml
system:
  database_path: "./data/tutoring_system.db"
  max_loop_count: 10
  enable_human_input: true
```

## State Management

### AgentState Schema

The graph uses `AgentState` TypedDict for type-safe state management:

```python
class AgentState(TypedDict):
    # Conversation
    messages: List[Message]
    conversation_id: str
    
    # User
    user_profile: UserProfile
    
    # Task
    current_task: Optional[str]
    next_agent: Optional[str]
    
    # Data
    course_candidates: List[CourseInfo]
    learning_plan: Optional[LearningPlan]
    
    # Control
    requires_human_input: bool
    human_feedback: Optional[str]
    loop_count: int
    is_complete: bool
```

### State Updates

All nodes receive and return `AgentState`. State updates are automatically managed by LangGraph:

```python
def my_node(state: AgentState) -> AgentState:
    # Read from state
    messages = state["messages"]
    
    # Update state
    state["next_agent"] = "course_advisor"
    state = add_message(state, role="assistant", content="...", agent="my_node")
    
    return state
```

## Error Handling

### Node-Level Error Handling

Each node implements error handling:

```python
def coordinator_node(state: AgentState) -> AgentState:
    try:
        # Node logic
        ...
    except VLLMClientError as e:
        return ErrorHandler.handle_llm_error(e, state)
    except Exception as e:
        return ErrorHandler.handle_routing_error(e, state)
```

### Loop Prevention

The graph automatically prevents infinite loops:

1. Each coordinator execution increments `loop_count`
2. `route_next()` checks if `loop_count > max_loop_count`
3. If exceeded, routes to "end" node
4. User is notified of loop limit

### Recovery Mechanisms

- **LLM Errors**: Notify user, request human input
- **Tool Errors**: Provide fallback response, continue execution
- **State Errors**: Reset to safe state, restart conversation
- **Routing Errors**: Request user clarification

## Testing

### Unit Tests

Test individual nodes:

```python
def test_coordinator_node():
    state = create_initial_state()
    state = add_message(state, role="user", content="推荐课程", agent=None)
    
    result = coordinator_node(state)
    
    assert result["next_agent"] in ["course_advisor", "learning_planner"]
    assert result["current_task"] is not None
```

### Integration Tests

Test complete graph execution:

```python
def test_graph_execution():
    graph = create_graph()
    state = create_initial_state()
    state = add_message(state, role="user", content="我想学习 Python", agent=None)
    
    result = graph.invoke(state)
    
    assert result["is_complete"]
    assert len(result["messages"]) > 1
```

### Property-Based Tests

Test graph properties:

```python
@given(user_input=st.text(min_size=1, max_size=200))
def test_graph_always_completes(user_input):
    """Property: Graph should always reach completion or loop limit"""
    graph = create_graph(max_loop_count=5)
    state = create_initial_state()
    state = add_message(state, role="user", content=user_input, agent=None)
    
    result = graph.invoke(state)
    
    # Should either complete or hit loop limit
    assert result["is_complete"] or result["loop_count"] > 5
```

## Performance Considerations

### Async Operations

Nodes use async operations for LLM and tool calls:

```python
# In node function (sync context)
import asyncio

loop = asyncio.get_event_loop()
result = loop.run_until_complete(agent.async_method(state))
```

### Checkpointing Overhead

- Checkpointing adds I/O overhead for state persistence
- Use for production where conversation history is needed
- Skip for testing or stateless scenarios

### Memory Management

- State is passed by reference between nodes
- Large data (course lists, plans) stored in state
- Consider pagination for very large result sets

## Deployment

### Production Setup

1. **Use Persistent Checkpointer**
   ```python
   from langgraph.checkpoint.postgres import PostgresSaver
   checkpointer = PostgresSaver.from_conn_string(db_url)
   ```

2. **Configure Loop Limits**
   ```yaml
   system:
     max_loop_count: 15  # Higher for production
   ```

3. **Enable Monitoring**
   ```python
   # Add logging in nodes
   logger.info(f"Node executed: {node_name}, duration: {duration}ms")
   ```

4. **Handle Concurrent Conversations**
   ```python
   # Use unique thread_id per conversation
   thread_id = f"user-{user_id}-{timestamp}"
   config = {"configurable": {"thread_id": thread_id}}
   ```

### Scaling Considerations

- **Horizontal Scaling**: Each conversation is independent
- **Database**: Use connection pooling for checkpointer
- **LLM Service**: Ensure vLLM can handle concurrent requests
- **Caching**: Consider caching course search results

## Troubleshooting

### Common Issues

1. **Graph doesn't complete**
   - Check loop_count in state
   - Verify next_agent is set correctly
   - Check for errors in node execution

2. **Checkpointer errors**
   - Verify database connection
   - Check table schema is created
   - Ensure thread_id is provided in config

3. **Routing loops**
   - Review coordinator routing logic
   - Check if next_agent is being set
   - Verify route_next() conditions

4. **Agent not initialized**
   - Call initialize_agents() before creating graph
   - Verify vLLM client is created
   - Check tool clients are initialized

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [StateGraph API](https://langchain-ai.github.io/langgraph/reference/graphs/)
- [Checkpointing Guide](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- Design Document: `.kiro/specs/education-tutoring-system/design.md`
- Requirements: `.kiro/specs/education-tutoring-system/requirements.md`

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
