# vLLM Service Integration

## Overview

This document describes the vLLM service integration implemented for the Education Tutoring System. The integration provides a robust, production-ready client for interacting with vLLM servers using the OpenAI-compatible API.

## Components

### 1. VLLMClient (`src/llm/vllm_client.py`)

The main client class for interacting with vLLM services.

**Features:**
- OpenAI-compatible API support
- Automatic retry with exponential backoff (using tenacity)
- Comprehensive error handling and classification
- Support for streaming responses
- Health check functionality
- Connection pooling and timeout management

**Key Methods:**
- `generate(prompt, ...)`: Generate text from a single prompt
- `generate_with_messages(messages, ...)`: Generate text from conversation history
- `generate_stream(prompt, ...)`: Generate text with streaming response
- `check_health()`: Check if vLLM service is available

**Error Types:**
- `VLLMClientError`: Base exception for all vLLM errors
- `VLLMConnectionError`: Connection failures (retriable)
- `VLLMTimeoutError`: Request timeouts (retriable)
- `VLLMAPIError`: API errors (non-retriable)

### 2. Error Handler (`src/utils/error_handler.py`)

Unified error handling system that integrates with the agent state management.

**Features:**
- Consistent error handling across all components
- User-friendly error messages in Chinese
- State preservation during error recovery
- Error classification and recovery strategies
- Detailed logging for debugging

**Key Methods:**
- `handle_llm_error()`: Handle LLM service errors
- `handle_tool_error()`: Handle tool execution errors
- `handle_state_error()`: Handle state management errors
- `handle_routing_error()`: Handle routing decision errors
- `is_recoverable_error()`: Determine if error is recoverable
- `should_retry()`: Determine if operation should be retried

## Configuration

The vLLM client is configured through `config/system_config.yaml`:

```yaml
vllm:
  api_base: "http://your-vllm-server:8000/v1"
  api_key: "your-api-key"  # or null if not required
  model_name: "your-model-name"
  temperature: 0.7
  max_tokens: 2000
  timeout: 60
```

## Usage Examples

### Basic Text Generation

```python
from src.utils.config import get_config
from src.llm import create_vllm_client

# Load configuration
config = get_config()

# Create client
client = create_vllm_client(config.vllm)

# Generate text
response = await client.generate(
    prompt="请介绍一下 Python 编程语言。",
    temperature=0.7,
    max_tokens=200,
)

print(response)

# Clean up
await client.close()
```

### Multi-turn Conversation

```python
messages = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
    {"role": "user", "content": "我想学习编程"},
]

response = await client.generate_with_messages(
    messages=messages,
    temperature=0.7,
    max_tokens=200,
)
```

### Streaming Response

```python
async for chunk in client.generate_stream(
    prompt="请列举学习 Python 的步骤。",
    temperature=0.7,
    max_tokens=200,
):
    print(chunk, end="", flush=True)
```

### Error Handling

```python
from src.llm import VLLMConnectionError, VLLMTimeoutError, VLLMAPIError

try:
    response = await client.generate(prompt="Hello")
except VLLMConnectionError as e:
    print(f"Connection failed: {e}")
    # Retry or use fallback
except VLLMTimeoutError as e:
    print(f"Request timed out: {e}")
    # Retry or use fallback
except VLLMAPIError as e:
    print(f"API error: {e}")
    # Log and notify user
```

### Integration with Agent State

```python
from src.utils.error_handler import ErrorHandler

try:
    response = await client.generate(prompt=user_input)
    # Update state with response
except Exception as e:
    # Handle error and update state
    state = ErrorHandler.handle_llm_error(e, state)
```

## Retry Strategy

The client implements automatic retry with exponential backoff for recoverable errors:

- **Retriable errors**: Connection errors, timeout errors
- **Max attempts**: 3
- **Wait strategy**: Exponential backoff (min=2s, max=10s)
- **Non-retriable errors**: API errors (invalid requests, etc.)

## Health Checks

The client provides a health check method to verify service availability:

```python
is_healthy = await client.check_health()
if not is_healthy:
    # Handle service unavailability
    state = handle_vllm_service_failure(state)
```

## Testing

Comprehensive unit tests are provided in:
- `tests/unit/test_vllm_client.py`: Tests for VLLMClient
- `tests/unit/test_error_handler.py`: Tests for ErrorHandler

Run tests:
```bash
uv run pytest tests/unit/test_vllm_client.py tests/unit/test_error_handler.py -v
```

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 11.1**: Connects to external vLLM service via API endpoint ✅
- **Requirement 11.2**: Configures LLM parameters for different agent roles ✅
- **Requirement 11.3**: Detects vLLM service failures and notifies users ✅
- **Requirement 11.4**: Supports configurable API endpoint and credentials ✅
- **Requirement 11.5**: Handles LLM response streaming ✅

## Future Enhancements

Potential improvements for future iterations:

1. **Connection pooling**: Implement connection pool for better performance
2. **Metrics collection**: Add detailed metrics for monitoring
3. **Caching**: Implement response caching for repeated queries
4. **Rate limiting**: Add client-side rate limiting
5. **Batch processing**: Support batch generation requests
6. **Model switching**: Support dynamic model selection

## Troubleshooting

### Connection Issues

If you encounter connection errors:
1. Verify vLLM server is running and accessible
2. Check network connectivity
3. Verify API endpoint in configuration
4. Check firewall settings

### Timeout Issues

If requests timeout frequently:
1. Increase timeout value in configuration
2. Check vLLM server load
3. Consider using streaming for long responses
4. Verify network latency

### API Errors

If you encounter API errors:
1. Verify API key is correct (if required)
2. Check model name in configuration
3. Verify request parameters are valid
4. Check vLLM server logs for details

## References

- [vLLM Documentation](https://docs.vllm.ai/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Tenacity Documentation](https://tenacity.readthedocs.io/)

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
