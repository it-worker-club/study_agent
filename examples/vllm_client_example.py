"""Example usage of vLLM client"""

import asyncio
from src.utils.config import get_config
from src.llm import create_vllm_client, VLLMConnectionError, VLLMTimeoutError


async def main():
    """Demonstrate vLLM client usage"""
    
    # Load configuration
    try:
        config = get_config()
        print(f"Loaded configuration from config file")
        print(f"vLLM endpoint: {config.vllm.api_base}")
        print(f"Model: {config.vllm.model_name}")
        print()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    # Create vLLM client
    client = create_vllm_client(config.vllm)
    
    try:
        # Check service health
        print("Checking vLLM service health...")
        is_healthy = await client.check_health()
        
        if not is_healthy:
            print("❌ vLLM service is not available")
            return
        
        print("✅ vLLM service is healthy")
        print()
        
        # Example 1: Simple text generation
        print("=" * 60)
        print("Example 1: Simple text generation")
        print("=" * 60)
        
        prompt = "请用一句话介绍什么是人工智能。"
        print(f"Prompt: {prompt}")
        print()
        
        response = await client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=100,
        )
        
        print(f"Response: {response}")
        print()
        
        # Example 2: Multi-turn conversation
        print("=" * 60)
        print("Example 2: Multi-turn conversation")
        print("=" * 60)
        
        messages = [
            {"role": "user", "content": "你好，我想学习 Python 编程。"},
            {"role": "assistant", "content": "你好！很高兴帮助你学习 Python。你有编程基础吗？"},
            {"role": "user", "content": "我是完全的初学者。"},
        ]
        
        print("Conversation history:")
        for msg in messages:
            print(f"  {msg['role']}: {msg['content']}")
        print()
        
        response = await client.generate_with_messages(
            messages=messages,
            temperature=0.7,
            max_tokens=200,
        )
        
        print(f"Assistant: {response}")
        print()
        
        # Example 3: Streaming generation
        print("=" * 60)
        print("Example 3: Streaming generation")
        print("=" * 60)
        
        prompt = "请列举学习 Python 的三个重要步骤。"
        print(f"Prompt: {prompt}")
        print()
        print("Streaming response:")
        
        async for chunk in client.generate_stream(
            prompt=prompt,
            temperature=0.7,
            max_tokens=200,
        ):
            print(chunk, end="", flush=True)
        
        print()
        print()
        
    except VLLMConnectionError as e:
        print(f"❌ Connection error: {e}")
    except VLLMTimeoutError as e:
        print(f"❌ Timeout error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Clean up
        await client.close()
        print("Client closed")


if __name__ == "__main__":
    asyncio.run(main())
