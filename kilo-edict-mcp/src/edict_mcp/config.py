"""
配置管理模块

管理 Edict MCP Server 的所有配置项
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class EdictConfig:
    """Edict MCP Server 配置类"""
    
    # Edict API 配置
    api_url: str = field(
        default_factory=lambda: os.getenv("EDICT_API_URL", "http://localhost:8000")
    )
    ws_url: str = field(
        default_factory=lambda: os.getenv("EDICT_WS_URL", "ws://localhost:8000")
    )
    api_timeout: int = field(
        default_factory=lambda: int(os.getenv("EDICT_API_TIMEOUT", "30"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("EDICT_MAX_RETRIES", "3"))
    )
    
    # WebSocket 配置
    ws_reconnect_delay: int = field(
        default_factory=lambda: int(os.getenv("EDICT_WS_RECONNECT_DELAY", "5"))
    )
    ws_heartbeat_interval: int = field(
        default_factory=lambda: int(os.getenv("EDICT_WS_HEARTBEAT_INTERVAL", "30"))
    )
    
    # MCP Server 配置
    server_name: str = field(
        default_factory=lambda: os.getenv("MCP_SERVER_NAME", "edict")
    )
    server_version: str = field(
        default_factory=lambda: os.getenv("MCP_SERVER_VERSION", "0.1.0")
    )
    
    # 日志配置
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    
    def __post_init__(self):
        """验证配置的有效性"""
        self._validate_api_url()
        self._validate_ws_url()
        self._validate_timeout()
        self._validate_retries()
    
    def _validate_api_url(self):
        """验证 API URL 格式"""
        if not self.api_url.startswith(("http://", "https://")):
            raise ValueError(
                f"EDICT_API_URL must start with http:// or https://, got: {self.api_url}"
            )
    
    def _validate_ws_url(self):
        """验证 WebSocket URL 格式"""
        if not self.ws_url.startswith(("ws://", "wss://")):
            raise ValueError(
                f"EDICT_WS_URL must start with ws:// or wss://, got: {self.ws_url}"
            )
    
    def _validate_timeout(self):
        """验证超时时间"""
        if self.api_timeout < 1:
            raise ValueError(
                f"EDICT_API_TIMEOUT must be >= 1, got: {self.api_timeout}"
            )
    
    def _validate_retries(self):
        """验证重试次数"""
        if self.max_retries < 0:
            raise ValueError(
                f"EDICT_MAX_RETRIES must be >= 0, got: {self.max_retries}"
            )
    
    @property
    def api_base_url(self) -> str:
        """获取 API 基础 URL（不含路径）"""
        return self.api_url.rstrip("/")
    
    @property
    def ws_base_url(self) -> str:
        """获取 WebSocket 基础 URL（不含路径）"""
        return self.ws_url.rstrip("/")
    
    def get_tasks_url(self) -> str:
        """获取任务 API URL"""
        return f"{self.api_base_url}/api/tasks"
    
    def get_task_url(self, task_id: str) -> str:
        """获取单个任务 API URL"""
        return f"{self.api_base_url}/api/tasks/{task_id}"
    
    def get_task_transition_url(self, task_id: str) -> str:
        """获取任务状态流转 API URL"""
        return f"{self.api_base_url}/api/tasks/{task_id}/transition"
    
    def get_task_dispatch_url(self, task_id: str) -> str:
        """获取任务派发 API URL"""
        return f"{self.api_base_url}/api/tasks/{task_id}/dispatch"
    
    def get_agents_url(self) -> str:
        """获取 Agent 列表 API URL"""
        return f"{self.api_base_url}/api/agents"
    
    def get_agent_url(self, agent_id: str) -> str:
        """获取单个 Agent API URL"""
        return f"{self.api_base_url}/api/agents/{agent_id}"
    
    def get_events_url(self) -> str:
        """获取事件 API URL"""
        return f"{self.api_base_url}/api/events"
    
    def get_ws_url(self, path: str = "/ws/ws") -> str:
        """获取 WebSocket URL"""
        return f"{self.ws_base_url}{path}"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "api_url": self.api_url,
            "ws_url": self.ws_url,
            "api_timeout": self.api_timeout,
            "max_retries": self.max_retries,
            "ws_reconnect_delay": self.ws_reconnect_delay,
            "server_name": self.server_name,
            "server_version": self.server_version,
            "log_level": self.log_level,
        }


# 全局配置实例
_config: Optional[EdictConfig] = None


def get_config() -> EdictConfig:
    """获取全局配置实例（单例模式）"""
    global _config
    if _config is None:
        _config = EdictConfig()
    return _config


def set_config(config: EdictConfig) -> None:
    """设置全局配置实例"""
    global _config
    _config = config


def reset_config() -> None:
    """重置全局配置实例"""
    global _config
    _config = None
