"""
任务管理 Tools

定义任务相关的 MCP Tools
"""

from typing import Any, Optional
from mcp.types import Tool, TextContent
from mcp.server import Server
import logging

from edict_mcp.client import EdictClient
from edict_mcp.models import MCPTask
from edict_mcp.exceptions import (
    EdictTaskNotFoundError,
    EdictInvalidTransitionError,
    EdictError,
)

logger = logging.getLogger(__name__)


def get_task_tools(server: Server, client: EdictClient) -> list[Tool]:
    """获取任务相关的 MCP Tools
    
    Args:
        server: MCP Server 实例
        client: EdictClient 实例
        
    Returns:
        list[Tool]: Tools 列表
    """
    return [
        Tool(
            name="create_task",
            description="创建一个新任务。任务将进入 Taizi（太子分拣）状态开始流转。",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "任务标题",
                    },
                    "description": {
                        "type": "string",
                        "description": "任务描述",
                        "default": "",
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级",
                        "enum": ["低", "中", "高", "紧急"],
                        "default": "中",
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="get_task",
            description="获取任务详情，包括状态、进度、流转日志等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID",
                    },
                },
                "required": ["task_id"],
            },
        ),
        Tool(
            name="list_tasks",
            description="获取任务列表，可按状态过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "按状态过滤（Taizi, Zhongshu, Menxia, Assigned, Next, Doing, Review, Done, Blocked, Cancelled）",
                        "enum": ["Taizi", "Zhongshu", "Menxia", "Assigned", "Next", "Doing", "Review", "Done", "Blocked", "Cancelled", "Pending"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 100,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "偏移量",
                        "default": 0,
                    },
                },
            },
        ),
        Tool(
            name="delete_task",
            description="删除指定任务。",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID",
                    },
                },
                "required": ["task_id"],
            },
        ),
        Tool(
            name="transition_task",
            description="转换任务状态。状态流转必须符合三省六部流程：Taizi→Zhongshu→Menxia→Assigned→Next→Doing→Review→Done",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID",
                    },
                    "new_state": {
                        "type": "string",
                        "description": "目标状态",
                        "enum": ["Taizi", "Zhongshu", "Menxia", "Assigned", "Next", "Doing", "Review", "Done", "Blocked", "Cancelled"],
                    },
                    "reason": {
                        "type": "string",
                        "description": "流转原因",
                        "default": "",
                    },
                },
                "required": ["task_id", "new_state"],
            },
        ),
        Tool(
            name="dispatch_task",
            description="将任务派发给指定的 Agent 执行。",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID",
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "目标 Agent ID",
                    },
                    "instruction": {
                        "type": "string",
                        "description": "派发指令",
                        "default": "",
                    },
                },
                "required": ["task_id", "agent_id"],
            },
        ),
        Tool(
            name="add_progress",
            description="为任务添加进度记录。",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID",
                    },
                    "message": {
                        "type": "string",
                        "description": "进度消息",
                    },
                },
                "required": ["task_id", "message"],
            },
        ),
        Tool(
            name="update_todos",
            description="更新任务的子任务清单。",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID",
                    },
                    "todos": {
                        "type": "array",
                        "description": "子任务列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "content": {"type": "string"},
                                "done": {"type": "boolean"},
                            },
                        },
                    },
                },
                "required": ["task_id", "todos"],
            },
        ),
    ]


async def handle_create_task(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 create_task 工具调用"""
    try:
        task = await client.create_task(
            title=arguments["title"],
            description=arguments.get("description", ""),
            priority=arguments.get("priority", "中"),
        )
        return [TextContent(type="text", text="任务创建成功: " + task.model_dump_json(indent=2))]
    except EdictError as e:
        return [TextContent(type="text", text="创建任务失败: " + str(e))]


async def handle_get_task(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 get_task 工具调用"""
    try:
        task = await client.get_task(arguments["task_id"])
        return [TextContent(type="text", text=task.model_dump_json(indent=2))]
    except EdictTaskNotFoundError:
        return [TextContent(type="text", text="任务不存在: " + arguments["task_id"])]
    except EdictError as e:
        return [TextContent(type="text", text="获取任务失败: " + str(e))]


async def handle_list_tasks(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 list_tasks 工具调用"""
    try:
        tasks = await client.list_tasks(
            state=arguments.get("state"),
            limit=arguments.get("limit", 100),
            offset=arguments.get("offset", 0),
        )
        if not tasks:
            return [TextContent(type="text", text="没有找到任务")]
        
        result = ["共 {} 个任务:".format(len(tasks))]
        for task in tasks:
            result.append("- [{}] {} ({})".format(task.id, task.title, task.state))
        
        return [TextContent(type="text", text="\n".join(result))]
    except EdictError as e:
        return [TextContent(type="text", text="获取任务列表失败: " + str(e))]


async def handle_delete_task(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 delete_task 工具调用"""
    try:
        await client.delete_task(arguments["task_id"])
        return [TextContent(type="text", text="任务已删除: " + arguments["task_id"])]
    except EdictError as e:
        return [TextContent(type="text", text="删除任务失败: " + str(e))]


async def handle_transition_task(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 transition_task 工具调用"""
    try:
        task = await client.transition_task(
            task_id=arguments["task_id"],
            new_state=arguments["new_state"],
            reason=arguments.get("reason", ""),
        )
        return [TextContent(type="text", text="状态转换成功: " + task.model_dump_json(indent=2))]
    except EdictTaskNotFoundError:
        return [TextContent(type="text", text="任务不存在: " + arguments["task_id"])]
    except EdictInvalidTransitionError as e:
        return [TextContent(type="text", text="无效的状态转换: " + str(e))]
    except EdictError as e:
        return [TextContent(type="text", text="状态转换失败: " + str(e))]


async def handle_dispatch_task(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 dispatch_task 工具调用"""
    try:
        task = await client.dispatch_task(
            task_id=arguments["task_id"],
            agent_id=arguments["agent_id"],
            instruction=arguments.get("instruction", ""),
        )
        return [TextContent(type="text", text="任务派发成功: " + task.model_dump_json(indent=2))]
    except EdictTaskNotFoundError:
        return [TextContent(type="text", text="任务不存在: " + arguments["task_id"])]
    except EdictError as e:
        return [TextContent(type="text", text="任务派发失败: " + str(e))]


async def handle_add_progress(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 add_progress 工具调用"""
    try:
        task = await client.add_progress(
            task_id=arguments["task_id"],
            message=arguments["message"],
        )
        return [TextContent(type="text", text="进度添加成功: " + task.model_dump_json(indent=2))]
    except EdictError as e:
        return [TextContent(type="text", text="添加进度失败: " + str(e))]


async def handle_update_todos(client: EdictClient, arguments: dict) -> list[TextContent]:
    """处理 update_todos 工具调用"""
    try:
        task = await client.update_todos(
            task_id=arguments["task_id"],
            todos=arguments["todos"],
        )
        return [TextContent(type="text", text="子任务更新成功: " + task.model_dump_json(indent=2))]
    except EdictError as e:
        return [TextContent(type="text", text="更新子任务失败: " + str(e))]


# 工具处理器映射
TASK_TOOL_HANDLERS = {
    "create_task": handle_create_task,
    "get_task": handle_get_task,
    "list_tasks": handle_list_tasks,
    "delete_task": handle_delete_task,
    "transition_task": handle_transition_task,
    "dispatch_task": handle_dispatch_task,
    "add_progress": handle_add_progress,
    "update_todos": handle_update_todos,
}
