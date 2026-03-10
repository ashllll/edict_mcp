"""
事件查询 Tools

定义事件相关的 MCP Tools
"""

from typing import Any, Optional
from mcp.types import Tool, TextContent
from mcp.server import Server
import json

from edict_mcp.client import EdictClient
from edict_mcp.exceptions import EdictError

import logging

logger = logging.getLogger(__name__)


def get_event_tools(server: Server, client: EdictClient) -> list[Tool]:
    """获取事件相关的 MCP Tools
    
    Args:
        server: MCP Server 实例
        client: EdictClient 实例
        
    Returns:
        list[Tool]: Tools 列表
    """
    return [
        Tool(
            name="list_events",
            description="获取事件列表，可按主题或任务 ID 过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "事件主题过滤",
                    },
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID 过滤",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 100,
                    },
                },
            },
        ),
        Tool(
            name="list_topics",
            description="获取所有事件主题列表。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_stream_info",
            description="获取 Redis Stream 的详细信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Stream 主题",
                        "default": "task_events",
                    },
                },
            },
        ),
    ]


async def handle_list_events(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 list_events 工具调用"""
    try:
        events = await client.list_events(
            topic=arguments.get("topic"),
            task_id=arguments.get("task_id"),
            limit=arguments.get("limit", 100),
        )
        if not events:
            return [TextContent(type="text", text="没有找到事件")]
        
        result = ["共 {} 个事件:".format(len(events))]
        for event in events:
            result.append("- [{}] {} - {} ({})".format(
                event.id, event.topic, event.task_id or "N/A", event.timestamp
            ))
        
        return [TextContent(type="text", text="\n".join(result))]
    except EdictError as e:
        return [TextContent(type="text", text="获取事件列表失败: " + str(e))]


async def handle_list_topics(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 list_topics 工具调用"""
    try:
        topics = await client.list_topics()
        if not topics:
            return [TextContent(type="text", text="没有找到事件主题")]
        
        result = ["事件主题:"]
        for topic in topics:
            result.append("- {}".format(topic))
        
        return [TextContent(type="text", text="\n".join(result))]
    except EdictError as e:
        return [TextContent(type="text", text="获取事件主题列表失败: " + str(e))]


async def handle_get_stream_info(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 get_stream_info 工具调用"""
    try:
        info = await client.get_stream_info(arguments.get("topic", "task_events"))
        return [TextContent(type="text", text=info.model_dump_json(indent=2))]
    except EdictError as e:
        return [TextContent(type="text", text="获取 Stream 信息失败: " + str(e))]


# 工具处理器映射
EVENT_TOOL_HANDLERS = {
    "list_events": handle_list_events,
    "list_topics": handle_list_topics,
    "get_stream_info": handle_get_stream_info,
}
