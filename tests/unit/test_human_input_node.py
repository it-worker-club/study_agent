"""Unit tests for human input node.

Tests the human_input_node function which handles human-in-the-loop
interaction for critical decisions like learning plan approval and
course recommendation feedback.
"""

import pytest
from datetime import datetime

from src.graph.state import AgentState, LearningPlan, CourseInfo
from src.graph.nodes import human_input_node
from src.graph.helpers import create_initial_state, add_message


class TestHumanInputNode:
    """Test suite for human_input_node function."""
    
    def test_waiting_for_feedback_learning_plan(self):
        """Test that node prompts for feedback when learning plan needs approval."""
        # Create state with a draft learning plan
        state = create_initial_state()
        
        learning_plan: LearningPlan = {
            "goal": "学习 Python 数据分析",
            "milestones": [
                {"name": "基础语法", "duration": "2周"},
                {"name": "数据处理", "duration": "3周"},
            ],
            "recommended_courses": [],
            "estimated_duration": "5周",
            "created_at": datetime.now(),
            "status": "draft",
        }
        
        state["learning_plan"] = learning_plan
        state["requires_human_input"] = True
        state["human_feedback"] = None
        
        # Execute node
        result = human_input_node(state)
        
        # Should still require human input
        assert result["requires_human_input"] is True
        
        # Should have added a prompt message
        assert len(result["messages"]) > 0
        last_message = result["messages"][-1]
        assert last_message["role"] == "assistant"
        assert "学习计划" in last_message["content"]
        assert "同意" in last_message["content"] or "批准" in last_message["content"]
    
    def test_waiting_for_feedback_course_recommendations(self):
        """Test that node prompts for feedback when courses are recommended."""
        # Create state with course recommendations
        state = create_initial_state()
        
        course: CourseInfo = {
            "title": "Python 数据分析实战",
            "url": "https://example.com/course",
            "description": "学习数据分析",
            "difficulty": "intermediate",
            "duration": "10小时",
            "rating": 4.5,
            "source": "geektime",
        }
        
        state["course_candidates"] = [course]
        state["requires_human_input"] = True
        state["human_feedback"] = None
        
        # Execute node
        result = human_input_node(state)
        
        # Should still require human input
        assert result["requires_human_input"] is True
        
        # Should have added a prompt message
        assert len(result["messages"]) > 0
        last_message = result["messages"][-1]
        assert last_message["role"] == "assistant"
        assert "课程" in last_message["content"]
        assert "反馈" in last_message["content"]
    
    def test_approve_learning_plan(self):
        """Test approving a learning plan."""
        # Create state with draft learning plan and approval feedback
        state = create_initial_state()
        
        learning_plan: LearningPlan = {
            "goal": "学习 Python",
            "milestones": [{"name": "基础", "duration": "2周"}],
            "recommended_courses": [],
            "estimated_duration": "2周",
            "created_at": datetime.now(),
            "status": "draft",
        }
        
        state["learning_plan"] = learning_plan
        state["requires_human_input"] = True
        state["human_feedback"] = "同意这个计划"
        
        # Execute node
        result = human_input_node(state)
        
        # Should clear human input request
        assert result["requires_human_input"] is False
        assert result["human_feedback"] is None
        
        # Should approve the plan
        assert result["learning_plan"]["status"] == "approved"
        
        # Should route to coordinator
        assert result["next_agent"] == "coordinator"
        
        # Should have added user message and response
        assert len(result["messages"]) >= 2
        assert result["messages"][-2]["role"] == "user"
        assert result["messages"][-2]["content"] == "同意这个计划"
        assert result["messages"][-1]["role"] == "assistant"
        assert "确认" in result["messages"][-1]["content"]
    
    def test_request_plan_revision(self):
        """Test requesting learning plan revision."""
        # Create state with draft learning plan and revision request
        state = create_initial_state()
        
        learning_plan: LearningPlan = {
            "goal": "学习 Python",
            "milestones": [{"name": "基础", "duration": "2周"}],
            "recommended_courses": [],
            "estimated_duration": "2周",
            "created_at": datetime.now(),
            "status": "draft",
        }
        
        state["learning_plan"] = learning_plan
        state["requires_human_input"] = True
        state["human_feedback"] = "我想重新规划"
        
        # Execute node
        result = human_input_node(state)
        
        # Should clear human input request
        assert result["requires_human_input"] is False
        
        # Should keep plan as draft
        assert result["learning_plan"]["status"] == "draft"
        
        # Should set task for revision
        assert result["current_task"] == "revise_learning_plan"
        
        # Should route to coordinator
        assert result["next_agent"] == "coordinator"
    
    def test_specific_plan_feedback(self):
        """Test providing specific feedback on learning plan."""
        # Create state with draft learning plan and specific feedback
        state = create_initial_state()
        
        learning_plan: LearningPlan = {
            "goal": "学习 Python",
            "milestones": [{"name": "基础", "duration": "2周"}],
            "recommended_courses": [],
            "estimated_duration": "2周",
            "created_at": datetime.now(),
            "status": "draft",
        }
        
        state["learning_plan"] = learning_plan
        state["requires_human_input"] = True
        state["human_feedback"] = "我希望增加更多实战项目"
        
        # Execute node
        result = human_input_node(state)
        
        # Should clear human input request
        assert result["requires_human_input"] is False
        
        # Should set task for adjustment
        assert result["current_task"] == "adjust_learning_plan_with_feedback"
        
        # Should route to coordinator
        assert result["next_agent"] == "coordinator"
    
    def test_satisfied_with_courses(self):
        """Test user satisfied with course recommendations."""
        # Create state with courses and satisfaction feedback
        state = create_initial_state()
        
        course: CourseInfo = {
            "title": "Python 课程",
            "url": "https://example.com",
            "description": "学习 Python",
            "difficulty": "beginner",
            "duration": "10小时",
            "rating": 4.5,
            "source": "geektime",
        }
        
        state["course_candidates"] = [course]
        state["requires_human_input"] = True
        state["human_feedback"] = "这些课程很好，我很满意"
        
        # Execute node
        result = human_input_node(state)
        
        # Should clear human input request
        assert result["requires_human_input"] is False
        
        # Should route to coordinator
        assert result["next_agent"] == "coordinator"
        
        # Should have positive response
        assert "满意" in result["messages"][-1]["content"]
    
    def test_request_more_courses(self):
        """Test requesting more course recommendations."""
        # Create state with courses and request for more
        state = create_initial_state()
        
        course: CourseInfo = {
            "title": "Python 课程",
            "url": "https://example.com",
            "description": "学习 Python",
            "difficulty": "beginner",
            "duration": "10小时",
            "rating": 4.5,
            "source": "geektime",
        }
        
        state["course_candidates"] = [course]
        state["requires_human_input"] = True
        state["human_feedback"] = "能给我推荐更多课程吗？"
        
        # Execute node
        result = human_input_node(state)
        
        # Should clear human input request
        assert result["requires_human_input"] is False
        
        # Should set task for more courses
        assert result["current_task"] == "find_more_courses"
        
        # Should route to coordinator
        assert result["next_agent"] == "coordinator"
    
    def test_adjust_course_recommendations(self):
        """Test adjusting course recommendations based on feedback."""
        # Create state with courses and adjustment request
        state = create_initial_state()
        
        course: CourseInfo = {
            "title": "Python 课程",
            "url": "https://example.com",
            "description": "学习 Python",
            "difficulty": "beginner",
            "duration": "10小时",
            "rating": 4.5,
            "source": "geektime",
        }
        
        state["course_candidates"] = [course]
        state["requires_human_input"] = True
        state["human_feedback"] = "我想要更高级的课程"
        
        # Execute node
        result = human_input_node(state)
        
        # Should clear human input request
        assert result["requires_human_input"] is False
        
        # Should set task for adjustment
        assert result["current_task"] == "adjust_course_recommendations"
        
        # Should route to coordinator
        assert result["next_agent"] == "coordinator"
    
    def test_general_feedback(self):
        """Test handling general feedback without specific context."""
        # Create state with general feedback
        state = create_initial_state()
        state["requires_human_input"] = True
        state["human_feedback"] = "谢谢你的帮助"
        
        # Execute node
        result = human_input_node(state)
        
        # Should clear human input request
        assert result["requires_human_input"] is False
        
        # Should route to coordinator
        assert result["next_agent"] == "coordinator"
        
        # Should have acknowledgment
        assert len(result["messages"]) >= 2
    
    def test_empty_feedback_waits(self):
        """Test that empty feedback causes node to wait."""
        # Create state with empty feedback
        state = create_initial_state()
        state["requires_human_input"] = True
        state["human_feedback"] = ""
        
        # Execute node
        result = human_input_node(state)
        
        # Should still require human input
        assert result["requires_human_input"] is True
        
        # Should have prompt message
        assert len(result["messages"]) > 0
    
    def test_none_feedback_waits(self):
        """Test that None feedback causes node to wait."""
        # Create state with None feedback
        state = create_initial_state()
        state["requires_human_input"] = True
        state["human_feedback"] = None
        
        # Execute node
        result = human_input_node(state)
        
        # Should still require human input
        assert result["requires_human_input"] is True
        
        # Should have prompt message
        assert len(result["messages"]) > 0
    
    def test_feedback_added_as_user_message(self):
        """Test that feedback is added as a user message."""
        # Create state with feedback
        state = create_initial_state()
        state["requires_human_input"] = True
        state["human_feedback"] = "这是我的反馈"
        
        initial_message_count = len(state["messages"])
        
        # Execute node
        result = human_input_node(state)
        
        # Should have added at least 2 messages (user + assistant)
        assert len(result["messages"]) >= initial_message_count + 2
        
        # User message should be present
        user_messages = [m for m in result["messages"] if m["role"] == "user"]
        assert len(user_messages) > 0
        assert user_messages[-1]["content"] == "这是我的反馈"
    
    def test_multiple_approval_keywords(self):
        """Test various approval keywords for learning plan."""
        approval_keywords = ["同意", "批准", "确认", "好的", "可以", "approve", "yes"]
        
        for keyword in approval_keywords:
            # Create fresh state for each test
            state = create_initial_state()
            
            learning_plan: LearningPlan = {
                "goal": "学习 Python",
                "milestones": [{"name": "基础", "duration": "2周"}],
                "recommended_courses": [],
                "estimated_duration": "2周",
                "created_at": datetime.now(),
                "status": "draft",
            }
            
            state["learning_plan"] = learning_plan
            state["requires_human_input"] = True
            state["human_feedback"] = keyword
            
            # Execute node
            result = human_input_node(state)
            
            # Should approve the plan
            assert result["learning_plan"]["status"] == "approved", \
                f"Failed to approve with keyword: {keyword}"
    
    def test_multiple_revision_keywords(self):
        """Test various revision keywords for learning plan."""
        revision_keywords = ["重新", "不同", "修改", "调整", "redo", "change"]
        
        for keyword in revision_keywords:
            # Create fresh state for each test
            state = create_initial_state()
            
            learning_plan: LearningPlan = {
                "goal": "学习 Python",
                "milestones": [{"name": "基础", "duration": "2周"}],
                "recommended_courses": [],
                "estimated_duration": "2周",
                "created_at": datetime.now(),
                "status": "draft",
            }
            
            state["learning_plan"] = learning_plan
            state["requires_human_input"] = True
            state["human_feedback"] = keyword
            
            # Execute node
            result = human_input_node(state)
            
            # Should request revision
            assert result["current_task"] == "revise_learning_plan", \
                f"Failed to request revision with keyword: {keyword}"
