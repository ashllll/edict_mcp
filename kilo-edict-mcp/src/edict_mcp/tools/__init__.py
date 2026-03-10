"""
Tools 模块

定义 MCP 工具集合
"""

from edict_mcp.tools.tasks import get_task_tools
from edict_mcp.tools.agents import get_agent_tools
from edict_mcp.tools.events import get_event_tools

__all__ = [
    "get_task_tools",
    "get_agent_tools",
    "get_event_tools",
]
