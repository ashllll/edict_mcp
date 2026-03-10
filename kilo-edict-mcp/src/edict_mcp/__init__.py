"""
Edict MCP - MCP integration for Edict Agent Platform

基于中国古代"三省六部"制度的 AI Agent 协作平台的 MCP 集成方案
"""

__version__ = "0.1.0"
__author__ = "Edict Team"
__description__ = "MCP integration for Edict Agent Platform"

from edict_mcp.client import EdictClient
from edict_mcp.models import MCPTask, MCPAgent, MCPEvent

__all__ = [
    "EdictClient",
    "MCPTask",
    "MCPAgent",
    "MCPEvent",
]
