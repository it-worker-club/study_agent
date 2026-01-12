"""Unit tests for the Learning Planner agent."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.learning_planner import LearningPlannerAgent
from src.graph.state import AgentState, CourseInfo, Message
from src.llm.vllm_client import VLLMClientError
from src.tools.web_search import WebSearchError, WebSearchResult
from src.utils.config import AgentConfig


@pytest.fixture
def mock_vllm_client():
    """Create a mock vLLM client."""
    client = MagicMock()
    client.generate = AsyncMock()
    return client


@pytest.fixture
def mock_web_search_client():
    """Create a mock web search client."""
    client = MagicMock()
    return client


@pytest.fixture
def agent_config():
    """Create agent configuration."""
    return AgentConfig(
        temperature=0.6,
        max_tokens=2500,
    )


@pytest.fixture
def learning_planner_agent(mock_vllm_client, mock_web_search_client, agent_config):
    """Create a learning planner agent instance."""
    return LearningPlannerAgent(
        vllm_client=mock_vllm_client,
        web_search_client=mock_web_search_client,
        config=agent_config,
    )


@pytest.fixture
def sample_state():
    """Create a sample agent state."""
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
            "learning_goals": ["Python数据分析", "机器学习"],
            "time_availability": "每天2小时",
            "preferences": {},
        },
        "current_task": "制定Python数据分析学习计划",
        "next_agent": None,
        "course_candidates": [
            {
                "title": "Python数据分析实战",
                "url": "https://example.com/course1",
                "description": "从零开始学习Python数据分析",
                "difficulty": "intermediate",
                "duration": "8周",
                "rating": 4.5,
                "source": "geektime",
            },
            {
                "title": "数据可视化进阶",
                "url": "https://example.com/course2",
                "description": "掌握高级数据可视化技术",
                "difficulty": "advanced",
                "duration": "6周",
                "rating": 4.7,
                "source": "geektime",
            },
        ],
        "learning_plan": None,
        "requires_human_input": False,
        "human_feedback": None,
        "loop_count": 0,
        "is_complete": False,
    }


def test_learning_planner_initialization(learning_planner_agent):
    """Test learning planner agent initialization."""
    assert learning_planner_agent.role == "learning_planner"
    assert "learning_plan_creation" in learning_planner_agent.capabilities
    assert "milestone_planning" in learning_planner_agent.capabilities
    assert "time_estimation" in learning_planner_agent.capabilities
    assert "learning_path_research" in learning_planner_agent.capabilities


def test_get_capabilities(learning_planner_agent):
    """Test get_capabilities method."""
    capabilities = learning_planner_agent.get_capabilities()
    assert isinstance(capabilities, list)
    assert len(capabilities) == 4
    assert "learning_plan_creation" in capabilities


def test_get_role(learning_planner_agent):
    """Test get_role method."""
    assert learning_planner_agent.get_role() == "learning_planner"


def test_format_conversation_history(learning_planner_agent):
    """Test conversation history formatting."""
    messages = [
        {
            "role": "user",
            "content": "你好",
            "timestamp": datetime.now(),
            "agent": None,
        },
        {
            "role": "assistant",
            "content": "你好！有什么可以帮助你的？",
            "timestamp": datetime.now(),
            "agent": "coordinator",
        },
    ]
    
    formatted = learning_planner_agent._format_conversation_history(messages)
    assert "用户: 你好" in formatted
    assert "助手: 你好！有什么可以帮助你的？" in formatted


def test_format_conversation_history_empty(learning_planner_agent):
    """Test conversation history formatting with empty messages."""
    formatted = learning_planner_agent._format_conversation_history([])
    assert formatted == "（暂无对话历史）"


def test_extract_user_request_from_task(learning_planner_agent, sample_state):
    """Test extracting user request from current_task."""
    request = learning_planner_agent._extract_user_request(sample_state)
    assert request == "制定Python数据分析学习计划"


def test_extract_user_request_from_messages(learning_planner_agent, sample_state):
    """Test extracting user request from messages when no current_task."""
    sample_state["current_task"] = None
    request = learning_planner_agent._extract_user_request(sample_state)
    assert request == "我想学习Python数据分析"


def test_format_courses(learning_planner_agent, sample_state):
    """Test course formatting."""
    formatted = learning_planner_agent._format_courses(sample_state["course_candidates"])
    assert "Python数据分析实战" in formatted
    assert "数据可视化进阶" in formatted
    assert "intermediate" in formatted
    assert "8周" in formatted


def test_format_courses_empty(learning_planner_agent):
    """Test course formatting with empty list."""
    formatted = learning_planner_agent._format_courses([])
    assert formatted == "（暂无推荐课程）"


def test_format_learning_resources(learning_planner_agent):
    """Test learning resources formatting."""
    resources = [
        {
            "title": "Python数据分析学习路径",
            "source": "example.com",
            "snippet": "完整的学习路径指南",
            "url": "https://example.com/path",
        },
    ]
    
    formatted = learning_planner_agent._format_learning_resources(resources)
    assert "Python数据分析学习路径" in formatted
    assert "example.com" in formatted
    assert "完整的学习路径指南" in formatted


def test_format_learning_resources_empty(learning_planner_agent):
    """Test learning resources formatting with empty list."""
    formatted = learning_planner_agent._format_learning_resources([])
    assert formatted == "（暂无参考资料）"


@pytest.mark.asyncio
async def test_search_learning_resources_success(
    learning_planner_agent, mock_web_search_client, sample_state
):
    """Test successful learning resources search."""
    # Mock web search results
    mock_results = [
        WebSearchResult(
            title="Python数据分析学习路径",
            url="https://example.com/path",
            snippet="完整的学习路径",
            source="example.com",
        ),
    ]
    mock_web_search_client.search.return_value = mock_results
    
    # Mock LLM response for query generation
    learning_planner_agent.vllm_client.generate.return_value = json.dumps({
        "queries": ["Python数据分析学习路径", "数据分析最佳实践"]
    })
    
    resources = await learning_planner_agent._search_learning_resources(sample_state)
    
    assert isinstance(resources, list)
    assert len(resources) > 0
    assert mock_web_search_client.search.called


@pytest.mark.asyncio
async def test_search_learning_resources_fallback(
    learning_planner_agent, mock_web_search_client, sample_state
):
    """Test learning resources search with fallback queries."""
    # Mock web search results
    mock_results = [
        WebSearchResult(
            title="Python学习资源",
            url="https://example.com/resource",
            snippet="学习资源",
            source="example.com",
        ),
    ]
    mock_web_search_client.search.return_value = mock_results
    
    # Mock LLM response that doesn't contain valid JSON
    learning_planner_agent.vllm_client.generate.return_value = "Invalid response"
    
    resources = await learning_planner_agent._search_learning_resources(sample_state)
    
    assert isinstance(resources, list)
    # Should still search with fallback queries
    assert mock_web_search_client.search.called


def test_parse_learning_plan_success(learning_planner_agent, sample_state):
    """Test successful learning plan parsing."""
    response = json.dumps({
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
        ],
        "estimated_duration": "8周",
        "learning_advice": "循序渐进",
        "summary": "为您制定了完整的学习计划",
    })
    
    plan = learning_planner_agent._parse_learning_plan(response, sample_state)
    
    assert plan["goal"] == "掌握Python数据分析"
    assert len(plan["milestones"]) == 1
    assert plan["estimated_duration"] == "8周"
    assert plan["status"] == "draft"
    assert isinstance(plan["created_at"], datetime)


def test_parse_learning_plan_missing_field(learning_planner_agent, sample_state):
    """Test learning plan parsing with missing required field."""
    response = json.dumps({
        "goal": "掌握Python数据分析",
        # Missing milestones
        "estimated_duration": "8周",
    })
    
    with pytest.raises(ValueError, match="Missing required field"):
        learning_planner_agent._parse_learning_plan(response, sample_state)


def test_parse_learning_plan_invalid_json(learning_planner_agent, sample_state):
    """Test learning plan parsing with invalid JSON."""
    response = "This is not JSON"
    
    with pytest.raises(ValueError, match="No JSON found"):
        learning_planner_agent._parse_learning_plan(response, sample_state)


@pytest.mark.asyncio
async def test_create_learning_plan_success(
    learning_planner_agent, mock_web_search_client, sample_state
):
    """Test successful learning plan creation."""
    # Mock web search results
    mock_results = [
        WebSearchResult(
            title="学习路径",
            url="https://example.com/path",
            snippet="路径指南",
            source="example.com",
        ),
    ]
    mock_web_search_client.search.return_value = mock_results
    
    # Mock LLM responses
    learning_planner_agent.vllm_client.generate.side_effect = [
        # First call: query generation
        json.dumps({"queries": ["Python数据分析学习路径"]}),
        # Second call: plan generation
        json.dumps({
            "goal": "掌握Python数据分析",
            "milestones": [
                {
                    "title": "基础知识",
                    "content": "学习Python基础",
                    "courses": ["Python数据分析实战"],
                    "estimated_time": "2周",
                    "acceptance_criteria": "完成基础练习",
                    "tips": "多练习",
                },
            ],
            "estimated_duration": "8周",
            "learning_advice": "循序渐进",
            "summary": "为您制定了完整的学习计划",
        }),
    ]
    
    result = await learning_planner_agent.create_learning_plan(sample_state)
    
    assert "learning_plan" in result
    assert "learning_resources" in result
    assert "response" in result
    assert result["learning_plan"]["goal"] == "掌握Python数据分析"
    assert len(result["learning_plan"]["milestones"]) == 1


@pytest.mark.asyncio
async def test_create_learning_plan_llm_error(
    learning_planner_agent, mock_web_search_client, sample_state
):
    """Test learning plan creation with LLM error."""
    # Mock web search results
    mock_results = []
    mock_web_search_client.search.return_value = mock_results
    
    # Mock LLM error
    learning_planner_agent.vllm_client.generate.side_effect = VLLMClientError(
        "Service unavailable"
    )
    
    with pytest.raises(VLLMClientError):
        await learning_planner_agent.create_learning_plan(sample_state)
