# Coordinator Agent Implementation

## Overview

This document describes the implementation of the Coordinator Agent for the Education Tutoring System, completed as part of Task 7 in the implementation plan.

## Components Implemented

### 1. CoordinatorAgent Class (`src/agents/coordinator.py`)

The coordinator agent is responsible for:
- Analyzing user input and identifying intent
- Making routing decisions to specialized agents
- Managing conversation flow and state transitions
- Requesting user clarification when needed

**Key Features:**
- Prompt template for intent recognition
- JSON-based decision parsing
- Robust error handling for invalid LLM responses
- Support for routing to: course_advisor, learning_planner, human_input, or end

**Methods:**
- `analyze_and_route(state)`: Main method that analyzes intent and returns routing decision
- `_build_prompt(state)`: Constructs the prompt with conversation history and user profile
- `_parse_decision(response)`: Parses LLM response into structured decision
- `_format_conversation_history(messages)`: Formats messages for prompt
- `_extract_user_input(messages)`: Extracts latest user message

### 2. Coordinator Node Function (`src/graph/nodes.py`)

The coordinator node function integrates the coordinator agent into the LangGraph workflow:
- Executes the coordinator agent's analysis
- Updates state with routing decisions
- Handles loop count to prevent infinite loops
- Manages error conditions gracefully

**Key Features:**
- Loop count tracking and limit enforcement (max 10 iterations)
- Async-to-sync bridge for LLM calls
- Comprehensive error handling (LLM errors, parsing errors, routing errors)
- State mutation with routing information

### 3. Supporting Infrastructure

**Module Exports:**
- Updated `src/agents/__init__.py` to export CoordinatorAgent
- Updated `src/graph/__init__.py` to export node functions
- Added `initialize_agents()` function for agent initialization

**Circular Import Resolution:**
- Used TYPE_CHECKING for type hints
- Lazy imports in node functions to avoid circular dependencies

## Testing

### Unit Tests for CoordinatorAgent (`tests/unit/test_coordinator.py`)

16 tests covering:
- Agent initialization and configuration
- Conversation history formatting
- User input extraction
- Prompt building
- Decision parsing (valid JSON, invalid JSON, missing fields)
- Intent analysis and routing
- Error handling

### Unit Tests for Coordinator Node (`tests/unit/test_coordinator_node.py`)

8 tests covering:
- Successful routing to different agents
- Loop limit enforcement
- LLM error handling
- Parse error handling
- Loop count incrementation
- State updates

**All 105 unit tests pass successfully.**

## Usage Example

```python
from src.agents.coordinator import CoordinatorAgent
from src.graph.nodes import initialize_agents, coordinator_node
from src.graph.helpers import create_initial_state, add_message
from src.llm.vllm_client import VLLMClient
from src.utils.config import load_config

# Load configuration
config = load_config("config/system_config.yaml")

# Create vLLM client
vllm_client = VLLMClient(config.vllm)

# Initialize agents
initialize_agents(config, vllm_client)

# Create initial state
state = create_initial_state()

# Add user message
state = add_message(
    state,
    role="user",
    content="我想学习 Python 数据分析",
    agent=None,
)

# Execute coordinator node
result_state = coordinator_node(state)

# Check routing decision
print(f"Next agent: {result_state['next_agent']}")
print(f"Current task: {result_state['current_task']}")
```

## Routing Logic

The coordinator uses the following decision rules:

1. **Course Advisor**: User asks about courses, wants recommendations, or inquires about specific courses
2. **Learning Planner**: User wants to create a learning plan or needs learning path planning
3. **Human Input**: User intent is unclear or more information is needed
4. **End**: User indicates they want to end the conversation (goodbye, thanks, etc.)

## Error Handling

The coordinator implements comprehensive error handling:

1. **LLM Errors**: Connection failures, timeouts, API errors → User-friendly error message
2. **Parse Errors**: Invalid JSON responses → Fallback to requesting clarification
3. **Loop Limit**: Exceeds 10 iterations → Automatically end conversation
4. **Invalid Agent**: Unknown agent name → Default to human_input

## Integration Points

The coordinator integrates with:
- **vLLM Client**: For LLM inference
- **State Management**: Reads and updates AgentState
- **Error Handler**: For consistent error handling
- **Graph Helpers**: For state manipulation utilities

## Next Steps

The coordinator is now ready to be integrated into the full LangGraph workflow. Future tasks include:

1. Implementing Course Advisor Agent (Task 8)
2. Implementing Learning Planner Agent (Task 9)
3. Building the complete LangGraph graph (Task 13)
4. Implementing human input node (Task 12)

## Requirements Validated

This implementation validates the following requirements:

- **Requirement 1.1**: System includes a Coordinator agent ✓
- **Requirement 5.1**: Coordinator analyzes intent and routes to appropriate agent ✓
- **Requirement 5.2**: System supports conditional routing based on conversation state ✓
- **Requirement 5.4**: Router distinguishes between different request types ✓
- **Requirement 5.5**: System asks for clarification when routing is uncertain ✓

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
