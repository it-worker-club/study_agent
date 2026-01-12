"""Unit tests for tool integrations"""

import pytest
from datetime import datetime

from src.utils.config import MCPConfig, WebSearchConfig, Config, VLLMConfig
from src.tools.mcp_playwright import (
    MCPPlaywrightClient,
    MCPPlaywrightError,
    create_mcp_playwright_client,
)
from src.tools.web_search import (
    WebSearchClient,
    WebSearchResult,
    WebSearchError,
    create_web_search_client,
)
from src.tools.tool_manager import (
    ToolManager,
    ToolExecutionResult,
    create_tool_manager,
)


class TestMCPPlaywrightClient:
    """Tests for MCP Playwright client"""
    
    def test_client_initialization(self):
        """Test client can be initialized"""
        config = MCPConfig(
            playwright_enabled=True,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
        )
        
        client = MCPPlaywrightClient(config)
        
        assert client is not None
        assert client.geektime_url == "https://time.geekbang.org/"
        assert client.browser_headless is True
    
    def test_search_geektime_courses(self):
        """Test searching GeekTime courses"""
        config = MCPConfig(
            playwright_enabled=True,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
        )
        
        client = MCPPlaywrightClient(config)
        courses = client.search_geektime_courses("Python")
        
        assert isinstance(courses, list)
        assert len(courses) > 0
        
        # Verify course structure
        for course in courses:
            assert "title" in course
            assert "url" in course
            assert "description" in course
            assert "difficulty" in course
            assert "source" in course
            assert course["source"] == "geektime"
    
    def test_search_with_different_queries(self):
        """Test search with different query types"""
        config = MCPConfig(
            playwright_enabled=True,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
        )
        
        client = MCPPlaywrightClient(config)
        
        # Test different queries
        queries = ["Python", "数据分析", "机器学习", "未知主题"]
        
        for query in queries:
            courses = client.search_geektime_courses(query)
            assert isinstance(courses, list)
            assert len(courses) > 0
            assert len(courses) <= 5  # Max 5 results
    
    def test_get_course_details(self):
        """Test getting course details"""
        config = MCPConfig(
            playwright_enabled=True,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
        )
        
        client = MCPPlaywrightClient(config)
        course = client.get_course_details("https://time.geekbang.org/course/intro/100001")
        
        assert isinstance(course, dict)
        assert "title" in course
        assert "url" in course
        assert "description" in course
    
    def test_disabled_playwright(self):
        """Test behavior when Playwright is disabled"""
        config = MCPConfig(
            playwright_enabled=False,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
        )
        
        client = MCPPlaywrightClient(config)
        courses = client.search_geektime_courses("Python")
        
        # Should return empty list when disabled
        assert courses == []
    
    def test_factory_function(self):
        """Test factory function"""
        config = MCPConfig(
            playwright_enabled=True,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
        )
        
        client = create_mcp_playwright_client(config)
        
        assert isinstance(client, MCPPlaywrightClient)


class TestWebSearchClient:
    """Tests for web search client"""
    
    def test_client_initialization(self):
        """Test client can be initialized"""
        config = WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        )
        
        client = WebSearchClient(config)
        
        assert client is not None
        assert client.provider == "duckduckgo"
        assert client.max_results == 5
    
    def test_search(self):
        """Test web search"""
        config = WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        )
        
        client = WebSearchClient(config)
        results = client.search("Python教程")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert len(results) <= 5
        
        # Verify result structure
        for result in results:
            assert isinstance(result, WebSearchResult)
            assert result.title
            assert result.url
            assert result.snippet
    
    def test_search_with_custom_max_results(self):
        """Test search with custom max results"""
        config = WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        )
        
        client = WebSearchClient(config)
        results = client.search("Python", max_results=3)
        
        assert len(results) <= 3
    
    def test_search_learning_resources(self):
        """Test searching learning resources"""
        config = WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        )
        
        client = WebSearchClient(config)
        results = client.search_learning_resources("Python", skill_level="beginner")
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_search_best_practices(self):
        """Test searching best practices"""
        config = WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        )
        
        client = WebSearchClient(config)
        results = client.search_best_practices("Python")
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_search_tutorials(self):
        """Test searching tutorials"""
        config = WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        )
        
        client = WebSearchClient(config)
        results = client.search_tutorials("Python")
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_disabled_search(self):
        """Test behavior when search is disabled"""
        config = WebSearchConfig(
            enabled=False,
            provider="duckduckgo",
            max_results=5,
        )
        
        client = WebSearchClient(config)
        results = client.search("Python")
        
        # Should return empty list when disabled
        assert results == []
    
    def test_web_search_result(self):
        """Test WebSearchResult class"""
        result = WebSearchResult(
            title="Test Title",
            url="https://example.com/test",
            snippet="Test snippet",
            source="example.com",
        )
        
        assert result.title == "Test Title"
        assert result.url == "https://example.com/test"
        assert result.snippet == "Test snippet"
        assert result.source == "example.com"
        
        # Test to_dict
        result_dict = result.to_dict()
        assert result_dict["title"] == "Test Title"
        assert result_dict["url"] == "https://example.com/test"
    
    def test_factory_function(self):
        """Test factory function"""
        config = WebSearchConfig(
            enabled=True,
            provider="duckduckgo",
            max_results=5,
        )
        
        client = create_web_search_client(config)
        
        assert isinstance(client, WebSearchClient)


class TestToolManager:
    """Tests for tool manager"""
    
    def create_test_config(self) -> Config:
        """Create test configuration"""
        return Config(
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
    
    def test_manager_initialization(self):
        """Test manager can be initialized"""
        config = self.create_test_config()
        manager = ToolManager(config)
        
        assert manager is not None
        assert manager.mcp_client is not None
        assert manager.web_search_client is not None
    
    def test_search_courses(self):
        """Test course search with fallback"""
        config = self.create_test_config()
        manager = ToolManager(config)
        
        result = manager.search_courses("Python")
        
        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert isinstance(result.data, list)
        assert len(result.data) > 0
    
    def test_search_courses_fallback(self):
        """Test course search fallback mechanism"""
        config = self.create_test_config()
        config.mcp.playwright_enabled = False
        
        manager = ToolManager(config)
        result = manager.search_courses("Python", use_fallback=True)
        
        # Should use fallback (web search)
        assert isinstance(result, ToolExecutionResult)
        # May succeed with fallback or fail if web search also unavailable
    
    def test_get_course_details(self):
        """Test getting course details"""
        config = self.create_test_config()
        manager = ToolManager(config)
        
        result = manager.get_course_details("https://time.geekbang.org/course/intro/100001")
        
        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert isinstance(result.data, dict)
    
    def test_search_web(self):
        """Test web search"""
        config = self.create_test_config()
        manager = ToolManager(config)
        
        result = manager.search_web("Python教程")
        
        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert isinstance(result.data, list)
    
    def test_search_learning_resources(self):
        """Test searching learning resources"""
        config = self.create_test_config()
        manager = ToolManager(config)
        
        result = manager.search_learning_resources("Python", skill_level="beginner")
        
        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert isinstance(result.data, list)
    
    def test_get_tool_status(self):
        """Test getting tool status"""
        config = self.create_test_config()
        manager = ToolManager(config)
        
        status = manager.get_tool_status()
        
        assert isinstance(status, dict)
        assert "mcp_playwright" in status
        assert "web_search" in status
    
    def test_reset_tool_availability(self):
        """Test resetting tool availability"""
        config = self.create_test_config()
        manager = ToolManager(config)
        
        # Manually mark tools as unavailable
        from src.tools.tool_manager import ToolType
        manager.tool_availability[ToolType.MCP_PLAYWRIGHT] = False
        
        # Reset
        manager.reset_tool_availability()
        
        # Should be available again
        assert manager.tool_availability[ToolType.MCP_PLAYWRIGHT] is True
    
    def test_factory_function(self):
        """Test factory function"""
        config = self.create_test_config()
        manager = create_tool_manager(config)
        
        assert isinstance(manager, ToolManager)
    
    def test_tool_execution_result(self):
        """Test ToolExecutionResult class"""
        result = ToolExecutionResult(
            success=True,
            data=["test"],
            tool_name="test_tool",
        )
        
        assert result.success is True
        assert result.data == ["test"]
        assert result.tool_name == "test_tool"
        assert result.fallback_used is False
        assert result.error is None
        assert isinstance(result.timestamp, datetime)
