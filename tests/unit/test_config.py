"""Unit tests for configuration management"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.utils.config import (
    AgentConfig,
    AgentsConfig,
    Config,
    LoggingConfig,
    MCPConfig,
    SystemConfig,
    VLLMConfig,
    WebSearchConfig,
    get_config,
    load_config,
)


class TestVLLMConfig:
    """Test vLLM configuration model"""
    
    def test_valid_config(self):
        """Test creating valid vLLM config"""
        config = VLLMConfig(
            api_base="http://localhost:8000/v1",
            model_name="test-model",
            temperature=0.7,
            max_tokens=2000,
            timeout=60,
        )
        
        assert config.api_base == "http://localhost:8000/v1"
        assert config.model_name == "test-model"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.timeout == 60
        assert config.api_key is None
    
    def test_with_api_key(self):
        """Test vLLM config with API key"""
        config = VLLMConfig(
            api_base="http://localhost:8000/v1",
            api_key="secret-key",
            model_name="test-model",
        )
        
        assert config.api_key == "secret-key"
    
    def test_invalid_temperature(self):
        """Test that invalid temperature raises error"""
        with pytest.raises(ValueError):
            VLLMConfig(
                api_base="http://localhost:8000/v1",
                model_name="test-model",
                temperature=3.0,  # Invalid: > 2.0
            )
    
    def test_invalid_max_tokens(self):
        """Test that invalid max_tokens raises error"""
        with pytest.raises(ValueError):
            VLLMConfig(
                api_base="http://localhost:8000/v1",
                model_name="test-model",
                max_tokens=0,  # Invalid: must be > 0
            )


class TestMCPConfig:
    """Test MCP configuration model"""
    
    def test_valid_config(self):
        """Test creating valid MCP config"""
        config = MCPConfig(
            playwright_enabled=True,
            geektime_url="https://time.geekbang.org/",
            browser_headless=True,
            browser_timeout=30000,
        )
        
        assert config.playwright_enabled is True
        assert config.geektime_url == "https://time.geekbang.org/"
        assert config.browser_headless is True
        assert config.browser_timeout == 30000
    
    def test_default_values(self):
        """Test MCP config default values"""
        config = MCPConfig()
        
        assert config.playwright_enabled is True
        assert config.geektime_url == "https://time.geekbang.org/"
        assert config.browser_headless is True


class TestSystemConfig:
    """Test system configuration model"""
    
    def test_valid_config(self):
        """Test creating valid system config"""
        config = SystemConfig(
            database_path="./test.db",
            max_loop_count=10,
            enable_human_input=True,
            session_timeout=30,
        )
        
        assert config.database_path == "./test.db"
        assert config.max_loop_count == 10
        assert config.enable_human_input is True
        assert config.session_timeout == 30
    
    def test_default_values(self):
        """Test system config default values"""
        config = SystemConfig()
        
        assert config.database_path == "./data/tutoring_system.db"
        assert config.max_loop_count == 10
        assert config.enable_human_input is True


class TestAgentConfig:
    """Test agent configuration model"""
    
    def test_valid_config(self):
        """Test creating valid agent config"""
        config = AgentConfig(temperature=0.5, max_tokens=1500)
        
        assert config.temperature == 0.5
        assert config.max_tokens == 1500
    
    def test_default_values(self):
        """Test agent config default values"""
        config = AgentConfig()
        
        assert config.temperature == 0.7
        assert config.max_tokens == 2000


class TestCompleteConfig:
    """Test complete configuration model"""
    
    def test_minimal_config(self):
        """Test creating config with minimal required fields"""
        config = Config(
            vllm=VLLMConfig(
                api_base="http://localhost:8000/v1",
                model_name="test-model",
            ),
            mcp=MCPConfig(),
        )
        
        assert config.vllm.api_base == "http://localhost:8000/v1"
        assert config.mcp.playwright_enabled is True
        assert config.system.max_loop_count == 10
        assert config.logging.level == "INFO"
    
    def test_full_config(self):
        """Test creating config with all fields"""
        config = Config(
            vllm=VLLMConfig(
                api_base="http://localhost:8000/v1",
                api_key="secret",
                model_name="test-model",
                temperature=0.8,
                max_tokens=3000,
                timeout=120,
            ),
            mcp=MCPConfig(
                playwright_enabled=False,
                geektime_url="https://example.com/",
                browser_headless=False,
            ),
            web_search=WebSearchConfig(
                enabled=False,
                provider="google",
                max_results=10,
            ),
            system=SystemConfig(
                database_path="./custom.db",
                max_loop_count=20,
                enable_human_input=False,
                session_timeout=60,
            ),
            logging=LoggingConfig(
                level="DEBUG",
                file="./custom.log",
            ),
            agents=AgentsConfig(
                coordinator=AgentConfig(temperature=0.5, max_tokens=1000),
                course_advisor=AgentConfig(temperature=0.6, max_tokens=1500),
                learning_planner=AgentConfig(temperature=0.7, max_tokens=2000),
            ),
        )
        
        assert config.vllm.api_key == "secret"
        assert config.mcp.playwright_enabled is False
        assert config.web_search.enabled is False
        assert config.system.database_path == "./custom.db"
        assert config.logging.level == "DEBUG"
        assert config.agents.coordinator.temperature == 0.5


class TestConfigLoading:
    """Test configuration loading from files"""
    
    def test_load_valid_yaml(self):
        """Test loading valid YAML configuration"""
        config_data = {
            "vllm": {
                "api_base": "http://localhost:8000/v1",
                "model_name": "test-model",
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 60,
            },
            "mcp": {
                "playwright_enabled": True,
                "geektime_url": "https://time.geekbang.org/",
                "browser_headless": True,
            },
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            assert config.vllm.api_base == "http://localhost:8000/v1"
            assert config.vllm.model_name == "test-model"
            assert config.mcp.playwright_enabled is True
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises error"""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.yaml")
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises error"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_empty_file(self):
        """Test loading empty file raises error"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="empty"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_missing_required_fields(self):
        """Test loading config with missing required fields raises error"""
        config_data = {
            "mcp": {
                "playwright_enabled": True,
            },
            # Missing required vllm section
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)


class TestGetConfig:
    """Test get_config function"""
    
    def test_get_config_with_path(self):
        """Test get_config with explicit path"""
        config_data = {
            "vllm": {
                "api_base": "http://localhost:8000/v1",
                "model_name": "test-model",
            },
            "mcp": {
                "playwright_enabled": True,
            },
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = get_config(temp_path)
            assert config.vllm.model_name == "test-model"
        finally:
            os.unlink(temp_path)
    
    def test_get_config_finds_standard_location(self):
        """Test get_config finds config in standard location"""
        # This test verifies that get_config can find the config file
        # in the standard location (config/system_config.yaml)
        config = get_config()
        assert config is not None
        assert config.vllm is not None
        assert config.mcp is not None


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_temperature_bounds(self):
        """Test temperature parameter bounds"""
        # Valid temperatures
        VLLMConfig(
            api_base="http://localhost:8000/v1",
            model_name="test",
            temperature=0.0,
        )
        VLLMConfig(
            api_base="http://localhost:8000/v1",
            model_name="test",
            temperature=2.0,
        )
        
        # Invalid temperatures
        with pytest.raises(ValueError):
            VLLMConfig(
                api_base="http://localhost:8000/v1",
                model_name="test",
                temperature=-0.1,
            )
        
        with pytest.raises(ValueError):
            VLLMConfig(
                api_base="http://localhost:8000/v1",
                model_name="test",
                temperature=2.1,
            )
    
    def test_positive_integer_fields(self):
        """Test that integer fields must be positive"""
        # Valid values
        SystemConfig(max_loop_count=1)
        VLLMConfig(
            api_base="http://localhost:8000/v1",
            model_name="test",
            max_tokens=1,
            timeout=1,
        )
        
        # Invalid values
        with pytest.raises(ValueError):
            SystemConfig(max_loop_count=0)
        
        with pytest.raises(ValueError):
            VLLMConfig(
                api_base="http://localhost:8000/v1",
                model_name="test",
                max_tokens=0,
            )
