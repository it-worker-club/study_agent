"""Unit tests for the learning planner node function."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.graph.helpers import create_initial_state
from src.graph.nodes import learning_planner_node
from src.graph.state import AgentState
from src.llm.vllm_client import VLLMClientError
from src.tools.web_search import WebSearchError, WebSearchResult


@pytest.fixture
def sample_state():
    """Create a sample agent state."""
    state = create_initial_state("test-conv-123", "user-123")
    state["messages"] = [
        {
            "role": "user",
            "content": "我想制定一个Python数据分析的学习计划",
            "timestamp": datetime.now(),
            "agent": None,
        }
    ]
    state["user_profile"]["learning_goals"] = ["Python数据分析", "机器学习"]
    state["user_profile"]["skill_level"] = "intermediate"
    state["user_profile"]["time_availability"] = "每天2小时"
    state["current_task"] = "制定学习计划"
    state["course_candidates"] = [
        {
            "title": "Python数据分析实战",
            "url": "https://example.com/course1",
            "description": "从零开始学习Python数据分析",
            "difficulty": "intermediate",
            "duration": "8周",
            "rating": 4.5,
            "source": "geektime",
        },
    ]
    return state


@pytest.fixture
def mock_learning_planner_agent():
    """Create a mock learning planner agent."""
    agent = MagicMock()
    agent.create_learning_plan = AsyncMock()
    return agent


def test_learning_planner_node_success(sample_state, mock_learning_planner_agent):
    """Test successful learning planner node execution."""
    # Mock the learning plan result
    mock_learning_planner_agent.create_learning_plan.return_value = {
        "learning_plan": {
            "goal": "掌握Python数据分析",
            "milestones": [
                {
                    "title": "基础知识",
                    "content": "学习Python基础和NumPy",
                    "courses": ["Python数据分析实战"],
                    "estimated_time": "2周",
                    "acceptance_criteria": "能够使用NumPy进行数组操作",
                    "tips": "多做练习",
                },
                {
                    "title": "数据处理",
                    "content": "学习Pandas数据处理",
                    "courses": ["Python数据分析实战"],
                    "estimated_time": "3周",
                    "acceptance_criteria": "能够处理真实数据集",
                    "tips": "实践项目",
                },
            ],
            "recommended_courses": sample_state["course_candidates"],
            "estimated_duration": "8周",
            "created_at": datetime.now(),
            "status": "draft",
        },
        "learning_resources": [
            {
                "title": "Python学习路径",
                "url": "https://example.com/path",
                "snippet": "完整的学习路径",
                "source": "example.com",
            }
        ],
        "response": "我为您制定了一个8周的Python数据分析学习计划，包含2个主要里程碑。",
    }
    
    # Record initial message count
    initial_message_count = len(sample_state["messages"])
    
    # Patch the global agent
    with patch("src.graph.nodes._learning_planner_agent", mock_learning_planner_agent):
        result_state = learning_planner_node(sample_state)
    
    # Verify state updates
    assert result_state["learning_plan"] is not None
    assert result_state["learning_plan"]["goal"] == "掌握Python数据分析"
    assert len(result_state["learning_plan"]["milestones"]) == 2
    assert result_state["learning_plan"]["estimated_duration"] == "8周"
    
    # Verify message was added (includes summary message)
    assert len(result_state["messages"]) >= initial_message_count + 1
    
    # Find the learning planner's response message
    planner_messages = [
        msg for msg in result_state["messages"]
        if msg.get("agent") == "learning_planner"
    ]
    assert len(planner_messages) > 0
    assert "学习计划" in planner_messages[0]["content"]
    
    # Verify routing
    assert result_state["requires_human_input"] is True
    assert result_state["next_agent"] == "human_input"


def test_learning_planner_node_not_initialized(sample_state):
    """Test learning planner node when agent is not initialized."""
    # Record initial message count
    initial_message_count = len(sample_state["messages"])
    
    # Patch the global agent to None
    with patch("src.graph.nodes._learning_planner_agent", None):
        result_state = learning_planner_node(sample_state)
    
    # Should handle error gracefully
    assert len(result_state["messages"]) == initial_message_count + 1
    last_message = result_state["messages"][-1]
    assert "错误" in last_message["content"] or "问题" in last_message["content"]


def test_learning_planner_node_llm_error(sample_state, mock_learning_planner_agent):
    """Test learning planner node with LLM error."""
    # Record initial message count
    initial_message_count = len(sample_state["messages"])
    
    # Mock LLM error
    mock_learning_planner_agent.create_learning_plan.side_effect = VLLMClientError(
        "Service unavailable"
    )
    
    with patch("src.graph.nodes._learning_planner_agent", mock_learning_planner_agent):
        result_state = learning_planner_node(sample_state)
    
    # Should handle error gracefully
    assert len(result_state["messages"]) == initial_message_count + 1
    last_message = result_state["messages"][-1]
    assert "暂时不可用" in last_message["content"] or "服务" in last_message["content"]


def test_learning_planner_node_web_search_error(sample_state, mock_learning_planner_agent):
    """Test learning planner node with web search error."""
    # Record initial message count
    initial_message_count = len(sample_state["messages"])
    
    # Mock web search error
    mock_learning_planner_agent.create_learning_plan.side_effect = WebSearchError(
        "Search failed"
    )
    
    with patch("src.graph.nodes._learning_planner_agent", mock_learning_planner_agent):
        result_state = learning_planner_node(sample_state)
    
    # Should handle error gracefully
    assert len(result_state["messages"]) == initial_message_count + 1
    last_message = result_state["messages"][-1]
    # Should mention tool or search error
    assert any(
        keyword in last_message["content"]
        for keyword in ["工具", "搜索", "备用", "暂时"]
    )


def test_learning_planner_node_generic_error(sample_state, mock_learning_planner_agent):
    """Test learning planner node with generic error."""
    # Record initial message count
    initial_message_count = len(sample_state["messages"])
    
    # Mock generic error
    mock_learning_planner_agent.create_learning_plan.side_effect = Exception(
        "Unexpected error"
    )
    
    with patch("src.graph.nodes._learning_planner_agent", mock_learning_planner_agent):
        result_state = learning_planner_node(sample_state)
    
    # Should handle error gracefully
    assert len(result_state["messages"]) == initial_message_count + 1
    last_message = result_state["messages"][-1]
    assert "错误" in last_message["content"] or "问题" in last_message["content"]


def test_learning_planner_node_with_multiple_milestones(
    sample_state, mock_learning_planner_agent
):
    """Test learning planner node with multiple milestones."""
    # Mock a plan with 5 milestones
    milestones = [
        {
            "title": f"里程碑{i}",
            "content": f"学习内容{i}",
            "courses": ["Python数据分析实战"],
            "estimated_time": f"{i}周",
            "acceptance_criteria": f"完成标准{i}",
            "tips": f"建议{i}",
        }
        for i in range(1, 6)
    ]
    
    mock_learning_planner_agent.create_learning_plan.return_value = {
        "learning_plan": {
            "goal": "全面掌握Python数据分析",
            "milestones": milestones,
            "recommended_courses": sample_state["course_candidates"],
            "estimated_duration": "15周",
            "created_at": datetime.now(),
            "status": "draft",
        },
        "learning_resources": [],
        "response": "我为您制定了一个包含5个里程碑的详细学习计划。",
    }
    
    with patch("src.graph.nodes._learning_planner_agent", mock_learning_planner_agent):
        result_state = learning_planner_node(sample_state)
    
    # Verify all milestones are included
    assert len(result_state["learning_plan"]["milestones"]) == 5
    assert result_state["learning_plan"]["estimated_duration"] == "15周"


def test_learning_planner_node_requires_human_approval(
    sample_state, mock_learning_planner_agent
):
    """Test that learning planner node always requires human approval."""
    mock_learning_planner_agent.create_learning_plan.return_value = {
        "learning_plan": {
            "goal": "学习目标",
            "milestones": [
                {
                    "title": "里程碑1",
                    "content": "内容",
                    "courses": [],
                    "estimated_time": "1周",
                    "acceptance_criteria": "标准",
                    "tips": "建议",
                }
            ],
            "recommended_courses": [],
            "estimated_duration": "1周",
            "created_at": datetime.now(),
            "status": "draft",
        },
        "learning_resources": [],
        "response": "学习计划已制定。",
    }
    
    with patch("src.graph.nodes._learning_planner_agent", mock_learning_planner_agent):
        result_state = learning_planner_node(sample_state)
    
    # Should always require human input for plan approval
    assert result_state["requires_human_input"] is True
    assert result_state["next_agent"] == "human_input"


def test_learning_planner_node_preserves_conversation_id(
    sample_state, mock_learning_planner_agent
):
    """Test that learning planner node preserves conversation ID."""
    mock_learning_planner_agent.create_learning_plan.return_value = {
        "learning_plan": {
            "goal": "学习目标",
            "milestones": [],
            "recommended_courses": [],
            "estimated_duration": "1周",
            "created_at": datetime.now(),
            "status": "draft",
        },
        "learning_resources": [],
        "response": "计划已制定。",
    }
    
    original_conv_id = sample_state["conversation_id"]
    
    with patch("src.graph.nodes._learning_planner_agent", mock_learning_planner_agent):
        result_state = learning_planner_node(sample_state)
    
    assert result_state["conversation_id"] == original_conv_id
