"""
Agent 管理 Tools

定义 Agent 相关的 MCP Tools
"""

from typing import Any
from mcp.types import Tool, TextContent
from mcp.server import Server
import json

from edict_mcp.client import EdictClient
from edict_mcp.exceptions import EdictAgentNotFoundError, EdictError

import logging

logger = logging.getLogger(__name__)


def get_agent_tools(server: Server, client: EdictClient) -> list[Tool]:
    """获取 Agent 相关的 MCP Tools
    
    Args:
        server: MCP Server 实例
        client: EdictClient 实例
        
    Returns:
        list[Tool]: Tools 列表
    """
    return [
        Tool(
            name="list_agents",
            description="获取所有 Agent 的列表，包括各 Agent 的角色、部门、状态等信息。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_agent",
            description="获取指定 Agent 的详细信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent ID",
                    },
                },
                "required": ["agent_id"],
            },
        ),
        Tool(
            name="get_agent_config",
            description="获取指定 Agent 的配置信息，包括模型、技能等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent ID",
                    },
                },
                "required": ["agent_id"],
            },
        ),
    ]


async def handle_list_agents(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 list_agents 工具调用"""
    try:
        agents = await client.list_agents()
        if not agents:
            return [TextContent(type="text", text="没有找到 Agent")]
        
        result = ["共 {} 个 Agent:".format(len(agents))]
        for agent in agents:
            result.append("- [{}] {} - {} ({})".format(
                agent.id, agent.name, agent.role or agent.department, agent.status
            ))
        
        return [TextContent(type="text", text="\n".join(result))]
    except EdictError as e:
        return [TextContent(type="text", text="获取 Agent 列表失败: " + str(e))]


async def handle_get_agent(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 get_agent 工具调用"""
    try:
        agent = await client.get_agent(arguments["agent_id"])
        return [TextContent(type="text", text=agent.model_dump_json(indent=2))]
    except EdictAgentNotFoundError:
        return [TextContent(type="text", text="Agent 不存在: " + arguments["agent_id"])]
    except EdictError as e:
        return [TextContent(type="text", text="获取 Agent 详情失败: " + str(e))]


async def handle_get_agent_config(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 get_agent_config 工具调用"""
    try:
        config = await client.get_agent_config(arguments["agent_id"])
        return [TextContent(type="text", text=json.dumps(config, indent=2, ensure_ascii=False))]
    except EdictAgentNotFoundError:
        return [TextContent(type="text", text="Agent 不存在: " + arguments["agent_id"])]
    except EdictError as e:
        return [TextContent(type="text", text="获取 Agent 配置失败: " + str(e))]


# 工具处理器映射
AGENT_TOOL_HANDLERS = {
    "list_agents": handle_list_agents,
    "get_agent": handle_get_agent,
    "get_agent_config": handle_get_agent_config,
}
