"""Example demonstrating tool usage"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import Config, VLLMConfig, MCPConfig, WebSearchConfig
from src.tools import (
    create_mcp_playwright_client,
    create_web_search_client,
    create_tool_manager,
)


def example_mcp_playwright():
    """Example: Using MCP Playwright client directly"""
    print("\n=== MCP Playwright Example ===\n")
    
    # Create configuration
    config = MCPConfig(
        playwright_enabled=True,
        geektime_url="https://time.geekbang.org/",
        browser_headless=True,
    )
    
    # Create client
    client = create_mcp_playwright_client(config)
    
    # Search for courses
    print("Searching for Python courses...")
    courses = client.search_geektime_courses("Python")
    
    print(f"Found {len(courses)} courses:\n")
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course['title']}")
        print(f"   URL: {course['url']}")
        print(f"   Difficulty: {course['difficulty']}")
        print(f"   Description: {course['description'][:80]}...")
        print()
    
    # Get course details
    if courses:
        print(f"\nGetting details for: {courses[0]['title']}")
        details = client.get_course_details(courses[0]['url'])
        print(f"Duration: {details.get('duration', 'N/A')}")
        print(f"Rating: {details.get('rating', 'N/A')}")


def example_web_search():
    """Example: Using web search client directly"""
    print("\n=== Web Search Example ===\n")
    
    # Create configuration
    config = WebSearchConfig(
        enabled=True,
        provider="duckduckgo",
        max_results=5,
    )
    
    # Create client
    client = create_web_search_client(config)
    
    # Search for learning resources
    print("Searching for Python learning resources...")
    results = client.search_learning_resources("Python", skill_level="beginner")
    
    print(f"Found {len(results)} resources:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Source: {result.source}")
        print(f"   Snippet: {result.snippet[:80]}...")
        print()
    
    # Search for best practices
    print("\nSearching for Python best practices...")
    practices = client.search_best_practices("Python")
    
    print(f"Found {len(practices)} best practice resources:\n")
    for i, result in enumerate(practices, 1):
        print(f"{i}. {result.title}")
        print(f"   URL: {result.url}")
        print()


def example_tool_manager():
    """Example: Using tool manager with fallback"""
    print("\n=== Tool Manager Example ===\n")
    
    # Create complete configuration
    config = Config(
        vllm=VLLMConfig(
            api_base="http://localhost:8000/v1",
            model_name="test-model",
        ),
        mcp=MCPConfig(
            playwright_enabled=True,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
        ),
        web_search=WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        ),
    )
    
    # Create tool manager
    manager = create_tool_manager(config)
    
    # Check tool status
    print("Tool Status:")
    status = manager.get_tool_status()
    for tool, available in status.items():
        print(f"  {tool}: {'✓ Available' if available else '✗ Unavailable'}")
    print()
    
    # Search for courses (with automatic fallback)
    print("Searching for courses (with fallback support)...")
    result = manager.search_courses("Python数据分析", use_fallback=True)
    
    if result.success:
        print(f"✓ Search succeeded using: {result.tool_name}")
        if result.fallback_used:
            print("  (Fallback was used)")
        
        courses = result.data
        print(f"\nFound {len(courses)} courses:\n")
        for i, course in enumerate(courses, 1):
            print(f"{i}. {course['title']}")
            print(f"   Source: {course['source']}")
            print()
    else:
        print(f"✗ Search failed: {result.error}")
    
    # Search for learning resources
    print("\nSearching for learning resources...")
    result = manager.search_learning_resources("机器学习", skill_level="intermediate")
    
    if result.success:
        print(f"✓ Search succeeded")
        resources = result.data
        print(f"\nFound {len(resources)} resources:\n")
        for i, resource in enumerate(resources, 1):
            print(f"{i}. {resource.title}")
            print(f"   URL: {resource.url}")
            print()
    else:
        print(f"✗ Search failed: {result.error}")


def example_error_handling():
    """Example: Error handling and fallback"""
    print("\n=== Error Handling Example ===\n")
    
    # Create configuration with MCP disabled
    config = Config(
        vllm=VLLMConfig(
            api_base="http://localhost:8000/v1",
            model_name="test-model",
        ),
        mcp=MCPConfig(
            playwright_enabled=False,  # Disabled
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
        ),
        web_search=WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        ),
    )
    
    manager = create_tool_manager(config)
    
    print("MCP Playwright is disabled. Testing fallback...")
    result = manager.search_courses("Python", use_fallback=True)
    
    if result.success:
        print(f"✓ Fallback succeeded using: {result.tool_name}")
        print(f"  Found {len(result.data)} courses")
    else:
        print(f"✗ Both primary and fallback failed")
    
    # Test without fallback
    print("\nTesting without fallback...")
    result = manager.search_courses("Python", use_fallback=False)
    
    if result.success:
        print(f"✓ Search succeeded")
    else:
        print(f"✗ Search failed (as expected): {result.error}")


def main():
    """Run all examples"""
    print("=" * 60)
    print("Tool Integration Examples")
    print("=" * 60)
    
    try:
        example_mcp_playwright()
        example_web_search()
        example_tool_manager()
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
