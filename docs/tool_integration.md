# Tool Integration Documentation

## Overview

The education tutoring system integrates two external tools to provide comprehensive course recommendations and learning resources:

1. **MCP Playwright**: Accesses GeekTime (极客时间) website to search and retrieve course information
2. **Web Search**: Searches the web for supplementary learning resources, tutorials, and best practices

Both tools are managed by a unified `ToolManager` that provides:
- Automatic retry on transient failures
- Fallback mechanisms when primary tools fail
- Error handling and graceful degradation
- Consistent interface for all tool operations

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Tool Manager                         │
│  - Unified interface                                     │
│  - Error handling                                        │
│  - Fallback logic                                        │
└─────────────────┬───────────────────────┬───────────────┘
                  │                       │
        ┌─────────▼─────────┐   ┌────────▼──────────┐
        │  MCP Playwright   │   │   Web Search      │
        │  - GeekTime       │   │   - DuckDuckGo    │
        │  - Course search  │   │   - Resources     │
        │  - Course details │   │   - Tutorials     │
        └───────────────────┘   └───────────────────┘
```

## Components

### 1. MCP Playwright Client

**Purpose**: Access GeekTime website to search and retrieve course information.

**Key Features**:
- Search courses by keyword
- Retrieve detailed course information
- Configurable browser options (headless mode, timeout)
- Automatic retry on failures

**Usage**:
```python
from src.tools import create_mcp_playwright_client
from src.utils.config import MCPConfig

config = MCPConfig(
    playwright_enabled=True,
    geektime_url="https://time.geekbang.org/",
    browser_headless=True,
)

client = create_mcp_playwright_client(config)

# Search for courses
courses = client.search_geektime_courses("Python")

# Get course details
details = client.get_course_details(course_url)
```

**Configuration**:
```yaml
mcp:
  playwright_enabled: true
  geektime_url: "https://time.geekbang.org/"
  browser_headless: true
  browser_timeout: 30000  # milliseconds
```

### 2. Web Search Client

**Purpose**: Search the web for supplementary learning resources.

**Key Features**:
- General web search
- Specialized learning resource search
- Best practices search
- Tutorial search
- Configurable result limits

**Usage**:
```python
from src.tools import create_web_search_client
from src.utils.config import WebSearchConfig

config = WebSearchConfig(
    enabled=True,
    provider="duckduckgo",
    max_results=5,
)

client = create_web_search_client(config)

# General search
results = client.search("Python教程")

# Learning resources
resources = client.search_learning_resources("Python", skill_level="beginner")

# Best practices
practices = client.search_best_practices("Python")

# Tutorials
tutorials = client.search_tutorials("Python")
```

**Configuration**:
```yaml
web_search:
  enabled: true
  provider: "duckduckgo"
  max_results: 5
```

### 3. Tool Manager

**Purpose**: Unified interface for all tools with error handling and fallback.

**Key Features**:
- Automatic fallback from MCP Playwright to Web Search
- Retry logic with exponential backoff
- Tool availability tracking
- Error reporting and logging
- Graceful degradation

**Usage**:
```python
from src.tools import create_tool_manager
from src.utils.config import Config

config = Config(...)  # Complete system config
manager = create_tool_manager(config)

# Search courses (with automatic fallback)
result = manager.search_courses("Python", use_fallback=True)

if result.success:
    courses = result.data
    print(f"Found {len(courses)} courses")
    if result.fallback_used:
        print("Fallback was used")
else:
    print(f"Search failed: {result.error}")

# Get course details
result = manager.get_course_details(course_url)

# Web search
result = manager.search_web("Python教程")

# Learning resources
result = manager.search_learning_resources("Python", skill_level="beginner")

# Check tool status
status = manager.get_tool_status()
print(f"MCP Playwright: {status['mcp_playwright']}")
print(f"Web Search: {status['web_search']}")
```

## Error Handling

### Error Types

1. **MCPPlaywrightError**: Base exception for MCP Playwright errors
   - `MCPPlaywrightConnectionError`: Connection failures
   - `MCPPlaywrightNavigationError`: Navigation failures

2. **WebSearchError**: Base exception for web search errors
   - `WebSearchConnectionError`: Connection failures
   - `WebSearchAPIError`: API errors

### Retry Strategy

Both tools use automatic retry with exponential backoff:
- Maximum 2 attempts
- Wait time: 1-5 seconds (exponential)
- Only retries on transient errors (connection, timeout)

### Fallback Mechanism

When MCP Playwright fails, the Tool Manager automatically falls back to Web Search:

```
Course Search Request
        ↓
    MCP Playwright
        ↓
    [Failed?]
        ↓
    Web Search (Fallback)
        ↓
    Result or Error
```

### Integration with Error Handler

Tool errors are integrated with the system's unified error handler:

```python
from src.utils.error_handler import ErrorHandler

# Handle tool error in agent state
state = manager.handle_tool_error_in_state(result, state)
```

## Data Models

### CourseInfo

```python
{
    "title": str,           # Course title
    "url": str,             # Course URL
    "description": str,     # Course description
    "difficulty": str,      # beginner/intermediate/advanced
    "duration": str,        # Optional: e.g., "20小时"
    "rating": float,        # Optional: e.g., 4.8
    "source": str,          # "geektime" or "web_search"
}
```

### WebSearchResult

```python
{
    "title": str,           # Result title
    "url": str,             # Result URL
    "snippet": str,         # Result snippet/description
    "source": str,          # Source domain
}
```

### ToolExecutionResult

```python
{
    "success": bool,        # Whether execution succeeded
    "data": Any,            # Result data (courses, search results, etc.)
    "error": Exception,     # Error if failed
    "fallback_used": bool,  # Whether fallback was used
    "tool_name": str,       # Name of the tool used
    "timestamp": datetime,  # Execution timestamp
}
```

## Testing

### Unit Tests

All tools have comprehensive unit tests:

```bash
# Run all tool tests
uv run pytest tests/unit/test_tools.py -v

# Run specific test class
uv run pytest tests/unit/test_tools.py::TestMCPPlaywrightClient -v
uv run pytest tests/unit/test_tools.py::TestWebSearchClient -v
uv run pytest tests/unit/test_tools.py::TestToolManager -v
```

### Example Usage

See `examples/tool_usage_example.py` for complete examples:

```bash
uv run python examples/tool_usage_example.py
```

## Best Practices

1. **Always use Tool Manager**: Use `ToolManager` instead of individual clients for automatic error handling and fallback

2. **Enable fallback**: Set `use_fallback=True` for critical operations to ensure service continuity

3. **Check tool status**: Use `manager.get_tool_status()` to verify tool availability before critical operations

4. **Handle errors gracefully**: Always check `result.success` and handle errors appropriately

5. **Log tool usage**: Tool operations are automatically logged for monitoring and debugging

6. **Configure timeouts**: Adjust browser and API timeouts based on network conditions

7. **Monitor fallback usage**: Track when fallbacks are used to identify primary tool issues

## Future Enhancements

### Planned Features

1. **Real MCP Integration**: Replace simulated MCP calls with actual MCP protocol implementation
2. **Real Web Search API**: Integrate with DuckDuckGo API or other search providers
3. **Caching**: Add result caching to reduce API calls
4. **Rate Limiting**: Implement rate limiting for API calls
5. **Advanced Filtering**: Add filtering by difficulty, rating, duration, etc.
6. **Multi-language Support**: Support multiple languages for search queries
7. **Course Comparison**: Add ability to compare multiple courses
8. **User Reviews**: Fetch and analyze user reviews

### Integration Points

The tool system is designed to integrate with:
- **Course Advisor Agent**: Uses tools to search and recommend courses
- **Learning Planner Agent**: Uses tools to find supplementary resources
- **Memory System**: Caches search results for faster retrieval
- **Error Handler**: Unified error handling across the system

## Troubleshooting

### Common Issues

1. **MCP Playwright not working**
   - Check if `playwright_enabled` is `true` in config
   - Verify browser drivers are installed
   - Check network connectivity to GeekTime

2. **Web Search not working**
   - Check if `enabled` is `true` in config
   - Verify network connectivity
   - Check if search provider is accessible

3. **All tools failing**
   - Check network connectivity
   - Review logs for detailed error messages
   - Verify configuration is correct

### Debug Mode

Enable debug logging to troubleshoot issues:

```yaml
logging:
  level: "DEBUG"
```

### Health Checks

Check tool health programmatically:

```python
status = manager.get_tool_status()
if not status['mcp_playwright']:
    logger.warning("MCP Playwright is unavailable")
if not status['web_search']:
    logger.warning("Web Search is unavailable")
```

## References

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Playwright Documentation](https://playwright.dev/)
- [GeekTime Website](https://time.geekbang.org/)
- [DuckDuckGo Search](https://duckduckgo.com/)

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
