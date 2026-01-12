# Human Input Node Implementation

## Overview

The human input node (`human_input_node`) implements human-in-the-loop interaction for the education tutoring system. It handles critical decision points where user approval or feedback is required, such as learning plan approval and course recommendation feedback.

## Implementation Details

### Location
- **Module**: `src/graph/nodes.py`
- **Function**: `human_input_node(state: AgentState) -> AgentState`
- **Tests**: `tests/unit/test_human_input_node.py`

### Functionality

The human input node operates in two modes:

#### 1. Waiting Mode (No Feedback Yet)
When `state["human_feedback"]` is `None` or empty:
- Analyzes the current context (learning plan, course recommendations, etc.)
- Generates an appropriate prompt for the user
- Keeps `requires_human_input` as `True`
- Returns state for the application layer to collect user input

#### 2. Processing Mode (Feedback Received)
When `state["human_feedback"]` contains user input:
- Adds the feedback as a user message
- Processes the feedback based on context
- Updates state accordingly (approve plan, request revision, etc.)
- Clears `requires_human_input` and `human_feedback`
- Routes back to coordinator for next steps

### Supported Contexts

#### Learning Plan Approval
When a draft learning plan exists:
- **Approval keywords**: 同意, 批准, 确认, 好的, 可以, approve, yes
  - Action: Sets plan status to "approved"
- **Revision keywords**: 重新, 不同, 修改, 调整, redo, change
  - Action: Sets task to "revise_learning_plan"
- **Specific feedback**: Any other input
  - Action: Sets task to "adjust_learning_plan_with_feedback"

#### Course Recommendation Feedback
When course candidates exist:
- **Satisfaction keywords**: 满意, 好的, 可以, 不错, satisfied, good
  - Action: Acknowledges satisfaction
- **More courses keywords**: 更多, 其他, 别的, more, other
  - Action: Sets task to "find_more_courses"
- **Adjustment feedback**: Any other input
  - Action: Sets task to "adjust_course_recommendations"

#### General Feedback
For any other context:
- Acknowledges the feedback
- Routes to coordinator for handling

## Integration with Application Layer

The human input node is designed to work with an application layer (UI/API) that:

1. **Detects** when `state["requires_human_input"]` is `True`
2. **Pauses** graph execution
3. **Collects** user input through UI/API
4. **Places** the input in `state["human_feedback"]`
5. **Resumes** graph execution

### Example Flow

```python
# Application layer pseudo-code
while not state["is_complete"]:
    # Execute graph step
    state = graph.invoke(state)
    
    # Check if human input is needed
    if state["requires_human_input"]:
        # Pause and collect input
        user_input = await collect_user_input()
        
        # Update state with feedback
        state["human_feedback"] = user_input
        
        # Continue execution (will process feedback)
        state = graph.invoke(state)
```

## State Updates

### Input State Fields
- `requires_human_input`: Boolean indicating if input is needed
- `human_feedback`: String containing user's feedback (or None)
- `learning_plan`: Optional learning plan object
- `course_candidates`: List of recommended courses
- `messages`: Conversation history

### Output State Fields
- `requires_human_input`: Set to False after processing
- `human_feedback`: Cleared (set to None)
- `next_agent`: Set to "coordinator"
- `current_task`: Updated based on feedback type
- `messages`: Updated with user feedback and system response
- `learning_plan.status`: Updated if plan was approved

## Requirements Validated

This implementation validates the following requirements:

- **Requirement 6.1**: WHEN Learning_Planner creates a learning plan, THE System SHALL present it to user for approval
- **Requirement 6.2**: WHEN Course_Advisor recommends courses, THE System SHALL allow user to provide feedback
- **Requirement 6.3**: THE System SHALL support user interruption at any point in the conversation
- **Requirement 6.4**: WHEN user provides feedback, THE System SHALL adjust recommendations accordingly
- **Requirement 6.5**: THE System SHALL provide clear prompts for user input when human intervention is needed

## Testing

The implementation includes comprehensive unit tests covering:

1. **Waiting scenarios**:
   - Prompting for learning plan approval
   - Prompting for course recommendation feedback
   - Handling empty/None feedback

2. **Learning plan feedback**:
   - Approving plans with various keywords
   - Requesting revisions
   - Providing specific adjustment feedback

3. **Course recommendation feedback**:
   - Expressing satisfaction
   - Requesting more courses
   - Requesting adjustments

4. **General feedback**:
   - Handling feedback without specific context
   - Adding feedback as user messages

5. **Edge cases**:
   - Multiple approval keywords
   - Multiple revision keywords
   - Empty and None feedback

All tests pass successfully, validating the implementation.

## Usage Example

```python
from src.graph.nodes import human_input_node
from src.graph.helpers import create_initial_state

# Create state with a draft learning plan
state = create_initial_state()
state["learning_plan"] = {
    "goal": "学习 Python",
    "milestones": [...],
    "status": "draft",
    ...
}
state["requires_human_input"] = True

# First call - prompts for input
state = human_input_node(state)
# state["requires_human_input"] is still True
# state["messages"] contains prompt

# User provides feedback (done by application layer)
state["human_feedback"] = "同意这个计划"

# Second call - processes feedback
state = human_input_node(state)
# state["requires_human_input"] is now False
# state["learning_plan"]["status"] is "approved"
# state["next_agent"] is "coordinator"
```

## Future Enhancements

Potential improvements for future iterations:

1. **Structured feedback**: Support for structured feedback forms (ratings, selections)
2. **Timeout handling**: Automatic timeout if user doesn't respond within a time limit
3. **Feedback history**: Track all feedback for analytics and improvement
4. **Multi-language support**: Better support for different languages
5. **Context-aware prompts**: More sophisticated prompt generation based on conversation history
6. **Validation**: Input validation for specific feedback types

## Related Components

- **Coordinator Agent**: Routes to human_input_node when needed
- **Learning Planner Agent**: Sets requires_human_input for plan approval
- **Course Advisor Agent**: Can request feedback on recommendations
- **Router Function**: Routes to human_input_node based on state
- **State Helpers**: Provides utility functions for state manipulation

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
