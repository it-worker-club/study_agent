"""Unit tests for conversation flow control.

Tests the conversation flow management functions including:
- Context maintenance during agent transitions
- Topic switching and returning
- Subtask summarization
- Conversation health checks
"""

import pytest
from datetime import datetime

from src.graph.state import AgentState, Message, UserProfile, CourseInfo, LearningPlan
from src.graph.helpers import create_initial_state, add_message
from src.graph.conversation_flow import (
    maintain_context_on_transition,
    extract_conversation_context,
    build_context_summary_for_agent,
    ensure_context_consistency,
    detect_topic_switch,
    handle_topic_switch,
    return_to_previous_topic,
    summarize_subtask_completion,
    create_conversation_summary,
    check_conversation_health,
)


class TestContextMaintenance:
    """Tests for context maintenance during agent transitions."""
    
    def test_maintain_context_preserves_messages(self):
        """Test that context maintenance preserves all messages."""
        state = create_initial_state()
        state = add_message(state, "user", "Hello", None)
        state = add_message(state, "assistant", "Hi there", "coordinator")
        
        original_message_count = len(state["messages"])
        
        # Maintain context on transition
        state = maintain_context_on_transition(state, "coordinator", "course_advisor")
        
        # Messages should be preserved (possibly with one added)
        assert len(state["messages"]) >= original_message_count
    
    def test_maintain_context_preserves_user_profile(self):
        """Test that user profile is preserved during transitions."""
        state = create_initial_state()
        state["user_profile"]["background"] = "Software Engineer"
        state["user_profile"]["skill_level"] = "intermediate"
        state["user_profile"]["learning_goals"] = ["Learn Python"]
        
        # Maintain context on transition
        state = maintain_context_on_transition(state, "coordinator", "course_advisor")
        
        # User profile should be unchanged
        assert state["user_profile"]["background"] == "Software Engineer"
        assert state["user_profile"]["skill_level"] == "intermediate"
        assert state["user_profile"]["learning_goals"] == ["Learn Python"]
    
    def test_maintain_context_preserves_courses(self):
        """Test that course candidates are preserved during transitions."""
        state = create_initial_state()
        state["course_candidates"] = [
            {
                "title": "Python Course",
                "url": "https://example.com/python",
                "description": "Learn Python",
                "difficulty": "beginner",
                "duration": "10 hours",
                "rating": 4.5,
                "source": "geektime",
            }
        ]
        
        # Maintain context on transition
        state = maintain_context_on_transition(state, "course_advisor", "coordinator")
        
        # Courses should be preserved
        assert len(state["course_candidates"]) == 1
        assert state["course_candidates"][0]["title"] == "Python Course"
    
    def test_maintain_context_adds_transition_message(self):
        """Test that appropriate transition messages are added."""
        state = create_initial_state()
        original_count = len(state["messages"])
        
        # Transition from coordinator to course_advisor should add message
        state = maintain_context_on_transition(state, "coordinator", "course_advisor")
        
        # Should have added a transition message
        assert len(state["messages"]) == original_count + 1
        assert "查找" in state["messages"][-1]["content"] or "课程" in state["messages"][-1]["content"]


class TestContextExtraction:
    """Tests for context extraction and summarization."""
    
    def test_extract_context_identifies_phase(self):
        """Test that context extraction correctly identifies conversation phase."""
        state = create_initial_state()
        
        # Initial phase
        context = extract_conversation_context(state)
        assert context["phase"] == "initial_inquiry"
        
        # Add goals
        state["user_profile"]["learning_goals"] = ["Learn Python"]
        context = extract_conversation_context(state)
        assert context["phase"] == "goal_clarification"
        
        # Add courses
        state["course_candidates"] = [
            {
                "title": "Python Course",
                "url": "https://example.com/python",
                "description": "Learn Python",
                "difficulty": "beginner",
                "source": "geektime",
            }
        ]
        context = extract_conversation_context(state)
        assert context["phase"] == "course_selection"
        
        # Add plan
        state["learning_plan"] = {
            "goal": "Learn Python",
            "milestones": [{"name": "Basics"}],
            "recommended_courses": [],
            "estimated_duration": "3 months",
            "created_at": datetime.now(),
            "status": "draft",
        }
        context = extract_conversation_context(state)
        assert context["phase"] == "plan_review"
    
    def test_build_context_summary_includes_goals(self):
        """Test that context summary includes user goals."""
        state = create_initial_state()
        state["user_profile"]["learning_goals"] = ["Learn Python", "Build APIs"]
        
        summary = build_context_summary_for_agent(state, "course_advisor")
        
        assert "Learn Python" in summary or "学习目标" in summary
    
    def test_build_context_summary_includes_skill_level(self):
        """Test that context summary includes skill level."""
        state = create_initial_state()
        state["user_profile"]["skill_level"] = "intermediate"
        
        summary = build_context_summary_for_agent(state, "course_advisor")
        
        assert "intermediate" in summary or "中级" in summary or "技能水平" in summary


class TestContextConsistency:
    """Tests for context consistency checking."""
    
    def test_consistent_state_passes_check(self):
        """Test that a consistent state passes the check."""
        state = create_initial_state()
        state = add_message(state, "user", "Hello", None)
        
        is_consistent, issue = ensure_context_consistency(state)
        
        assert is_consistent
        assert issue is None
    
    def test_inconsistent_human_input_flag_detected(self):
        """Test that inconsistent human input flag is detected."""
        state = create_initial_state()
        state["requires_human_input"] = True
        state["next_agent"] = "coordinator"  # Should be "human_input"
        
        is_consistent, issue = ensure_context_consistency(state)
        
        assert not is_consistent
        assert "requires_human_input" in issue
    
    def test_inconsistent_complete_flag_detected(self):
        """Test that inconsistent complete flag is detected."""
        state = create_initial_state()
        state["is_complete"] = True
        state["next_agent"] = "coordinator"  # Should be "end" or None
        
        is_consistent, issue = ensure_context_consistency(state)
        
        assert not is_consistent
        assert "is_complete" in issue


class TestTopicSwitching:
    """Tests for topic switching and branching."""
    
    def test_detect_topic_switch_with_keywords(self):
        """Test that topic switches are detected with keywords."""
        state = create_initial_state()
        state = add_message(state, "user", "换个话题，我想问问关于Java的课程", None)
        
        topic_switch = detect_topic_switch(state)
        
        assert topic_switch == "new_topic"
    
    def test_detect_return_to_previous_topic(self):
        """Test that returns to previous topics are detected."""
        state = create_initial_state()
        state = add_message(state, "user", "回到之前的Python课程讨论", None)
        
        topic_switch = detect_topic_switch(state)
        
        assert topic_switch == "previous_topic"
    
    def test_no_topic_switch_detected(self):
        """Test that normal messages don't trigger topic switch detection."""
        state = create_initial_state()
        state = add_message(state, "user", "我想学习Python", None)
        
        topic_switch = detect_topic_switch(state)
        
        assert topic_switch is None
    
    def test_handle_topic_switch_saves_context(self):
        """Test that topic switching saves current context."""
        state = create_initial_state()
        state["current_task"] = "course_search"
        state["course_candidates"] = [
            {
                "title": "Python Course",
                "url": "https://example.com/python",
                "description": "Learn Python",
                "difficulty": "beginner",
                "source": "geektime",
            }
        ]
        
        # Handle topic switch
        state = handle_topic_switch(state, "new_topic")
        
        # Should have saved context in preferences
        assert "conversation_stack" in state["user_profile"]["preferences"]
        assert len(state["user_profile"]["preferences"]["conversation_stack"]) > 0
    
    def test_handle_topic_switch_routes_to_coordinator(self):
        """Test that topic switching routes to coordinator."""
        state = create_initial_state()
        
        state = handle_topic_switch(state, "new_topic")
        
        assert state["next_agent"] == "coordinator"
        assert state["current_task"] is None
    
    def test_return_to_previous_topic_restores_context(self):
        """Test that returning to previous topic restores context."""
        state = create_initial_state()
        
        # Save a context first
        state["user_profile"]["preferences"]["conversation_stack"] = [
            {
                "context": {
                    "phase": "course_selection",
                    "current_task": "course_search",
                },
                "timestamp": datetime.now().isoformat(),
            }
        ]
        
        # Return to previous topic
        state = return_to_previous_topic(state)
        
        # Should have restored task
        assert state["current_task"] == "course_search"
        assert state["next_agent"] == "coordinator"
    
    def test_return_to_previous_topic_with_empty_stack(self):
        """Test returning to previous topic when stack is empty."""
        state = create_initial_state()
        
        state = return_to_previous_topic(state)
        
        # Should add a message indicating no previous topic
        assert len(state["messages"]) > 0
        assert "没有" in state["messages"][-1]["content"] or "other" in state["messages"][-1]["content"].lower()


class TestSubtaskSummarization:
    """Tests for subtask summarization."""
    
    def test_summarize_course_search(self):
        """Test summarization of course search subtask."""
        state = create_initial_state()
        
        state = summarize_subtask_completion(
            state,
            subtask_name="course_search",
            subtask_result={"num_courses": 5},
        )
        
        # Should have added a summary message
        assert len(state["messages"]) > 0
        last_message = state["messages"][-1]
        assert "课程" in last_message["content"]
        assert "5" in last_message["content"]
    
    def test_summarize_learning_plan_creation(self):
        """Test summarization of learning plan creation."""
        state = create_initial_state()
        
        state = summarize_subtask_completion(
            state,
            subtask_name="learning_plan_creation",
            subtask_result={
                "milestones": [{"name": "M1"}, {"name": "M2"}],
                "estimated_duration": "3 months",
            },
        )
        
        # Should have added a summary message
        assert len(state["messages"]) > 0
        last_message = state["messages"][-1]
        assert "计划" in last_message["content"]
        assert "2" in last_message["content"]
    
    def test_summarize_plan_approval(self):
        """Test summarization of plan approval."""
        state = create_initial_state()
        
        state = summarize_subtask_completion(
            state,
            subtask_name="plan_approval",
            subtask_result={"status": "approved"},
        )
        
        # Should have added a summary message
        assert len(state["messages"]) > 0
        last_message = state["messages"][-1]
        assert "确认" in last_message["content"] or "批准" in last_message["content"]


class TestConversationSummary:
    """Tests for conversation summary generation."""
    
    def test_create_conversation_summary_basic(self):
        """Test basic conversation summary creation."""
        state = create_initial_state()
        state = add_message(state, "user", "Hello", None)
        state = add_message(state, "assistant", "Hi", "coordinator")
        
        summary = create_conversation_summary(state)
        
        assert state["conversation_id"] in summary
        assert "2" in summary  # 2 messages
    
    def test_create_conversation_summary_with_goals(self):
        """Test conversation summary includes goals."""
        state = create_initial_state()
        state["user_profile"]["learning_goals"] = ["Learn Python"]
        
        summary = create_conversation_summary(state)
        
        assert "Python" in summary or "学习目标" in summary
    
    def test_create_conversation_summary_with_plan(self):
        """Test conversation summary includes plan status."""
        state = create_initial_state()
        state["learning_plan"] = {
            "goal": "Learn Python",
            "milestones": [{"name": "M1"}],
            "recommended_courses": [],
            "estimated_duration": "3 months",
            "created_at": datetime.now(),
            "status": "approved",
        }
        
        summary = create_conversation_summary(state)
        
        assert "approved" in summary or "批准" in summary


class TestConversationHealth:
    """Tests for conversation health checking."""
    
    def test_healthy_conversation(self):
        """Test that a healthy conversation is identified."""
        state = create_initial_state()
        state = add_message(state, "user", "Hello", None)
        state["loop_count"] = 3
        
        health = check_conversation_health(state)
        
        assert health["health"] == "healthy"
        assert len(health["issues"]) == 0
    
    def test_high_loop_count_warning(self):
        """Test that high loop count triggers warning."""
        state = create_initial_state()
        state["loop_count"] = 9
        
        health = check_conversation_health(state)
        
        assert health["health"] == "warning"
        assert len(health["warnings"]) > 0
    
    def test_excessive_loop_count_issue(self):
        """Test that excessive loop count triggers issue."""
        state = create_initial_state()
        state["loop_count"] = 11
        
        health = check_conversation_health(state)
        
        assert health["health"] == "unhealthy"
        assert len(health["issues"]) > 0
    
    def test_no_progress_warning(self):
        """Test that lack of progress triggers warning."""
        state = create_initial_state()
        
        # Add many messages but no progress
        for i in range(12):
            state = add_message(state, "user", f"Message {i}", None)
        
        health = check_conversation_health(state)
        
        # Should have a warning about no progress
        assert health["health"] in ["warning", "unhealthy"]
    
    def test_inconsistent_state_issue(self):
        """Test that inconsistent state triggers issue."""
        state = create_initial_state()
        state["requires_human_input"] = True
        state["next_agent"] = "coordinator"  # Inconsistent
        
        health = check_conversation_health(state)
        
        assert health["health"] == "unhealthy"
        assert len(health["issues"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
