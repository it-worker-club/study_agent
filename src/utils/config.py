"""Configuration management for the education tutoring system"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field


class VLLMConfig(BaseModel):
    """vLLM service configuration"""
    
    api_base: str = Field(..., description="vLLM API endpoint")
    api_key: Optional[str] = Field(None, description="API key (if required)")
    model_name: str = Field(..., description="Model name")
    temperature: float = Field(0.7, description="Temperature parameter", ge=0.0, le=2.0)
    max_tokens: int = Field(2000, description="Maximum tokens to generate", gt=0)
    timeout: int = Field(60, description="Request timeout in seconds", gt=0)


class MCPConfig(BaseModel):
    """MCP tool configuration"""
    
    playwright_enabled: bool = Field(True, description="Enable Playwright integration")
    geektime_url: str = Field("https://time.geekbang.org/", description="GeekTime URL")
    browser_headless: bool = Field(True, description="Run browser in headless mode")
    browser_timeout: int = Field(30000, description="Browser timeout in milliseconds", gt=0)


class WebSearchConfig(BaseModel):
    """Web search configuration"""
    
    enabled: bool = Field(True, description="Enable web search tool")
    provider: str = Field("duckduckgo", description="Search provider")
    max_results: int = Field(5, description="Maximum search results", gt=0)


class SystemConfig(BaseModel):
    """System-level configuration"""
    
    database_path: str = Field("./data/tutoring_system.db", description="Database path")
    max_loop_count: int = Field(10, description="Maximum loop count", gt=0)
    enable_human_input: bool = Field(True, description="Enable human-in-the-loop")
    session_timeout: int = Field(30, description="Session timeout in minutes", gt=0)


class LoggingConfig(BaseModel):
    """Logging configuration"""
    
    level: str = Field("INFO", description="Log level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )
    file: Optional[str] = Field(None, description="Log file path")
    max_file_size: int = Field(10, description="Max log file size in MB", gt=0)
    backup_count: int = Field(5, description="Number of backup log files", ge=0)


class AgentConfig(BaseModel):
    """Individual agent configuration"""
    
    temperature: float = Field(0.7, description="Temperature parameter", ge=0.0, le=2.0)
    max_tokens: int = Field(2000, description="Maximum tokens", gt=0)


class AgentsConfig(BaseModel):
    """Configuration for all agents"""
    
    coordinator: AgentConfig = Field(default_factory=lambda: AgentConfig(temperature=0.7, max_tokens=1500))
    course_advisor: AgentConfig = Field(default_factory=lambda: AgentConfig(temperature=0.6, max_tokens=2000))
    learning_planner: AgentConfig = Field(default_factory=lambda: AgentConfig(temperature=0.5, max_tokens=2500))


class Config(BaseModel):
    """Complete system configuration"""
    
    vllm: VLLMConfig
    mcp: MCPConfig
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)


def load_config(config_path: str = "config/system_config.yaml") -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Parsed configuration object
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        
        if config_dict is None:
            raise ValueError("Configuration file is empty")
        
        return Config(**config_dict)
    
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading configuration: {e}")


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get configuration, loading from file or environment.
    
    Args:
        config_path: Optional path to configuration file
    
    Returns:
        Configuration object
    """
    if config_path is None:
        # Try to find config in standard locations
        possible_paths = [
            "config/system_config.yaml",
            "system_config.yaml",
            os.path.expanduser("~/.config/education-tutoring-system/config.yaml"),
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                config_path = path
                break
    
    if config_path is None:
        raise FileNotFoundError(
            "No configuration file found. Please create config/system_config.yaml"
        )
    
    return load_config(config_path)
