"""
配置模块测试

测试 EdictConfig 类的功能
"""

import os
import pytest
from edict_mcp.config import EdictConfig, get_config, set_config, reset_config


class TestEdictConfig:
    """测试 EdictConfig 类"""
    
    def setup_method(self):
        """每个测试方法前重置配置"""
        reset_config()
    
    def test_default_values(self):
        """测试默认配置值"""
        config = EdictConfig()
        
        assert config.api_url == "http://localhost:8000"
        assert config.ws_url == "ws://localhost:8000"
        assert config.api_timeout == 30
        assert config.max_retries == 3
        assert config.server_name == "edict"
        assert config.server_version == "0.1.0"
    
    def test_env_variable_override(self):
        """测试环境变量覆盖"""
        os.environ["EDICT_API_URL"] = "http://example.com:9000"
        os.environ["EDICT_API_TIMEOUT"] = "60"
        os.environ["MCP_SERVER_NAME"] = "custom-edict"
        
        config = EdictConfig()
        
        assert config.api_url == "http://example.com:9000"
        assert config.api_timeout == 60
        assert config.server_name == "custom-edict"
        
        # 清理
        del os.environ["EDICT_API_URL"]
        del os.environ["EDICT_API_TIMEOUT"]
        del os.environ["MCP_SERVER_NAME"]
    
    def test_invalid_api_url(self):
        """测试无效的 API URL"""
        with pytest.raises(ValueError, match="must start with http:// or https://"):
            EdictConfig(api_url="invalid-url")
    
    def test_invalid_ws_url(self):
        """测试无效的 WebSocket URL"""
        with pytest.raises(ValueError, match="must start with ws:// or wss://"):
            EdictConfig(ws_url="invalid-url")
    
    def test_invalid_timeout(self):
        """测试无效的超时值"""
        with pytest.raises(ValueError, match="must be >= 1"):
            EdictConfig(api_timeout=0)
    
    def test_invalid_retries(self):
        """测试无效的重试次数"""
        with pytest.raises(ValueError, match="must be >= 0"):
            EdictConfig(max_retries=-1)
    
    def test_url_helpers(self):
        """测试 URL 辅助方法"""
        config = EdictConfig()
        
        assert config.api_base_url == "http://localhost:8000"
        assert config.ws_base_url == "ws://localhost:8000"
        
        assert config.get_tasks_url() == "http://localhost:8000/api/tasks"
        assert config.get_task_url("task-123") == "http://localhost:8000/api/tasks/task-123"
        assert config.get_agents_url() == "http://localhost:8000/api/agents"
        assert config.get_events_url() == "http://localhost:8000/api/events"
        assert config.get_ws_url() == "ws://localhost:8000/ws/ws"
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = EdictConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["api_url"] == "http://localhost:8000"
        assert config_dict["server_name"] == "edict"


class TestConfigSingleton:
    """测试配置单例"""
    
    def setup_method(self):
        """每个测试方法前重置配置"""
        reset_config()
    
    def test_get_config_singleton(self):
        """测试获取配置单例"""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_set_config(self):
        """测试设置配置"""
        custom_config = EdictConfig(api_url="http://custom:9999")
        set_config(custom_config)
        
        config = get_config()
        assert config.api_url == "http://custom:9999"
        
        # 清理
        reset_config()
