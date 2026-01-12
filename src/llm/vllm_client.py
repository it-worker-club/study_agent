"""vLLM client for LLM inference using OpenAI-compatible API"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from openai import AsyncOpenAI, OpenAIError, APITimeoutError, APIConnectionError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..utils.config import VLLMConfig
from ..utils.logger import get_logger


logger = get_logger(__name__)


class VLLMClientError(Exception):
    """Base exception for vLLM client errors"""
    pass


class VLLMConnectionError(VLLMClientError):
    """Exception raised when connection to vLLM service fails"""
    pass


class VLLMAPIError(VLLMClientError):
    """Exception raised when vLLM API returns an error"""
    pass


class VLLMTimeoutError(VLLMClientError):
    """Exception raised when vLLM request times out"""
    pass


class VLLMClient:
    """
    Client for interacting with vLLM service using OpenAI-compatible API.
    
    This client provides:
    - Automatic retry with exponential backoff
    - Support for streaming responses
    - Comprehensive error handling
    - Connection pooling and timeout management
    """
    
    def __init__(self, config: VLLMConfig):
        """
        Initialize vLLM client.
        
        Args:
            config: vLLM configuration object
        """
        self.config = config
        
        # Initialize OpenAI client with vLLM endpoint
        self.client = AsyncOpenAI(
            api_key=config.api_key or "EMPTY",  # vLLM may not require API key
            base_url=config.api_base,
            timeout=config.timeout,
        )
        
        logger.info(
            f"Initialized vLLM client: endpoint={config.api_base}, "
            f"model={config.model_name}"
        )
    
    @retry(
        retry=retry_if_exception_type((VLLMConnectionError, VLLMTimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text completion from prompt.
        
        Args:
            prompt: Input prompt text
            temperature: Sampling temperature (overrides config default)
            max_tokens: Maximum tokens to generate (overrides config default)
            stop: Stop sequences
            **kwargs: Additional parameters for the API
        
        Returns:
            Generated text completion
        
        Raises:
            VLLMConnectionError: If connection to service fails
            VLLMAPIError: If API returns an error
            VLLMTimeoutError: If request times out
        """
        try:
            logger.debug(f"Generating completion for prompt (length={len(prompt)})")
            
            # Use config defaults if not specified
            temperature = temperature if temperature is not None else self.config.temperature
            max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
            
            # Call vLLM API
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs,
            )
            
            # Extract generated text
            if not response.choices:
                raise VLLMAPIError("No completion choices returned from API")
            
            generated_text = response.choices[0].message.content
            
            if generated_text is None:
                raise VLLMAPIError("Generated text is None")
            
            logger.debug(
                f"Generated completion: length={len(generated_text)}, "
                f"tokens={response.usage.completion_tokens if response.usage else 'unknown'}"
            )
            
            return generated_text
        
        except VLLMClientError:
            # Re-raise our own exceptions (VLLMAPIError, etc.)
            raise
        
        except APITimeoutError as e:
            error_msg = str(e)
            logger.error(f"vLLM timeout error: {error_msg}")
            raise VLLMTimeoutError(f"Request timed out: {error_msg}") from e
        
        except APIConnectionError as e:
            error_msg = str(e)
            logger.error(f"vLLM connection error: {error_msg}")
            raise VLLMConnectionError(f"Connection failed: {error_msg}") from e
        
        except OpenAIError as e:
            error_msg = str(e)
            logger.error(f"vLLM API error: {error_msg}")
            raise VLLMAPIError(f"API error: {error_msg}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error in vLLM client: {e}")
            raise VLLMClientError(f"Unexpected error: {e}") from e
    
    @retry(
        retry=retry_if_exception_type((VLLMConnectionError, VLLMTimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text completion from conversation messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (overrides config default)
            max_tokens: Maximum tokens to generate (overrides config default)
            stop: Stop sequences
            **kwargs: Additional parameters for the API
        
        Returns:
            Generated text completion
        
        Raises:
            VLLMConnectionError: If connection to service fails
            VLLMAPIError: If API returns an error
            VLLMTimeoutError: If request times out
        """
        try:
            logger.debug(f"Generating completion for {len(messages)} messages")
            
            # Use config defaults if not specified
            temperature = temperature if temperature is not None else self.config.temperature
            max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
            
            # Call vLLM API
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs,
            )
            
            # Extract generated text
            if not response.choices:
                raise VLLMAPIError("No completion choices returned from API")
            
            generated_text = response.choices[0].message.content
            
            if generated_text is None:
                raise VLLMAPIError("Generated text is None")
            
            logger.debug(
                f"Generated completion: length={len(generated_text)}, "
                f"tokens={response.usage.completion_tokens if response.usage else 'unknown'}"
            )
            
            return generated_text
        
        except VLLMClientError:
            # Re-raise our own exceptions
            raise
        
        except APITimeoutError as e:
            error_msg = str(e)
            logger.error(f"vLLM timeout error: {error_msg}")
            raise VLLMTimeoutError(f"Request timed out: {error_msg}") from e
        
        except APIConnectionError as e:
            error_msg = str(e)
            logger.error(f"vLLM connection error: {error_msg}")
            raise VLLMConnectionError(f"Connection failed: {error_msg}") from e
        
        except OpenAIError as e:
            error_msg = str(e)
            logger.error(f"vLLM API error: {error_msg}")
            raise VLLMAPIError(f"API error: {error_msg}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error in vLLM client: {e}")
            raise VLLMClientError(f"Unexpected error: {e}") from e
    
    @retry(
        retry=retry_if_exception_type((VLLMConnectionError, VLLMTimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_stream(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Generate text completion with streaming response.
        
        Args:
            prompt: Input prompt text
            temperature: Sampling temperature (overrides config default)
            max_tokens: Maximum tokens to generate (overrides config default)
            stop: Stop sequences
            **kwargs: Additional parameters for the API
        
        Yields:
            Text chunks as they are generated
        
        Raises:
            VLLMConnectionError: If connection to service fails
            VLLMAPIError: If API returns an error
            VLLMTimeoutError: If request times out
        """
        try:
            logger.debug(f"Starting streaming generation for prompt (length={len(prompt)})")
            
            # Use config defaults if not specified
            temperature = temperature if temperature is not None else self.config.temperature
            max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
            
            # Call vLLM API with streaming
            stream = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                stream=True,
                **kwargs,
            )
            
            # Yield chunks as they arrive
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
            logger.debug("Streaming generation completed")
        
        except VLLMClientError:
            # Re-raise our own exceptions
            raise
        
        except APITimeoutError as e:
            error_msg = str(e)
            logger.error(f"vLLM streaming timeout error: {error_msg}")
            raise VLLMTimeoutError(f"Request timed out: {error_msg}") from e
        
        except APIConnectionError as e:
            error_msg = str(e)
            logger.error(f"vLLM streaming connection error: {error_msg}")
            raise VLLMConnectionError(f"Connection failed: {error_msg}") from e
        
        except OpenAIError as e:
            error_msg = str(e)
            logger.error(f"vLLM streaming API error: {error_msg}")
            raise VLLMAPIError(f"API error: {error_msg}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error in vLLM streaming: {e}")
            raise VLLMClientError(f"Unexpected error: {e}") from e
    
    async def check_health(self) -> bool:
        """
        Check if vLLM service is available and healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Try a simple generation to check health
            await self.generate(
                prompt="Hello",
                max_tokens=5,
                temperature=0.0,
            )
            logger.info("vLLM service health check: OK")
            return True
        
        except Exception as e:
            logger.error(f"vLLM service health check failed: {e}")
            return False
    
    async def close(self):
        """Close the client and cleanup resources."""
        await self.client.close()
        logger.info("vLLM client closed")


def create_vllm_client(config: VLLMConfig) -> VLLMClient:
    """
    Factory function to create a vLLM client.
    
    Args:
        config: vLLM configuration
    
    Returns:
        Initialized vLLM client
    """
    return VLLMClient(config)
