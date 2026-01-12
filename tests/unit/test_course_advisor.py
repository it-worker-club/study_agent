"""Unit tests for Course Advisor agent"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.course_advisor import CourseAdvisorAgent
from src.graph.state import AgentState, CourseInfo, Message, UserProfile
from src.llm.vllm_client import VLLMClient, VLLMClientError
from src.tools.mcp_playwright import MCPPlaywrightClient
from src.tools.web_search import WebSearchClient, WebSearchResult
from src.utils.config import AgentConfig


@pytest.fixture
def mock_vllm_client():
    """Create a mock vLLM client"""
    client = MagicMock(spec=VLLMClient)
    client.generate = AsyncMock()
    return client


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP Playwright client"""
    client = MagicMock(spec=MCPPlaywrightClient)
    return client


@pytest.fixture
def mock_web_search_client():
    """Create a mock web search client"""
    client = MagicMock(spec=WebSearchClient)
    return client


@pytest.fixture
def agent_config():
    """Create agent configuration"""
    return AgentConfig(temperature=0.7, max_tokens=2000)


@pytest.fixture
def course_advisor(mock_vllm_client, mock_mcp_client, mock_web_search_client, agent_config):
    """Create a course advisor agent"""
    return CourseAdvisorAgent(
        vllm_client=mock_vllm_client,
        mcp_client=mock_mcp_client,
        web_search_client=mock_web_search_client,
        config=agent_config,
    )


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
            "learning_goals": ["Python数据分析", "机器学习"],
            "time_availability": "每天2小时",
            "preferences": {},
        },
        "current_task": "推荐Python数据分析课程",
        "next_agent": None,
        "course_candidates": [],
        "learning_plan": None,
        "requires_human_input": False,
        "human_feedback": None,
        "loop_count": 0,
        "is_complete": False,
    }


def test_course_advisor_initialization(course_advisor):
    """Test course advisor initialization"""
    assert course_advisor.role == "course_advisor"
    assert "course_search" in course_advisor.capabilities
    assert "course_recommendation" in course_advisor.capabilities
    assert "course_analysis" in course_advisor.capabilities
    assert "web_resource_search" in course_advisor.capabilities


def test_get_capabilities(course_advisor):
    """Test getting agent capabilities"""
    capabilities = course_advisor.get_capabilities()
    assert isinstance(capabilities, list)
    assert len(capabilities) == 4
    assert "course_search" in capabilities


def test_get_role(course_advisor):
    """Test getting agent role"""
    role = course_advisor.get_role()
    assert role == "course_advisor"


def test_format_conversation_history(course_advisor, sample_state):
    """Test conversation history formatting"""
    history = course_advisor._format_conversation_history(sample_state["messages"])
    assert "用户: 我想学习Python数据分析" in history


def test_format_conversation_history_empty(course_advisor):
    """Test conversation history formatting with empty messages"""
    history = course_advisor._format_conversation_history([])
    assert history == "（暂无对话历史）"


def test_extract_user_request_from_task(course_advisor, sample_state):
    """Test extracting user request from current_task"""
    request = course_advisor._extract_user_request(sample_state)
    assert request == "推荐Python数据分析课程"


def test_extract_user_request_from_messages(course_advisor, sample_state):
    """Test extracting user request from messages when no current_task"""
    sample_state["current_task"] = None
    request = course_advisor._extract_user_request(sample_state)
    assert request == "我想学习Python数据分析"


def test_get_default_tools(course_advisor):
    """Test getting default tool selection"""
    tools = course_advisor._get_default_tools("Python数据分析")
    assert len(tools) == 2
    assert tools[0]["name"] == "search_geektime"
    assert tools[0]["query"] == "Python数据分析"
    assert tools[1]["name"] == "web_search"


def test_format_courses(course_advisor):
    """Test formatting course information"""
    courses = [
        {
            "title": "Python核心技术",
            "url": "https://example.com/course1",
            "description": "学习Python核心技术",
            "difficulty": "intermediate",
            "duration": "20小时",
            "rating": 4.8,
            "source": "geektime",
        }
    ]
    formatted = course_advisor._format_courses(courses)
    assert "Python核心技术" in formatted
    assert "intermediate" in formatted
    assert "20小时" in formatted


def test_format_courses_empty(course_advisor):
    """Test formatting empty course list"""
    formatted = course_advisor._format_courses([])
    assert formatted == "（暂无可用课程）"


def test_format_web_resources(course_advisor):
    """Test formatting web resources"""
    resources = [
        {
            "title": "Python教程",
            "url": "https://example.com/tutorial",
            "snippet": "学习Python的最佳教程",
            "source": "example.com",
        }
    ]
    formatted = course_advisor._format_web_resources(resources)
    assert "Python教程" in formatted
    assert "example.com" in formatted


def test_format_web_resources_empty(course_advisor):
    """Test formatting empty web resources"""
    formatted = course_advisor._format_web_resources([])
    assert formatted == "（暂无补充资源）"


@pytest.mark.asyncio
async def test_select_tools_success(course_advisor, mock_vllm_client, sample_state):
    """Test tool selection with valid LLM response"""
    # Mock LLM response with tool selection
    mock_vllm_client.generate.return_value = '''
    {
        "tools": [
            {"name": "search_geektime", "query": "Python数据分析"},
            {"name": "web_search", "query": "Python数据分析教程"}
        ]
    }
    '''
    
    tools = await course_advisor._select_tools(sample_state)
    
    assert len(tools) == 2
    assert tools[0]["name"] == "search_geektime"
    assert tools[1]["name"] == "web_search"
    mock_vllm_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_select_tools_fallback(course_advisor, mock_vllm_client, sample_state):
    """Test tool selection falls back to defaults on error"""
    # Mock LLM error
    mock_vllm_client.generate.side_effect = Exception("LLM error")
    
    tools = await course_advisor._select_tools(sample_state)
    
    # Should return default tools
    assert len(tools) == 2
    assert tools[0]["name"] == "search_geektime"


@pytest.mark.asyncio
async def test_search_courses_success(course_advisor, mock_mcp_client, mock_web_search_client):
    """Test searching courses with both tools"""
    # Mock MCP Playwright results
    mock_mcp_client.search_geektime_courses.return_value = [
        {
            "title": "Python数据分析",
            "url": "https://geektime.com/course1",
            "description": "学习数据分析",
            "difficulty": "intermediate",
            "duration": "20小时",
            "rating": 4.8,
            "source": "geektime",
        }
    ]
    
    # Mock web search results
    mock_web_search_client.search.return_value = [
        WebSearchResult(
            title="Python教程",
            url="https://example.com/tutorial",
            snippet="学习Python",
        )
    ]
    
    tools = [
        {"name": "search_geektime", "query": "Python"},
        {"name": "web_search", "query": "Python教程"},
    ]
    
    courses, web_resources = await course_advisor._search_courses(tools)
    
    assert len(courses) == 1
    assert courses[0]["title"] == "Python数据分析"
    assert len(web_resources) == 1
    assert web_resources[0]["title"] == "Python教程"


@pytest.mark.asyncio
async def test_search_courses_tool_error(course_advisor, mock_mcp_client, mock_web_search_client):
    """Test searching courses handles tool errors gracefully"""
    # Mock MCP error
    from src.tools.mcp_playwright import MCPPlaywrightError
    mock_mcp_client.search_geektime_courses.side_effect = MCPPlaywrightError("Connection failed")
    
    # Mock web search success
    mock_web_search_client.search.return_value = [
        WebSearchResult(
            title="Python教程",
            url="https://example.com/tutorial",
            snippet="学习Python",
        )
    ]
    
    tools = [
        {"name": "search_geektime", "query": "Python"},
        {"name": "web_search", "query": "Python教程"},
    ]
    
    courses, web_resources = await course_advisor._search_courses(tools)
    
    # Should continue with web search even if MCP fails
    assert len(courses) == 0
    assert len(web_resources) == 1


@pytest.mark.asyncio
async def test_recommend_courses_success(
    course_advisor,
    mock_vllm_client,
    mock_mcp_client,
    mock_web_search_client,
    sample_state,
):
    """Test complete course recommendation flow"""
    # Mock tool selection
    mock_vllm_client.generate.side_effect = [
        # Tool selection response
        '{"tools": [{"name": "search_geektime", "query": "Python数据分析"}]}',
        # Recommendation response
        "我为您推荐以下Python数据分析课程：\n1. Python数据分析实战\n这门课程非常适合您...",
    ]
    
    # Mock course search
    mock_mcp_client.search_geektime_courses.return_value = [
        {
            "title": "Python数据分析实战",
            "url": "https://geektime.com/course1",
            "description": "实战课程",
            "difficulty": "intermediate",
            "duration": "20小时",
            "rating": 4.8,
            "source": "geektime",
        }
    ]
    
    mock_web_search_client.search.return_value = []
    
    result = await course_advisor.recommend_courses(sample_state)
    
    assert "courses" in result
    assert "web_resources" in result
    assert "response" in result
    assert len(result["courses"]) == 1
    assert "推荐" in result["response"]


@pytest.mark.asyncio
async def test_recommend_courses_llm_error(
    course_advisor,
    mock_vllm_client,
    sample_state,
):
    """Test course recommendation handles LLM errors"""
    # Mock LLM error
    mock_vllm_client.generate.side_effect = VLLMClientError("Service unavailable")
    
    with pytest.raises(VLLMClientError):
        await course_advisor.recommend_courses(sample_state)
