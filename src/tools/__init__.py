"""External tool integrations"""

from .mcp_playwright import (
    MCPPlaywrightClient,
    MCPPlaywrightError,
    MCPPlaywrightConnectionError,
    MCPPlaywrightNavigationError,
    create_mcp_playwright_client,
)

from .web_search import (
    WebSearchClient,
    WebSearchError,
    WebSearchConnectionError,
    WebSearchAPIError,
    WebSearchResult,
    create_web_search_client,
    parse_search_results,
)

from .tool_manager import (
    ToolManager,
    ToolType,
    ToolExecutionResult,
    create_tool_manager,
)

__all__ = [
    # MCP Playwright
    "MCPPlaywrightClient",
    "MCPPlaywrightError",
    "MCPPlaywrightConnectionError",
    "MCPPlaywrightNavigationError",
    "create_mcp_playwright_client",
    # Web Search
    "WebSearchClient",
    "WebSearchError",
    "WebSearchConnectionError",
    "WebSearchAPIError",
    "WebSearchResult",
    "create_web_search_client",
    "parse_search_results",
    # Tool Manager
    "ToolManager",
    "ToolType",
    "ToolExecutionResult",
    "create_tool_manager",
]
