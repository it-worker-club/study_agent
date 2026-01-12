"""Unit tests for the coordinator agent"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.coordinator import CoordinatorAgent
from src.graph.state import AgentState, Message, UserProfile
from src.graph.helpers import create_initial_state
from src.llm.vllm_client import VLLMClient
from src.utils.config import AgentConfig


@pytest.fixture
def mock_vllm_client():
    """Create a mock vLLM client"""
    client = MagicMock(spec=VLLMClient)
    client.generate = AsyncMock()
    return client


@pytest.fixture
def agent_config():
    """Create agent configuration"""
    return AgentConfig(temperature=0.7, max_tokens=1500)


@pytest.fixture
def coordinator_agent(mock_vllm_client, agent_config):
    """Create coordinator agent instance"""
    return CoordinatorAgent(mock_vllm_client, agent_config)


@pytest.fixture
def sample_state():
    """Create a sample agent state"""
    state = create_initial_state()
    
    # Add a user message
    user_message: Message = {
        "role": "user",
        "content": "我想学习 Python 数据分析",
        "timestamp": datetime.now(),
        "agent": None,
    }
    state["messages"].append(user_message)
    
    # Set user profile
    state["user_profile"]["background"] = "软件工程师"
    state["user_profile"]["skill_level"] = "intermediate"
    state["user_profile"]["learning_goals"] = ["Python 数据分析", "机器学习"]
    
    return state


def test_coordinator_initialization(coordinator_agent):
    """Test coordinator agent initialization"""
    assert coordinator_agent.role == "coordinator"
    assert "intent_recognition" in coordinator_agent.capabilities
    assert "task_routing" in coordinator_agent.capabilities
    assert "conversation_management" in coordinator_agent.capabilities


def test_format_conversation_history(coordinator_agent, sample_state):
    """Test conversation history formatting"""
    history = coordinator_agent._format_conversation_history(sample_state["messages"])
    
    assert "用户: 我想学习 Python 数据分析" in history


def test_extract_user_input(coordinator_agent, sample_state):
    """Test user input extraction"""
    user_input = coordinator_agent._extract_user_input(sample_state["messages"])
    
    assert user_input == "我想学习 Python 数据分析"


def test_extract_user_input_no_messages(coordinator_agent):
    """Test user input extraction with no messages"""
    user_input = coordinator_agent._extract_user_input([])
    
    assert user_input == "（无用户输入）"


def test_build_prompt(coordinator_agent, sample_state):
    """Test prompt building"""
    prompt = coordinator_agent._build_prompt(sample_state)
    
    assert "你是一个教育辅导系统的协调器" in prompt
    assert "我想学习 Python 数据分析" in prompt
    assert "软件工程师" in prompt
    assert "intermediate" in prompt
    assert "Python 数据分析" in prompt


def test_parse_decision_valid_json(coordinator_agent):
    """Test parsing valid JSON decision"""
    response = """
    {
        "next_agent": "course_advisor",
        "current_task": "推荐 Python 数据分析课程",
        "requires_human_input": false,
        "response": "好的，我来为您推荐一些课程。"
    }
    """
    
    decision = coordinator_agent._parse_decision(response)
    
    assert decision["next_agent"] == "course_advisor"
    assert decision["current_task"] == "推荐 Python 数据分析课程"
    assert decision["requires_human_input"] is False
    assert decision["response"] == "好的，我来为您推荐一些课程。"


def test_parse_decision_with_extra_text(coordinator_agent):
    """Test parsing JSON with extra text"""
    response = """
    好的，让我分析一下。
    {
        "next_agent": "learning_planner",
        "current_task": "制定学习计划"
    }
    这是我的决策。
    """
    
    decision = coordinator_agent._parse_decision(response)
    
    assert decision["next_agent"] == "learning_planner"
    assert decision["current_task"] == "制定学习计划"


def test_parse_decision_invalid_agent(coordinator_agent):
    """Test parsing with invalid agent name"""
    response = """
    {
        "next_agent": "invalid_agent",
        "current_task": "测试任务"
    }
    """
    
    decision = coordinator_agent._parse_decision(response)
    
    # Should default to human_input for invalid agent
    assert decision["next_agent"] == "human_input"
    assert decision["requires_human_input"] is True


def test_parse_decision_missing_json(coordinator_agent):
    """Test parsing response without JSON"""
    response = "这是一个没有 JSON 的响应"
    
    with pytest.raises(ValueError, match="No JSON found"):
        coordinator_agent._parse_decision(response)


def test_parse_decision_invalid_json(coordinator_agent):
    """Test parsing invalid JSON"""
    response = "{ invalid json }"
    
    with pytest.raises(ValueError, match="Invalid JSON"):
        coordinator_agent._parse_decision(response)


def test_parse_decision_missing_required_field(coordinator_agent):
    """Test parsing JSON missing required fields"""
    response = """
    {
        "next_agent": "course_advisor"
    }
    """
    
    with pytest.raises(ValueError, match="Missing required field"):
        coordinator_agent._parse_decision(response)


@pytest.mark.asyncio
async def test_analyze_and_route_success(coordinator_agent, mock_vllm_client, sample_state):
    """Test successful intent analysis and routing"""
    # Mock LLM response
    mock_vllm_client.generate.return_value = """
    {
        "next_agent": "course_advisor",
        "current_task": "推荐 Python 数据分析课程",
        "requires_human_input": false,
        "response": "好的，我来为您推荐一些课程。"
    }
    """
    
    decision = await coordinator_agent.analyze_and_route(sample_state)
    
    assert decision["next_agent"] == "course_advisor"
    assert decision["current_task"] == "推荐 Python 数据分析课程"
    assert decision["requires_human_input"] is False
    assert decision["response"] == "好的，我来为您推荐一些课程。"
    
    # Verify LLM was called
    mock_vllm_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_and_route_parse_error(coordinator_agent, mock_vllm_client, sample_state):
    """Test handling of parse errors"""
    # Mock LLM response with invalid JSON
    mock_vllm_client.generate.return_value = "Invalid response without JSON"
    
    decision = await coordinator_agent.analyze_and_route(sample_state)
    
    # Should return safe default decision
    assert decision["next_agent"] == "human_input"
    assert decision["requires_human_input"] is True
    assert "不太确定" in decision["response"]


@pytest.mark.asyncio
async def test_analyze_and_route_llm_error(coordinator_agent, mock_vllm_client, sample_state):
    """Test handling of LLM errors"""
    from src.llm.vllm_client import VLLMConnectionError
    
    # Mock LLM error
    mock_vllm_client.generate.side_effect = VLLMConnectionError("Connection failed")
    
    with pytest.raises(VLLMConnectionError):
        await coordinator_agent.analyze_and_route(sample_state)


def test_get_capabilities(coordinator_agent):
    """Test getting agent capabilities"""
    capabilities = coordinator_agent.get_capabilities()
    
    assert "intent_recognition" in capabilities
    assert "task_routing" in capabilities
    assert "conversation_management" in capabilities


def test_get_role(coordinator_agent):
    """Test getting agent role"""
    role = coordinator_agent.get_role()
    
    assert role == "coordinator"
