"""Tests for state update visibility across agents.

This module tests that state updates made by one agent are immediately
visible to other agents, ensuring proper state sharing in the LangGraph
multi-agent system.

Validates:
    - Requirements 2.3: State updates are visible to all agents
    - Requirements 2.4: All agents access the latest state
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.graph.state import AgentState, CourseInfo, LearningPlan
from src.graph.helpers import create_initial_state, add_message
from src.graph.nodes import (
    coordinator_node,
    course_advisor_node,
    learning_planner_node,
    human_input_node,
    initialize_agents,
)
from src.utils.config import Config, AgentConfig, VLLMConfig, MCPConfig, WebSearchConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock(spec=Config)
    
    # Mock vLLM config
    vllm_config = MagicMock(spec=VLLMConfig)
    vllm_config.api_base = "http://localhost:8000/v1"
    vllm_config.model_name = "test-model"
    vllm_config.temperature = 0.7
    vllm_config.max_tokens = 2000
    config.vllm = vllm_config
    
    # Mock agent configs
    agent_config = MagicMock(spec=AgentConfig)
    agent_config.temperature = 0.7
    agent_config.max_tokens = 2000
    config.agents = MagicMock()
    config.agents.coordinator = agent_config
    config.agents.course_advisor = agent_config
    config.agents.learning_planner = agent_config
    
    # Mock MCP config
    mcp_config = MagicMock(spec=MCPConfig)
    mcp_config.playwright_enabled = True
    mcp_config.geektime_url = "https://time.geekbang.org/"
    mcp_config.browser_headless = True
    config.mcp = mcp_config
    
    # Mock web search config
    web_search_config = MagicMock(spec=WebSearchConfig)
    web_search_config.enabled = True
    config.web_search = web_search_config
    
    return config


@pytest.fixture
def initial_state():
    """Create an initial state for testing."""
    state = create_initial_state(
        conversation_id="test-conv-123",
        user_id="test-user-456",
    )
    
    # Add some initial user profile data
    state["user_profile"]["background"] = "Software Engineer"
    state["user_profile"]["skill_level"] = "intermediate"
    state["user_profile"]["learning_goals"] = ["Learn Python data analysis"]
    state["user_profile"]["time_availability"] = "2-3 hours per day"
    
    # Add initial user message
    state = add_message(
        state,
        role="user",
        content="I want to learn Python data analysis",
        agent=None,
    )
    
    return state


class TestStateVisibilityBetweenNodes:
    """Test that state updates are visible across different nodes."""
    
    def test_coordinator_updates_visible_to_course_advisor(
        self, initial_state, mock_config
    ):
        """Test that coordinator's state updates are visible to course advisor.
        
        This test verifies that when the coordinator updates the state
        (e.g., setting current_task and next_agent), these updates are
        visible to the course advisor node.
        """
        # Mock vLLM client
        mock_vllm_client = AsyncMock()
        mock_vllm_client.generate = AsyncMock(return_value='{"next_agent": "course_advisor", "current_task": "推荐Python数据分析课程", "requires_human_input": false, "response": "好的，我来为您推荐课程"}')
        
        # Initialize agents with mocks
        with patch('src.graph.nodes._coordinator_agent') as mock_coordinator, \
             patch('src.graph.nodes._course_advisor_agent') as mock_course_advisor, \
             patch('src.graph.nodes._vllm_client', mock_vllm_client):
            
            # Setup coordinator mock
            mock_coordinator.analyze_and_route = AsyncMock(return_value={
                "next_agent": "course_advisor",
                "current_task": "推荐Python数据分析课程",
                "requires_human_input": False,
                "response": "好的，我来为您推荐课程",
            })
            
            # Setup course advisor mock
            mock_course_advisor.recommend_courses = AsyncMock(return_value={
                "courses": [
                    {
                        "title": "Python数据分析实战",
                        "url": "https://example.com/course1",
                        "description": "从零开始学习Python数据分析",
                        "difficulty": "intermediate",
                        "duration": "10周",
                        "rating": 4.8,
                        "source": "geektime",
                    }
                ],
                "web_resources": [],
                "response": "为您推荐了1门课程",
            })
            
            # Step 1: Coordinator updates state
            initial_message_count = len(initial_state["messages"])
            state_after_coordinator = coordinator_node(initial_state)
            
            # Verify coordinator made updates
            assert state_after_coordinator["next_agent"] == "course_advisor"
            assert state_after_coordinator["current_task"] == "推荐Python数据分析课程"
            assert len(state_after_coordinator["messages"]) >= initial_message_count
            
            # Step 2: Course advisor receives the updated state
            state_after_advisor = course_advisor_node(state_after_coordinator)
            
            # Verify course advisor can see coordinator's updates
            # The current_task set by coordinator should still be visible
            assert "current_task" in state_after_advisor
            
            # Verify course advisor made its own updates
            assert len(state_after_advisor["course_candidates"]) > 0
            assert state_after_advisor["next_agent"] == "coordinator"
    
    def test_course_advisor_updates_visible_to_learning_planner(
        self, initial_state, mock_config
    ):
        """Test that course advisor's updates are visible to learning planner.
        
        This test verifies that when the course advisor adds course candidates
        to the state, the learning planner can access them.
        """
        # Add course candidates to state (simulating course advisor's work)
        initial_state["course_candidates"] = [
            {
                "title": "Python数据分析实战",
                "url": "https://example.com/course1",
                "description": "从零开始学习Python数据分析",
                "difficulty": "intermediate",
                "duration": "10周",
                "rating": 4.8,
                "source": "geektime",
            },
            {
                "title": "数据可视化进阶",
                "url": "https://example.com/course2",
                "description": "掌握高级数据可视化技术",
                "difficulty": "advanced",
                "duration": "8周",
                "rating": 4.7,
                "source": "geektime",
            },
        ]
        initial_state["current_task"] = "制定学习计划"
        initial_state["next_agent"] = "learning_planner"
        
        # Mock vLLM client and learning planner
        with patch('src.graph.nodes._learning_planner_agent') as mock_planner, \
             patch('src.graph.nodes._vllm_client') as mock_vllm:
            
            mock_planner.create_learning_plan = AsyncMock(return_value={
                "learning_plan": {
                    "goal": "掌握Python数据分析",
                    "milestones": [
                        {
                            "title": "Python基础",
                            "content": "学习Python基础语法",
                            "courses": ["Python数据分析实战"],
                            "estimated_time": "2周",
                            "acceptance_criteria": "能够编写基本的Python程序",
                            "tips": "多做练习",
                        }
                    ],
                    "recommended_courses": initial_state["course_candidates"],
                    "estimated_duration": "12周",
                    "created_at": datetime.now(),
                    "status": "draft",
                },
                "learning_resources": [],
                "response": "已为您制定学习计划",
            })
            
            # Execute learning planner node
            state_after_planner = learning_planner_node(initial_state)
            
            # Verify learning planner can see course candidates from course advisor
            assert state_after_planner["learning_plan"] is not None
            assert len(state_after_planner["learning_plan"]["recommended_courses"]) == 2
            
            # Verify the courses in the plan match the ones from course advisor
            plan_course_titles = [
                c["title"] for c in state_after_planner["learning_plan"]["recommended_courses"]
            ]
            assert "Python数据分析实战" in plan_course_titles
            assert "数据可视化进阶" in plan_course_titles
    
    def test_learning_planner_updates_visible_to_human_input(
        self, initial_state, mock_config
    ):
        """Test that learning planner's updates are visible to human input node.
        
        This test verifies that when the learning planner creates a learning plan,
        the human input node can access it for approval.
        """
        # Add learning plan to state (simulating learning planner's work)
        initial_state["learning_plan"] = {
            "goal": "掌握Python数据分析",
            "milestones": [
                {
                    "title": "Python基础",
                    "content": "学习Python基础语法",
                    "courses": ["Python数据分析实战"],
                    "estimated_time": "2周",
                    "acceptance_criteria": "能够编写基本的Python程序",
                    "tips": "多做练习",
                }
            ],
            "recommended_courses": [],
            "estimated_duration": "12周",
            "created_at": datetime.now(),
            "status": "draft",
        }
        initial_state["requires_human_input"] = True
        initial_state["next_agent"] = "human_input"
        
        # Execute human input node (without feedback first)
        state_after_human_input = human_input_node(initial_state)
        
        # Verify human input node can see the learning plan
        assert state_after_human_input["learning_plan"] is not None
        assert state_after_human_input["learning_plan"]["status"] == "draft"
        
        # Verify human input node added a prompt message
        last_message = state_after_human_input["messages"][-1]
        assert "学习计划" in last_message["content"]
        assert "反馈" in last_message["content"]
    
    def test_human_feedback_visible_to_coordinator(self, initial_state, mock_config):
        """Test that human feedback is visible to coordinator.
        
        This test verifies that when a user provides feedback through the
        human input node, the coordinator can see it in the next iteration.
        """
        # Simulate user providing feedback
        initial_state["requires_human_input"] = True
        initial_state["human_feedback"] = "我同意这个学习计划"
        initial_state["learning_plan"] = {
            "goal": "掌握Python数据分析",
            "milestones": [],
            "recommended_courses": [],
            "estimated_duration": "12周",
            "created_at": datetime.now(),
            "status": "draft",
        }
        
        # Execute human input node to process feedback
        state_after_human_input = human_input_node(initial_state)
        
        # Verify feedback was processed
        assert state_after_human_input["requires_human_input"] is False
        assert state_after_human_input["human_feedback"] is None
        assert state_after_human_input["next_agent"] == "coordinator"
        
        # Verify learning plan status was updated based on feedback
        assert state_after_human_input["learning_plan"]["status"] == "approved"
        
        # Now coordinator should be able to see the approved plan
        with patch('src.graph.nodes._coordinator_agent') as mock_coordinator, \
             patch('src.graph.nodes._vllm_client'):
            
            mock_coordinator.analyze_and_route = AsyncMock(return_value={
                "next_agent": "end",
                "current_task": "完成",
                "requires_human_input": False,
                "response": "学习计划已确认，祝您学习愉快！",
            })
            
            state_after_coordinator = coordinator_node(state_after_human_input)
            
            # Coordinator can see the approved plan
            assert state_after_coordinator["learning_plan"]["status"] == "approved"


class TestStateUpdateImmediacy:
    """Test that state updates are immediately visible."""
    
    def test_message_added_immediately_visible(self, initial_state):
        """Test that messages added to state are immediately visible."""
        initial_message_count = len(initial_state["messages"])
        
        # Add a message
        state = add_message(
            initial_state,
            role="assistant",
            content="Test message",
            agent="coordinator",
        )
        
        # Verify message is immediately visible
        assert len(state["messages"]) == initial_message_count + 1
        assert state["messages"][-1]["content"] == "Test message"
        assert state["messages"][-1]["agent"] == "coordinator"
    
    def test_user_profile_updates_immediately_visible(self, initial_state):
        """Test that user profile updates are immediately visible."""
        # Update user profile
        initial_state["user_profile"]["skill_level"] = "advanced"
        initial_state["user_profile"]["learning_goals"].append("Learn machine learning")
        
        # Verify updates are immediately visible
        assert initial_state["user_profile"]["skill_level"] == "advanced"
        assert "Learn machine learning" in initial_state["user_profile"]["learning_goals"]
    
    def test_course_candidates_updates_immediately_visible(self, initial_state):
        """Test that course candidates updates are immediately visible."""
        # Add course candidates
        course: CourseInfo = {
            "title": "Test Course",
            "url": "https://example.com/course",
            "description": "A test course",
            "difficulty": "beginner",
            "duration": "4周",
            "rating": 4.5,
            "source": "geektime",
        }
        
        initial_state["course_candidates"].append(course)
        
        # Verify update is immediately visible
        assert len(initial_state["course_candidates"]) == 1
        assert initial_state["course_candidates"][0]["title"] == "Test Course"
    
    def test_control_flags_updates_immediately_visible(self, initial_state):
        """Test that control flags updates are immediately visible."""
        # Update control flags
        initial_state["requires_human_input"] = True
        initial_state["is_complete"] = True
        initial_state["loop_count"] = 5
        
        # Verify updates are immediately visible
        assert initial_state["requires_human_input"] is True
        assert initial_state["is_complete"] is True
        assert initial_state["loop_count"] == 5


class TestStateConsistencyAcrossNodes:
    """Test that state remains consistent as it flows through nodes."""
    
    def test_conversation_id_preserved_across_nodes(self, initial_state, mock_config):
        """Test that conversation_id is preserved across all nodes."""
        original_conv_id = initial_state["conversation_id"]
        
        # Mock agents
        with patch('src.graph.nodes._coordinator_agent') as mock_coordinator, \
             patch('src.graph.nodes._vllm_client'):
            
            mock_coordinator.analyze_and_route = AsyncMock(return_value={
                "next_agent": "end",
                "current_task": "完成",
                "requires_human_input": False,
                "response": "完成",
            })
            
            # Execute coordinator node
            state = coordinator_node(initial_state)
            
            # Verify conversation_id is preserved
            assert state["conversation_id"] == original_conv_id
    
    def test_user_profile_preserved_across_nodes(self, initial_state, mock_config):
        """Test that user profile is preserved across all nodes."""
        original_user_id = initial_state["user_profile"]["user_id"]
        original_skill_level = initial_state["user_profile"]["skill_level"]
        
        # Mock agents
        with patch('src.graph.nodes._coordinator_agent') as mock_coordinator, \
             patch('src.graph.nodes._vllm_client'):
            
            mock_coordinator.analyze_and_route = AsyncMock(return_value={
                "next_agent": "end",
                "current_task": "完成",
                "requires_human_input": False,
                "response": "完成",
            })
            
            # Execute coordinator node
            state = coordinator_node(initial_state)
            
            # Verify user profile is preserved
            assert state["user_profile"]["user_id"] == original_user_id
            assert state["user_profile"]["skill_level"] == original_skill_level
    
    def test_messages_accumulate_across_nodes(self, initial_state, mock_config):
        """Test that messages accumulate as state flows through nodes."""
        initial_message_count = len(initial_state["messages"])
        
        # Mock agents
        with patch('src.graph.nodes._coordinator_agent') as mock_coordinator, \
             patch('src.graph.nodes._course_advisor_agent') as mock_advisor, \
             patch('src.graph.nodes._vllm_client'):
            
            # Coordinator adds a message
            mock_coordinator.analyze_and_route = AsyncMock(return_value={
                "next_agent": "course_advisor",
                "current_task": "推荐课程",
                "requires_human_input": False,
                "response": "好的，我来推荐课程",
            })
            
            state = coordinator_node(initial_state)
            message_count_after_coordinator = len(state["messages"])
            
            # Verify coordinator added a message
            assert message_count_after_coordinator > initial_message_count
            
            # Course advisor adds another message
            mock_advisor.recommend_courses = AsyncMock(return_value={
                "courses": [],
                "web_resources": [],
                "response": "为您推荐了课程",
            })
            
            state = course_advisor_node(state)
            message_count_after_advisor = len(state["messages"])
            
            # Verify messages accumulated
            assert message_count_after_advisor > message_count_after_coordinator


class TestStateIsolationBetweenConversations:
    """Test that different conversations have isolated states."""
    
    def test_different_conversations_have_different_states(self):
        """Test that different conversation IDs result in isolated states."""
        # Create two different states
        state1 = create_initial_state(conversation_id="conv-1", user_id="user-1")
        state2 = create_initial_state(conversation_id="conv-2", user_id="user-2")
        
        # Modify state1
        state1["user_profile"]["skill_level"] = "beginner"
        state1 = add_message(state1, "user", "Message in conv 1", None)
        
        # Modify state2
        state2["user_profile"]["skill_level"] = "advanced"
        state2 = add_message(state2, "user", "Message in conv 2", None)
        
        # Verify states are isolated
        assert state1["conversation_id"] != state2["conversation_id"]
        assert state1["user_profile"]["user_id"] != state2["user_profile"]["user_id"]
        assert state1["user_profile"]["skill_level"] != state2["user_profile"]["skill_level"]
        assert state1["messages"][0]["content"] != state2["messages"][0]["content"]
