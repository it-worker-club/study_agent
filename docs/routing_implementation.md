# Routing Logic Implementation

## Overview

The routing logic is a critical component of the education tutoring system that determines which agent or node should execute next based on the current conversation state. It implements conditional branching and loop prevention to ensure smooth conversation flow.

## Implementation

### Location

The routing function is implemented in `src/graph/helpers.py` as `route_next()`.

### Function Signature

```python
def route_next(state: AgentState, max_loop_count: int = 10) -> str:
    """路由决策函数
    
    根据当前状态决定下一个要执行的节点。
    
    Args:
        state: 当前状态
        max_loop_count: 最大循环次数，默认为 10
        
    Returns:
        下一个节点的名称（字符串）
    """
```

### Routing Logic

The function implements a priority-based decision tree:

1. **Loop Prevention (Highest Priority)**
   - If `loop_count > max_loop_count`, route to `"end"`
   - Prevents infinite loops (Requirements 9.5)
   - Default max is 10 iterations

2. **Task Completion Check**
   - If `is_complete == True`, route to `"end"`
   - Ensures conversation terminates when task is done

3. **Human Input Check**
   - If `requires_human_input == True`, route to `"human_input"`
   - Enables human-in-the-loop for critical decisions (Requirements 6.1, 6.2)

4. **Agent Routing**
   - Route based on `next_agent` field
   - Valid agents: `coordinator`, `course_advisor`, `learning_planner`, `human_input`, `end`
   - If `next_agent` is invalid or `None`, default to `"end"` (safe fallback)

### Priority Order

```
loop_count > max_loop_count
    ↓
is_complete == True
    ↓
requires_human_input == True
    ↓
next_agent (if valid)
    ↓
"end" (default fallback)
```

## Usage in LangGraph

The `route_next` function is designed to be used as a conditional edge function in LangGraph:

```python
from langgraph.graph import StateGraph
from src.graph import AgentState, route_next, coordinator_node, course_advisor_node

# Create graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("coordinator", coordinator_node)
graph.add_node("course_advisor", course_advisor_node)
# ... add other nodes

# Add conditional edge using route_next
graph.add_conditional_edges(
    "coordinator",
    route_next,  # This function determines the next node
    {
        "coordinator": "coordinator",
        "course_advisor": "course_advisor",
        "learning_planner": "learning_planner",
        "human_input": "human_input",
        "end": "end",
    }
)
```

## Valid Node Names

The routing function recognizes these node names:

- `"coordinator"` - Coordinator agent for task routing
- `"course_advisor"` - Course advisor agent for course recommendations
- `"learning_planner"` - Learning planner agent for creating learning plans
- `"human_input"` - Human-in-the-loop interaction node
- `"end"` - Terminal node to end conversation

## Loop Prevention

The loop prevention mechanism protects against infinite loops:

- Each time a node executes, `loop_count` should be incremented
- When `loop_count` exceeds `max_loop_count`, routing automatically goes to `"end"`
- Default `max_loop_count` is 10, but can be customized
- This satisfies **Property 24: Loop Prevention** (Requirements 9.5)

Example:
```python
from src.graph import increment_loop_count, route_next

# In a node function
state = increment_loop_count(state)

# Later, when routing
next_node = route_next(state, max_loop_count=15)  # Custom limit
```

## Human-in-the-Loop Integration

The routing logic supports human intervention:

- When `requires_human_input` is `True`, routing goes to `"human_input"`
- This has higher priority than `next_agent` but lower than loop prevention
- Satisfies **Property 11: Human-in-the-Loop for Critical Decisions** (Requirements 6.1, 6.2)

Example:
```python
from src.graph import request_human_input, route_next

# Request human input
state = request_human_input(state)

# Routing will now go to human_input node
next_node = route_next(state)  # Returns "human_input"
```

## Error Handling

The routing function includes safe defaults:

- **Invalid `next_agent`**: Routes to `"end"` instead of crashing
- **`None` `next_agent`**: Routes to `"end"` (safe termination)
- **Missing state fields**: Python will raise appropriate errors (fail-fast)

This ensures the system never gets stuck in an undefined state.

## Testing

Comprehensive unit tests are provided in `tests/unit/test_routing.py`:

- ✅ Loop count exceeded routing
- ✅ Task completion routing
- ✅ Human input required routing
- ✅ All valid agent routing
- ✅ Invalid agent fallback
- ✅ Priority order verification
- ✅ Custom max loop count

Run tests:
```bash
pytest tests/unit/test_routing.py -v
```

## Example Usage

See `examples/routing_example.py` for a complete demonstration of routing scenarios.

Run example:
```bash
python examples/routing_example.py
```

## Requirements Validation

This implementation validates the following requirements:

- **Requirements 5.2**: Support conditional routing based on conversation state ✅
- **Requirements 9.5**: Detect and handle conversation loops or dead ends ✅
- **Requirements 6.1, 6.2**: Human-in-the-loop for critical decisions ✅

## Correctness Properties

The routing logic supports these correctness properties:

- **Property 8: Routing Correctness** - Correctly classifies intent and routes to appropriate agent
- **Property 24: Loop Prevention** - Detects and prevents infinite loops
- **Property 11: Human-in-the-Loop** - Ensures critical decisions require user approval

## Future Enhancements

Potential improvements for future iterations:

1. **Dynamic max loop count**: Load from configuration instead of hardcoded default
2. **Routing metrics**: Track routing decisions for analytics
3. **Routing history**: Maintain history of routing decisions in state
4. **Conditional routing rules**: Support more complex routing conditions
5. **A/B testing**: Support multiple routing strategies for experimentation

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
