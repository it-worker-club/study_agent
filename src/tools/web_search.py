"""Web search tool integration for supplementary learning resources"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils.logger import get_logger
from ..utils.config import WebSearchConfig

logger = get_logger(__name__)


class WebSearchError(Exception):
    """Base exception for web search errors"""
    pass


class WebSearchConnectionError(WebSearchError):
    """Raised when connection to search service fails"""
    pass


class WebSearchAPIError(WebSearchError):
    """Raised when search API returns an error"""
    pass


class WebSearchResult:
    """Represents a single web search result"""
    
    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: Optional[str] = None,
    ):
        """
        Initialize web search result.
        
        Args:
            title: Result title
            url: Result URL
            snippet: Result snippet/description
            source: Source website
        """
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source or self._extract_domain(url)
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }
    
    def __repr__(self) -> str:
        return f"WebSearchResult(title='{self.title}', url='{self.url}')"


class WebSearchClient:
    """
    Client for web search functionality.
    
    Provides methods to search the web for supplementary learning resources.
    Currently uses a simulated search, but can be extended to use real APIs
    like DuckDuckGo, Google Custom Search, or Bing Search.
    """
    
    def __init__(self, config: WebSearchConfig):
        """
        Initialize web search client.
        
        Args:
            config: Web search configuration
        """
        self.config = config
        self.provider = config.provider
        self.max_results = config.max_results
        
        logger.info(
            f"Initialized web search client: "
            f"provider={self.provider}, max_results={self.max_results}"
        )
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    def search(self, query: str, max_results: Optional[int] = None) -> List[WebSearchResult]:
        """
        Search the web for information.
        
        Args:
            query: Search query string
            max_results: Maximum number of results (overrides config)
        
        Returns:
            List of search results
        
        Raises:
            WebSearchError: If search fails
        """
        if not self.config.enabled:
            logger.warning("Web search is disabled in configuration")
            return []
        
        max_results = max_results or self.max_results
        
        logger.info(f"Searching web: query='{query}', max_results={max_results}")
        
        try:
            # TODO: Implement actual web search API integration
            # This is a placeholder implementation
            
            if self.provider == "duckduckgo":
                results = self._search_duckduckgo(query, max_results)
            else:
                results = self._simulate_search(query, max_results)
            
            logger.info(f"Found {len(results)} results for query '{query}'")
            return results
        
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            raise WebSearchError(f"Search failed: {e}") from e
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[WebSearchResult]:
        """
        Search using DuckDuckGo.
        
        This is a placeholder for actual DuckDuckGo API integration.
        In production, this would use the duckduckgo-search library or API.
        
        Args:
            query: Search query
            max_results: Maximum results
        
        Returns:
            List of search results
        """
        # TODO: Implement actual DuckDuckGo search
        # For now, use simulation
        return self._simulate_search(query, max_results)
    
    def _simulate_search(self, query: str, max_results: int) -> List[WebSearchResult]:
        """
        Simulate web search results.
        
        This is a placeholder that returns mock data.
        In production, this would be replaced with actual search API calls.
        
        Args:
            query: Search query
            max_results: Maximum results
        
        Returns:
            List of simulated search results
        """
        query_lower = query.lower()
        results: List[WebSearchResult] = []
        
        # Generate mock results based on query
        if "python" in query_lower:
            results.extend([
                WebSearchResult(
                    title="Python官方文档",
                    url="https://docs.python.org/zh-cn/3/",
                    snippet="Python 3.x 官方中文文档，包含教程、库参考和语言参考。",
                    source="docs.python.org",
                ),
                WebSearchResult(
                    title="Real Python - Python教程和文章",
                    url="https://realpython.com/",
                    snippet="高质量的Python教程、文章和视频课程，适合各个水平的学习者。",
                    source="realpython.com",
                ),
                WebSearchResult(
                    title="Python最佳实践指南",
                    url="https://docs.python-guide.org/",
                    snippet="Python开发的最佳实践和风格指南，由社区维护。",
                    source="docs.python-guide.org",
                ),
            ])
        
        if "数据分析" in query_lower or "data analysis" in query_lower:
            results.extend([
                WebSearchResult(
                    title="Pandas官方文档",
                    url="https://pandas.pydata.org/docs/",
                    snippet="Pandas是Python中最流行的数据分析库，提供强大的数据结构和分析工具。",
                    source="pandas.pydata.org",
                ),
                WebSearchResult(
                    title="数据分析学习路径 - Kaggle",
                    url="https://www.kaggle.com/learn",
                    snippet="Kaggle提供的免费数据分析和机器学习课程，包含实践项目。",
                    source="kaggle.com",
                ),
            ])
        
        if "机器学习" in query_lower or "machine learning" in query_lower:
            results.extend([
                WebSearchResult(
                    title="机器学习课程 - Coursera",
                    url="https://www.coursera.org/learn/machine-learning",
                    snippet="Andrew Ng教授的经典机器学习课程，适合初学者。",
                    source="coursera.org",
                ),
                WebSearchResult(
                    title="Scikit-learn官方教程",
                    url="https://scikit-learn.org/stable/tutorial/",
                    snippet="Scikit-learn是Python中最流行的机器学习库，提供丰富的算法实现。",
                    source="scikit-learn.org",
                ),
            ])
        
        if "学习路径" in query_lower or "learning path" in query_lower:
            results.extend([
                WebSearchResult(
                    title="开发者学习路线图",
                    url="https://roadmap.sh/",
                    snippet="各种技术栈的学习路线图，帮助开发者规划学习路径。",
                    source="roadmap.sh",
                ),
                WebSearchResult(
                    title="GitHub学习资源集合",
                    url="https://github.com/topics/learning-resources",
                    snippet="GitHub上精选的学习资源和教程集合。",
                    source="github.com",
                ),
            ])
        
        # If no specific matches, return generic results
        if not results:
            results = [
                WebSearchResult(
                    title=f"{query} - 学习资源",
                    url=f"https://example.com/learn/{query.replace(' ', '-')}",
                    snippet=f"关于{query}的学习资源和教程。",
                    source="example.com",
                ),
                WebSearchResult(
                    title=f"{query} - 最佳实践",
                    url=f"https://example.com/best-practices/{query.replace(' ', '-')}",
                    snippet=f"{query}的最佳实践和经验分享。",
                    source="example.com",
                ),
                WebSearchResult(
                    title=f"{query} - 入门指南",
                    url=f"https://example.com/guide/{query.replace(' ', '-')}",
                    snippet=f"从零开始学习{query}的完整指南。",
                    source="example.com",
                ),
            ]
        
        return results[:max_results]
    
    def search_learning_resources(
        self,
        topic: str,
        skill_level: Optional[str] = None,
    ) -> List[WebSearchResult]:
        """
        Search for learning resources on a specific topic.
        
        Args:
            topic: Learning topic
            skill_level: User's skill level (beginner/intermediate/advanced)
        
        Returns:
            List of relevant learning resources
        """
        # Construct query based on topic and skill level
        query = f"{topic} 学习资源"
        
        if skill_level:
            level_map = {
                "beginner": "入门",
                "intermediate": "进阶",
                "advanced": "高级",
            }
            level_term = level_map.get(skill_level, "")
            if level_term:
                query = f"{topic} {level_term} 教程"
        
        return self.search(query)
    
    def search_best_practices(self, topic: str) -> List[WebSearchResult]:
        """
        Search for best practices on a specific topic.
        
        Args:
            topic: Topic to search for
        
        Returns:
            List of best practice resources
        """
        query = f"{topic} 最佳实践"
        return self.search(query)
    
    def search_tutorials(self, topic: str) -> List[WebSearchResult]:
        """
        Search for tutorials on a specific topic.
        
        Args:
            topic: Topic to search for
        
        Returns:
            List of tutorial resources
        """
        query = f"{topic} 教程"
        return self.search(query)


def create_web_search_client(config: WebSearchConfig) -> WebSearchClient:
    """
    Factory function to create web search client.
    
    Args:
        config: Web search configuration
    
    Returns:
        Initialized web search client
    """
    return WebSearchClient(config)


def parse_search_results(results: List[WebSearchResult]) -> List[Dict[str, Any]]:
    """
    Parse search results into dictionary format.
    
    Args:
        results: List of search results
    
    Returns:
        List of result dictionaries
    """
    return [result.to_dict() for result in results]
