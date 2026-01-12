# Conversation Flow Control Implementation

## Overview

This document describes the implementation of conversation flow control for the education tutoring system. The implementation ensures smooth conversation flow, context maintenance, topic switching support, and subtask summarization.

## Requirements Addressed

- **Requirement 9.1**: Maintain conversation context throughout the session
- **Requirement 9.2**: Provide smooth transitions when switching between agents
- **Requirement 9.3**: Support conversation branching and returning to previous topics
- **Requirement 9.4**: Summarize results before proceeding when a subtask is completed

## Implementation Components

### 1. Context Maintenance (`src/graph/conversation_flow.py`)

#### `maintain_context_on_transition()`

Ensures conversation context is preserved during agent transitions.

**Features:**
- Preserves all conversation history
- Maintains user profile and preferences
- Keeps course candidates and learning plans
- Adds appropriate transition messages
- Logs context preservation

**Usage:**
```python
from src.graph.conversation_flow import maintain_context_on_transition

# During agent transition
state = maintain_context_on_transition(state, "coordinator", "course_advisor")
```

#### `extract_conversation_context()`

Extracts key context information from the conversation state.

**Returns:**
- Current conversation phase
- Recent messages
- User goals and preferences
- Course and plan status
- Current task

**Usage:**
```python
from src.graph.conversation_flow import extract_conversation_context

context = extract_conversation_context(state)
print(f"Phase: {context['phase']}")
print(f"User goals: {context['user_goals']}")
```

#### `build_context_summary_for_agent()`

Creates a natural language summary of conversation context for agents.

**Features:**
- Includes user goals and background
- Shows skill level
- Lists course recommendations
- Displays plan status
- Mentions current task

**Usage:**
```python
from src.graph.conversation_flow import build_context_summary_for_agent

summary = build_context_summary_for_agent(state, "course_advisor")
# Use summary in agent prompts
```

#### `ensure_context_consistency()`

Verifies that conversation context is consistent.

**Checks:**
- Learning plan references valid courses
- Human input flags are consistent
- Complete flags match next_agent
- No conflicting states

**Usage:**
```python
from src.graph.conversation_flow import ensure_context_consistency

is_consistent, issue = ensure_context_consistency(state)
if not is_consistent:
    print(f"Consistency issue: {issue}")
```

### 2. Topic Switching and Branching

#### `detect_topic_switch()`

Detects when the user is switching topics or returning to previous topics.

**Detection Keywords:**
- **New topic**: "换个话题", "另外", "还有", "对了", "顺便问一下"
- **Previous topic**: "回到", "之前", "刚才", "前面"

**Returns:**
- `"new_topic"`: User is switching to a new topic
- `"previous_topic"`: User wants to return to previous topic
- `None`: Normal conversation flow

**Usage:**
```python
from src.graph.conversation_flow import detect_topic_switch

topic_switch = detect_topic_switch(state)
if topic_switch == "new_topic":
    # Handle new topic
    pass
```

#### `handle_topic_switch()`

Handles a topic switch by saving current context and preparing for new topic.

**Actions:**
- Saves current context to conversation stack
- Acknowledges the topic switch
- Clears current task
- Routes to coordinator

**Usage:**
```python
from src.graph.conversation_flow import handle_topic_switch

if topic_switch == "new_topic":
    state = handle_topic_switch(state, "new_topic")
```

#### `return_to_previous_topic()`

Returns to a previously saved topic context.

**Actions:**
- Retrieves previous context from stack
- Acknowledges the return
- Restores task context
- Routes to coordinator

**Usage:**
```python
from src.graph.conversation_flow import return_to_previous_topic

if topic_switch == "previous_topic":
    state = return_to_previous_topic(state)
```

### 3. Subtask Summarization

#### `summarize_subtask_completion()`

Summarizes the completion of a subtask before proceeding.

**Supported Subtasks:**
- `course_search`: Course recommendation completion
- `learning_plan_creation`: Learning plan creation
- `plan_approval`: Plan approval/rejection
- `course_recommendation_feedback`: User feedback on courses

**Features:**
- Creates context-appropriate summaries
- Uses checkmark (✓) for visual clarity
- Provides next steps guidance
- Adds summary to conversation

**Usage:**
```python
from src.graph.conversation_flow import summarize_subtask_completion

state = summarize_subtask_completion(
    state,
    subtask_name="course_search",
    subtask_result={"num_courses": 5},
)
```

### 4. Conversation Monitoring

#### `create_conversation_summary()`

Creates a comprehensive summary of the entire conversation.

**Includes:**
- Conversation metadata (ID, message count, loop count)
- User information (goals, skill level)
- Progress (courses, plan status)
- Current state (task, next agent)

**Usage:**
```python
from src.graph.conversation_flow import create_conversation_summary

summary = create_conversation_summary(state)
print(summary)
```

#### `check_conversation_health()`

Checks the health of the conversation flow.

**Health Indicators:**
- **Healthy**: No issues or warnings
- **Warning**: High loop count, no progress
- **Unhealthy**: Loop limit exceeded, inconsistent state

**Checks:**
- Loop count (warning at 8, issue at 10+)
- Progress (courses or plan after 10+ messages)
- User goals captured
- Context consistency

**Usage:**
```python
from src.graph.conversation_flow import check_conversation_health

health = check_conversation_health(state)
if health["health"] == "unhealthy":
    print(f"Issues: {health['issues']}")
```

## Integration with Graph Nodes

### Updated Node Functions

All node functions have been updated to use conversation flow control:

#### `coordinator_node()`
- Detects topic switches
- Handles new topics and returns to previous topics
- Maintains context on transitions

#### `course_advisor_node()`
- Summarizes course search completion
- Maintains context when returning to coordinator

#### `learning_planner_node()`
- Summarizes plan creation completion
- Maintains context when transitioning to human input

#### `human_input_node()`
- Summarizes feedback processing
- Maintains context when returning to coordinator

## Testing

### Unit Tests (`tests/unit/test_conversation_flow.py`)

Comprehensive test coverage including:

1. **Context Maintenance Tests**
   - Message preservation
   - User profile preservation
   - Course preservation
   - Transition message addition

2. **Context Extraction Tests**
   - Phase identification
   - Goal inclusion
   - Skill level inclusion

3. **Context Consistency Tests**
   - Consistent state validation
   - Inconsistent flag detection

4. **Topic Switching Tests**
   - Topic switch detection
   - Previous topic detection
   - Context saving
   - Context restoration

5. **Subtask Summarization Tests**
   - Course search summary
   - Plan creation summary
   - Plan approval summary

6. **Conversation Health Tests**
   - Healthy conversation
   - High loop count warning
   - Excessive loop count issue
   - No progress warning

### Test Results

All 28 tests pass successfully:
```
tests/unit/test_conversation_flow.py::TestContextMaintenance ✓ 4 tests
tests/unit/test_conversation_flow.py::TestContextExtraction ✓ 3 tests
tests/unit/test_conversation_flow.py::TestContextConsistency ✓ 3 tests
tests/unit/test_conversation_flow.py::TestTopicSwitching ✓ 7 tests
tests/unit/test_conversation_flow.py::TestSubtaskSummarization ✓ 3 tests
tests/unit/test_conversation_flow.py::TestConversationSummary ✓ 3 tests
tests/unit/test_conversation_flow.py::TestConversationHealth ✓ 5 tests
```

## Examples

See `examples/conversation_flow_example.py` for comprehensive examples demonstrating:

1. Context maintenance during transitions
2. Context extraction and summarization
3. Topic switching and branching
4. Subtask summarization
5. Conversation health checking
6. Complete conversation flow

Run the examples:
```bash
python examples/conversation_flow_example.py
```

## Usage Guidelines

### When to Use Context Maintenance

Use `maintain_context_on_transition()` whenever transitioning between agents:

```python
# In coordinator_node
to_agent = decision["next_agent"]
if to_agent and to_agent != "coordinator":
    state = maintain_context_on_transition(state, "coordinator", to_agent)
```

### When to Detect Topic Switches

Detect topic switches in the coordinator node before routing:

```python
# In coordinator_node
topic_switch = detect_topic_switch(state)

if topic_switch == "new_topic":
    state = handle_topic_switch(state, "new_topic")
elif topic_switch == "previous_topic":
    state = return_to_previous_topic(state)
    return state  # Already routed
```

### When to Summarize Subtasks

Summarize subtasks after completing major operations:

```python
# After course search
state = summarize_subtask_completion(
    state,
    subtask_name="course_search",
    subtask_result={"num_courses": len(courses)},
)

# After plan creation
state = summarize_subtask_completion(
    state,
    subtask_name="learning_plan_creation",
    subtask_result={
        "milestones": plan["milestones"],
        "estimated_duration": plan["estimated_duration"],
    },
)
```

### When to Check Conversation Health

Check conversation health periodically or when issues are suspected:

```python
# In main application loop
health = check_conversation_health(state)

if health["health"] == "unhealthy":
    logger.warning(f"Conversation health issues: {health['issues']}")
    # Take corrective action
```

## Best Practices

1. **Always maintain context on transitions**: Ensures smooth user experience
2. **Detect topic switches early**: Prevents confusion and maintains relevance
3. **Summarize after major operations**: Helps users understand progress
4. **Check consistency regularly**: Catches bugs early
5. **Monitor conversation health**: Prevents infinite loops and stalled conversations

## Future Enhancements

Potential improvements:

1. **Advanced topic detection**: Use LLM to detect subtle topic changes
2. **Context compression**: Summarize old context to save memory
3. **Multi-level topic stack**: Support nested topic switches
4. **Automatic health recovery**: Self-healing for unhealthy conversations
5. **Context visualization**: UI for viewing conversation flow

## Conclusion

The conversation flow control implementation provides robust support for:
- ✓ Context maintenance across agent transitions
- ✓ Smooth transitions with appropriate messaging
- ✓ Topic switching and branching
- ✓ Subtask summarization
- ✓ Conversation health monitoring

All requirements (9.1, 9.2, 9.3, 9.4) are fully implemented and tested.

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
