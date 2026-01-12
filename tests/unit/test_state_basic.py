"""Basic unit tests for state management functionality."""

import pytest
from datetime import datetime

from src.graph import (
    create_initial_state,
    validate_state,
    add_message,
    increment_loop_count,
    mark_complete,
    request_human_input,
    clear_human_input_request,
)


def test_create_initial_state():
    """Test creating an initial state with default values."""
    state = create_initial_state()
    
    # Verify basic structure
    assert "conversation_id" in state
    assert "messages" in state
    assert "user_profile" in state
    assert isinstance(state["messages"], list)
    assert len(state["messages"]) == 0
    
    # Verify user profile
    assert "user_id" in state["user_profile"]
    assert isinstance(state["user_profile"]["learning_goals"], list)
    assert isinstance(state["user_profile"]["preferences"], dict)
    
    # Verify control fields
    assert state["loop_count"] == 0
    assert state["is_complete"] is False
    assert state["requires_human_input"] is False


def test_create_initial_state_with_ids():
    """Test creating an initial state with custom IDs."""
    conv_id = "test-conversation-123"
    user_id = "test-user-456"
    
    state = create_initial_state(conversation_id=conv_id, user_id=user_id)
    
    assert state["conversation_id"] == conv_id
    assert state["user_profile"]["user_id"] == user_id


def test_validate_state_valid():
    """Test validating a valid state."""
    state = create_initial_state()
    is_valid, error = validate_state(state)
    
    assert is_valid is True
    assert error is None


def test_validate_state_missing_field():
    """Test validating a state with missing field."""
    state = create_initial_state()
    del state["conversation_id"]
    
    is_valid, error = validate_state(state)
    
    assert is_valid is False
    assert "conversation_id" in error


def test_add_message():
    """Test adding a message to state."""
    state = create_initial_state()
    
    state = add_message(state, "user", "Hello, I want to learn Python", agent=None)
    
    assert len(state["messages"]) == 1
    assert state["messages"][0]["role"] == "user"
    assert state["messages"][0]["content"] == "Hello, I want to learn Python"
    assert isinstance(state["messages"][0]["timestamp"], datetime)


def test_increment_loop_count():
    """Test incrementing loop count."""
    state = create_initial_state()
    
    assert state["loop_count"] == 0
    
    state = increment_loop_count(state)
    assert state["loop_count"] == 1
    
    state = increment_loop_count(state)
    assert state["loop_count"] == 2


def test_mark_complete():
    """Test marking task as complete."""
    state = create_initial_state()
    
    state = mark_complete(state)
    
    assert state["is_complete"] is True
    assert state["next_agent"] == "end"


def test_request_human_input():
    """Test requesting human input."""
    state = create_initial_state()
    
    state = request_human_input(state)
    
    assert state["requires_human_input"] is True
    assert state["next_agent"] == "human_input"


def test_clear_human_input_request():
    """Test clearing human input request."""
    state = create_initial_state()
    state["requires_human_input"] = True
    state["human_feedback"] = "Some feedback"
    
    state = clear_human_input_request(state)
    
    assert state["requires_human_input"] is False
    assert state["human_feedback"] is None


def test_validate_state_with_messages():
    """Test validating state with messages."""
    state = create_initial_state()
    state = add_message(state, "user", "Test message")
    
    is_valid, error = validate_state(state)
    
    assert is_valid is True
    assert error is None


def test_validate_state_invalid_skill_level():
    """Test validating state with invalid skill level."""
    state = create_initial_state()
    state["user_profile"]["skill_level"] = "expert"  # Invalid level
    
    is_valid, error = validate_state(state)
    
    assert is_valid is False
    assert "skill_level" in error


def test_validate_state_invalid_next_agent():
    """Test validating state with invalid next_agent."""
    state = create_initial_state()
    state["next_agent"] = "invalid_agent"
    
    is_valid, error = validate_state(state)
    
    assert is_valid is False
    assert "next_agent" in error
