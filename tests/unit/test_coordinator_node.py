"""Unit tests for the coordinator node function"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.graph.nodes import coordinator_node, initialize_agents
from src.graph.helpers import create_initial_state, add_message
from src.llm.vllm_client import VLLMClient, VLLMConnectionError
from src.utils.config import (
    Config,
    VLLMConfig,
    AgentConfig,
    AgentsConfig,
    MCPConfig,
    WebSearchConfig,
    SystemConfig,
)


@pytest.fixture
def mock_vllm_client():
    """Create a mock vLLM client"""
    client = MagicMock(spec=VLLMClient)
    client.generate = AsyncMock()
    return client


@pytest.fixture
def test_config():
    """Create test configuration"""
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
        ),
        web_search=WebSearchConfig(),
        system=SystemConfig(),
        agents=AgentsConfig(
            coordinator=AgentConfig(temperature=0.7, max_tokens=1500),
        ),
    )


@pytest.fixture
def sample_state():
    """Create a sample agent state"""
    state = create_initial_state()
    
    # Add a user message
    state = add_message(
        state,
        role="user",
        content="我想学习 Python 数据分析",
        agent=None,
    )
    
    # Set user profile
    state["user_profile"]["background"] = "软件工程师"
    state["user_profile"]["skill_level"] = "intermediate"
    state["user_profile"]["learning_goals"] = ["Python 数据分析"]
    
    return state


def test_coordinator_node_success(mock_vllm_client, test_config, sample_state):
    """Test successful coordinator node execution"""
    # Initialize agents
    initialize_agents(test_config, mock_vllm_client)
    
    # Mock LLM response
    mock_vllm_client.generate.return_value = """
    {
        "next_agent": "course_advisor",
        "current_task": "推荐 Python 数据分析课程",
        "requires_human_input": false,
        "response": "好的，我来为您推荐一些课程。"
    }
    """
    
    initial_message_count = len(sample_state["messages"])
    
    # Execute coordinator node
    result_state = coordinator_node(sample_state)
    
    # Verify routing decision
    assert result_state["next_agent"] == "course_advisor"
    assert result_state["current_task"] == "推荐 Python 数据分析课程"
    assert result_state["requires_human_input"] is False
    
    # Verify response message was added (may include transition message)
    assert len(result_state["messages"]) >= initial_message_count + 1
    
    # Find the coordinator's response message
    coordinator_messages = [
        msg for msg in result_state["messages"]
        if msg.get("agent") == "coordinator"
    ]
    assert len(coordinator_messages) > 0
    assert "推荐" in coordinator_messages[0]["content"]
    
    # Verify loop count was incremented
    assert result_state["loop_count"] == 1


def test_coordinator_node_learning_planner(mock_vllm_client, test_config, sample_state):
    """Test coordinator routing to learning planner"""
    # Initialize agents
    initialize_agents(test_config, mock_vllm_client)
    
    # Mock LLM response for learning plan request
    mock_vllm_client.generate.return_value = """
    {
        "next_agent": "learning_planner",
        "current_task": "制定学习计划",
        "requires_human_input": false,
        "response": "我来帮您制定一个学习计划。"
    }
    """
    
    # Execute coordinator node
    result_state = coordinator_node(sample_state)
    
    # Verify routing to learning planner
    assert result_state["next_agent"] == "learning_planner"
    assert result_state["current_task"] == "制定学习计划"


def test_coordinator_node_human_input(mock_vllm_client, test_config, sample_state):
    """Test coordinator requesting human input"""
    # Initialize agents
    initialize_agents(test_config, mock_vllm_client)
    
    # Mock LLM response requesting clarification
    mock_vllm_client.generate.return_value = """
    {
        "next_agent": "human_input",
        "current_task": "需要用户澄清",
        "requires_human_input": true,
        "response": "能否请您详细说明一下您的需求？"
    }
    """
    
    # Execute coordinator node
    result_state = coordinator_node(sample_state)
    
    # Verify human input request
    assert result_state["next_agent"] == "human_input"
    assert result_state["requires_human_input"] is True


def test_coordinator_node_end_conversation(mock_vllm_client, test_config, sample_state):
    """Test coordinator ending conversation"""
    # Initialize agents
    initialize_agents(test_config, mock_vllm_client)
    
    # Mock LLM response for ending conversation
    mock_vllm_client.generate.return_value = """
    {
        "next_agent": "end",
        "current_task": "结束对话",
        "requires_human_input": false,
        "response": "感谢您的使用！"
    }
    """
    
    # Execute coordinator node
    result_state = coordinator_node(sample_state)
    
    # Verify conversation end
    assert result_state["next_agent"] == "end"


def test_coordinator_node_loop_limit(mock_vllm_client, test_config, sample_state):
    """Test coordinator loop count limit"""
    # Initialize agents
    initialize_agents(test_config, mock_vllm_client)
    
    # Set loop count to exceed limit
    sample_state["loop_count"] = 10
    
    # Execute coordinator node
    result_state = coordinator_node(sample_state)
    
    # Verify loop limit handling
    assert result_state["next_agent"] == "end"
    assert result_state["is_complete"] is True
    
    # Verify error message was added
    last_message = result_state["messages"][-1]
    assert "最大轮次限制" in last_message["content"]


def test_coordinator_node_llm_error(mock_vllm_client, test_config, sample_state):
    """Test coordinator handling LLM errors"""
    # Initialize agents
    initialize_agents(test_config, mock_vllm_client)
    
    # Mock LLM error
    mock_vllm_client.generate.side_effect = VLLMConnectionError("Connection failed")
    
    # Execute coordinator node
    result_state = coordinator_node(sample_state)
    
    # Verify error handling
    assert result_state["requires_human_input"] is True
    
    # Verify error message was added
    last_message = result_state["messages"][-1]
    assert last_message["role"] == "assistant"
    assert "AI 服务" in last_message["content"] or "不可用" in last_message["content"]


def test_coordinator_node_parse_error(mock_vllm_client, test_config, sample_state):
    """Test coordinator handling parse errors"""
    # Initialize agents
    initialize_agents(test_config, mock_vllm_client)
    
    # Mock invalid LLM response
    mock_vllm_client.generate.return_value = "Invalid response without JSON"
    
    # Execute coordinator node
    result_state = coordinator_node(sample_state)
    
    # Verify fallback to human input
    assert result_state["requires_human_input"] is True
    
    # Verify clarification message was added
    last_message = result_state["messages"][-1]
    assert "不太确定" in last_message["content"] or "澄清" in last_message["content"]


def test_coordinator_node_increments_loop_count(mock_vllm_client, test_config, sample_state):
    """Test that coordinator increments loop count"""
    # Initialize agents
    initialize_agents(test_config, mock_vllm_client)
    
    # Mock LLM response
    mock_vllm_client.generate.return_value = """
    {
        "next_agent": "course_advisor",
        "current_task": "测试任务"
    }
    """
    
    initial_loop_count = sample_state["loop_count"]
    
    # Execute coordinator node
    result_state = coordinator_node(sample_state)
    
    # Verify loop count incremented
    assert result_state["loop_count"] == initial_loop_count + 1
