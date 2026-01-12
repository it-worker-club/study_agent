"""Unit tests for course advisor node function"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.graph.nodes import course_advisor_node, initialize_agents
from src.graph.state import AgentState
from src.llm.vllm_client import VLLMClient, VLLMClientError
from src.tools.mcp_playwright import MCPPlaywrightError
from src.tools.web_search import WebSearchError
from src.utils.config import (
    Config,
    VLLMConfig,
    MCPConfig,
    WebSearchConfig,
    SystemConfig,
    AgentsConfig,
    AgentConfig,
)


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    return Config(
        vllm=VLLMConfig(
            api_base="http://localhost:8000/v1",
            model_name="test-model",
            temperature=0.7,
            max_tokens=2000,
            timeout=60,
        ),
        mcp=MCPConfig(
            playwright_enabled=True,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
            browser_timeout=30000,
        ),
        web_search=WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        ),
        system=SystemConfig(),
        agents=AgentsConfig(
            coordinator=AgentConfig(temperature=0.7, max_tokens=1500),
            course_advisor=AgentConfig(temperature=0.6, max_tokens=2000),
            learning_planner=AgentConfig(temperature=0.5, max_tokens=2500),
        ),
    )


@pytest.fixture
def mock_vllm_client():
    """Create a mock vLLM client"""
    client = MagicMock(spec=VLLMClient)
    client.generate = AsyncMock()
    return client


@pytest.fixture
def sample_state():
    """Create a sample agent state"""
    return {
        "messages": [
            {
                "role": "user",
                "content": "我想学习Python数据分析",
                "timestamp": datetime.now(),
                "agent": None,
            }
        ],
        "conversation_id": "test-conv-123",
        "user_profile": {
            "user_id": "user-123",
            "background": "软件工程师",
            "skill_level": "intermediate",
            "learning_goals": ["Python数据分析"],
            "time_availability": "每天2小时",
            "preferences": {},
        },
        "current_task": "推荐Python数据分析课程",
        "next_agent": "course_advisor",
        "course_candidates": [],
        "learning_plan": None,
        "requires_human_input": False,
        "human_feedback": None,
        "loop_count": 1,
        "is_complete": False,
    }


def test_course_advisor_node_success(mock_config, mock_vllm_client, sample_state):
    """Test course advisor node with successful execution"""
    # Mock LLM responses
    mock_vllm_client.generate.side_effect = [
        # Tool selection
        '{"tools": [{"name": "search_geektime", "query": "Python数据分析"}]}',
        # Recommendation
        "我为您推荐以下Python数据分析课程：\n1. Python数据分析实战",
    ]
    
    # Initialize agents
    with patch("src.graph.nodes._course_advisor_agent") as mock_advisor:
        # Mock the recommend_courses method
        mock_advisor.recommend_courses = AsyncMock(
            return_value={
                "courses": [
                    {
                        "title": "Python数据分析实战",
                        "url": "https://geektime.com/course1",
                        "description": "实战课程",
                        "difficulty": "intermediate",
                        "duration": "20小时",
                        "rating": 4.8,
                        "source": "geektime",
                    }
                ],
                "web_resources": [],
                "response": "我为您推荐以下Python数据分析课程：\n1. Python数据分析实战",
            }
        )
        
        # Execute node
        result_state = course_advisor_node(sample_state)
        
        # Verify state updates
        assert len(result_state["course_candidates"]) == 1
        assert result_state["course_candidates"][0]["title"] == "Python数据分析实战"
        assert result_state["next_agent"] == "coordinator"
        
        # Verify message was added (includes summary message)
        assert len(result_state["messages"]) >= 2
        
        # Find the course advisor's response message
        advisor_messages = [
            msg for msg in result_state["messages"]
            if msg.get("agent") == "course_advisor"
        ]
        assert len(advisor_messages) > 0
        assert "推荐" in advisor_messages[0]["content"]


def test_course_advisor_node_not_initialized(sample_state):
    """Test course advisor node when agent is not initialized"""
    # Ensure agent is not initialized
    initial_message_count = len(sample_state["messages"])
    
    with patch("src.graph.nodes._course_advisor_agent", None):
        result_state = course_advisor_node(sample_state)
        
        # Should handle error gracefully
        assert len(result_state["messages"]) > initial_message_count
        error_message = result_state["messages"][-1]["content"]
        assert "错误" in error_message or "不可用" in error_message


def test_course_advisor_node_llm_error(sample_state):
    """Test course advisor node handles LLM errors"""
    initial_message_count = len(sample_state["messages"])
    
    with patch("src.graph.nodes._course_advisor_agent") as mock_advisor:
        # Mock LLM error
        mock_advisor.recommend_courses = AsyncMock(
            side_effect=VLLMClientError("Service unavailable")
        )
        
        result_state = course_advisor_node(sample_state)
        
        # Should handle error gracefully
        assert len(result_state["messages"]) > initial_message_count
        error_message = result_state["messages"][-1]["content"]
        assert "AI 服务" in error_message or "不可用" in error_message


def test_course_advisor_node_tool_error(sample_state):
    """Test course advisor node handles tool errors"""
    initial_message_count = len(sample_state["messages"])
    
    with patch("src.graph.nodes._course_advisor_agent") as mock_advisor:
        # Mock tool error
        mock_advisor.recommend_courses = AsyncMock(
            side_effect=MCPPlaywrightError("Connection failed")
        )
        
        result_state = course_advisor_node(sample_state)
        
        # Should handle error gracefully
        assert len(result_state["messages"]) > initial_message_count
        error_message = result_state["messages"][-1]["content"]
        # Error handler should provide fallback message
        assert len(error_message) > 0


def test_course_advisor_node_generic_error(sample_state):
    """Test course advisor node handles generic errors"""
    initial_message_count = len(sample_state["messages"])
    
    with patch("src.graph.nodes._course_advisor_agent") as mock_advisor:
        # Mock generic error
        mock_advisor.recommend_courses = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        result_state = course_advisor_node(sample_state)
        
        # Should handle error gracefully
        assert len(result_state["messages"]) > initial_message_count


def test_course_advisor_node_multiple_courses(sample_state):
    """Test course advisor node with multiple course recommendations"""
    with patch("src.graph.nodes._course_advisor_agent") as mock_advisor:
        # Mock multiple courses
        mock_advisor.recommend_courses = AsyncMock(
            return_value={
                "courses": [
                    {
                        "title": "Python数据分析实战",
                        "url": "https://geektime.com/course1",
                        "description": "实战课程",
                        "difficulty": "intermediate",
                        "duration": "20小时",
                        "rating": 4.8,
                        "source": "geektime",
                    },
                    {
                        "title": "Python核心技术",
                        "url": "https://geektime.com/course2",
                        "description": "核心技术",
                        "difficulty": "beginner",
                        "duration": "15小时",
                        "rating": 4.7,
                        "source": "geektime",
                    },
                    {
                        "title": "机器学习入门",
                        "url": "https://geektime.com/course3",
                        "description": "机器学习基础",
                        "difficulty": "intermediate",
                        "duration": "25小时",
                        "rating": 4.9,
                        "source": "geektime",
                    },
                ],
                "web_resources": [
                    {
                        "title": "Python教程",
                        "url": "https://example.com/tutorial",
                        "snippet": "学习Python",
                        "source": "example.com",
                    }
                ],
                "response": "我为您推荐以下3门课程...",
            }
        )
        
        result_state = course_advisor_node(sample_state)
        
        # Verify multiple courses were added
        assert len(result_state["course_candidates"]) == 3
        assert result_state["course_candidates"][0]["title"] == "Python数据分析实战"
        assert result_state["course_candidates"][1]["title"] == "Python核心技术"
        assert result_state["course_candidates"][2]["title"] == "机器学习入门"


def test_course_advisor_node_routes_to_coordinator(sample_state):
    """Test that course advisor node routes back to coordinator"""
    with patch("src.graph.nodes._course_advisor_agent") as mock_advisor:
        mock_advisor.recommend_courses = AsyncMock(
            return_value={
                "courses": [],
                "web_resources": [],
                "response": "未找到合适的课程",
            }
        )
        
        result_state = course_advisor_node(sample_state)
        
        # Should route back to coordinator
        assert result_state["next_agent"] == "coordinator"
