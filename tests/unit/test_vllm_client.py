"""Unit tests for vLLM client"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.vllm_client import (
    VLLMClient,
    VLLMClientError,
    VLLMConnectionError,
    VLLMAPIError,
    VLLMTimeoutError,
    create_vllm_client,
)
from src.utils.config import VLLMConfig


@pytest.fixture
def vllm_config():
    """Create a test vLLM configuration"""
    return VLLMConfig(
        api_base="http://test-server:8000/v1",
        api_key="test-key",
        model_name="test-model",
        temperature=0.7,
        max_tokens=100,
        timeout=30,
    )


@pytest.fixture
def vllm_client(vllm_config):
    """Create a vLLM client for testing"""
    return VLLMClient(vllm_config)


def test_vllm_client_initialization(vllm_config):
    """Test vLLM client initialization"""
    client = VLLMClient(vllm_config)
    
    assert client.config == vllm_config
    assert client.client is not None


def test_create_vllm_client(vllm_config):
    """Test factory function for creating vLLM client"""
    client = create_vllm_client(vllm_config)
    
    assert isinstance(client, VLLMClient)
    assert client.config == vllm_config


@pytest.mark.asyncio
async def test_generate_success(vllm_client):
    """Test successful text generation"""
    # Mock the OpenAI client response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Generated text"
    mock_response.usage.completion_tokens = 10
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ):
        result = await vllm_client.generate("Test prompt")
        
        assert result == "Generated text"


@pytest.mark.asyncio
async def test_generate_with_custom_params(vllm_client):
    """Test generation with custom parameters"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Custom response"
    mock_response.usage = None
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ) as mock_create:
        result = await vllm_client.generate(
            "Test prompt",
            temperature=0.5,
            max_tokens=50,
            stop=["END"]
        )
        
        assert result == "Custom response"
        
        # Verify parameters were passed correctly
        call_args = mock_create.call_args
        assert call_args.kwargs['temperature'] == 0.5
        assert call_args.kwargs['max_tokens'] == 50
        assert call_args.kwargs['stop'] == ["END"]


@pytest.mark.asyncio
async def test_generate_with_messages(vllm_client):
    """Test generation with conversation messages"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response to messages"
    mock_response.usage = None
    
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ):
        result = await vllm_client.generate_with_messages(messages)
        
        assert result == "Response to messages"


@pytest.mark.asyncio
async def test_generate_no_choices_error(vllm_client):
    """Test error when API returns no choices"""
    mock_response = MagicMock()
    mock_response.choices = []
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ):
        with pytest.raises(VLLMAPIError, match="No completion choices"):
            await vllm_client.generate("Test prompt")


@pytest.mark.asyncio
async def test_generate_none_content_error(vllm_client):
    """Test error when generated content is None"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ):
        with pytest.raises(VLLMAPIError, match="Generated text is None"):
            await vllm_client.generate("Test prompt")


@pytest.mark.asyncio
async def test_generate_connection_error(vllm_client):
    """Test handling of connection errors"""
    from openai import APIConnectionError
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        side_effect=APIConnectionError(request=MagicMock())
    ):
        with pytest.raises(VLLMConnectionError):
            await vllm_client.generate("Test prompt")


@pytest.mark.asyncio
async def test_generate_timeout_error(vllm_client):
    """Test handling of timeout errors"""
    from openai import APITimeoutError
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        side_effect=APITimeoutError(request=MagicMock())
    ):
        with pytest.raises(VLLMTimeoutError):
            await vllm_client.generate("Test prompt")


@pytest.mark.asyncio
async def test_check_health_success(vllm_client):
    """Test health check when service is available"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "OK"
    mock_response.usage = None
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ):
        result = await vllm_client.check_health()
        
        assert result is True


@pytest.mark.asyncio
async def test_check_health_failure(vllm_client):
    """Test health check when service is unavailable"""
    from openai import APIConnectionError
    
    with patch.object(
        vllm_client.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        side_effect=APIConnectionError(request=MagicMock())
    ):
        result = await vllm_client.check_health()
        
        assert result is False


@pytest.mark.asyncio
async def test_close_client(vllm_client):
    """Test closing the client"""
    with patch.object(vllm_client.client, 'close', new_callable=AsyncMock) as mock_close:
        await vllm_client.close()
        
        mock_close.assert_called_once()
