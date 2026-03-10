"""
系统状态 Resources

定义系统状态相关的 MCP Resources
"""

import json
import logging
from typing import Any

from mcp.types import Resource, ResourceTemplate
from mcp.server import Server

from edict_mcp.client import EdictClient

logger = logging.getLogger(__name__)


def get_system_resources(server: Server, client: EdictClient) -> list[Resource]:
    """获取系统状态相关的 Resources
    
    Args:
        server: MCP Server 实例
        client: EdictClient 实例
        
    Returns:
        list[Resource]: Resources 列表
    """
    return [
        Resource(
            uri="edict://system/status",
            name="system_status",
            description="Edict 系统状态，包括任务总数、Agent 数量等",
            mimeType="application/json",
        ),
        Resource(
            uri="edict://tasks/count",
            name="tasks_count",
            description="任务统计信息",
            mimeType="application/json",
        ),
        Resource(
            uri="edict://tasks/by-state",
            name="tasks_by_state",
            description="按状态分类的任务统计",
            mimeType="application/json",
        ),
        Resource(
            uri="edict://agents/list",
            name="agents_list",
            description="所有 Agent 的列表",
            mimeType="application/json",
        ),
    ]


def get_resource_templates(server: Server, client: EdictClient) -> list[ResourceTemplate]:
    """获取资源模板
    
    Args:
        server: MCP Server 实例
        client: EdictClient 实例
        
    Returns:
        list[ResourceTemplate]: Resource 模板列表
    """
    return [
        ResourceTemplate(
            uri="edict://task/{task_id}",
            name="task_detail",
            description="获取指定任务的详细信息",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uri="edict://agent/{agent_id}",
            name="agent_detail",
            description="获取指定 Agent 的详细信息",
            mimeType="application/json",
        ),
    ]


async def handle_read_resource(
    client: EdictClient,
    uri: str,
) -> dict[str, Any]:
    """处理 Resource 读取请求
    
    Args:
        client: EdictClient 实例
        uri: Resource URI
        
    Returns:
        dict: Resource 内容
        
    Raises:
        ValueError: 未知的 Resource URI
    """
    # 系统状态
    if uri == "edict://system/status":
        status = await client.get_system_status()
        return {"content": status.model_dump_json(), "mime_type": "application/json"}
    
    # 任务总数
    elif uri == "edict://tasks/count":
        all_tasks = await client.list_tasks(limit=1000)
        return {
            "content": json.dumps({"total": len(all_tasks)}, ensure_ascii=False),
            "mime_type": "application/json"
        }
    
    # 按状态统计任务
    elif uri == "edict://tasks/by-state":
        all_tasks = await client.list_tasks(limit=1000)
        state_counts: dict[str, int] = {}
        for task in all_tasks:
            state = task.state if isinstance(task.state, str) else str(task.state)
            state_counts[state] = state_counts.get(state, 0) + 1
        return {
            "content": json.dumps(state_counts, ensure_ascii=False),
            "mime_type": "application/json"
        }
    
    # Agent 列表
    elif uri == "edict://agents/list":
        agents = await client.list_agents()
        agent_list = [a.model_dump() for a in agents]
        return {
            "content": json.dumps(agent_list, ensure_ascii=False),
            "mime_type": "application/json"
        }
    
    # 任务详情（模板）
    elif uri.startswith("edict://task/"):
        task_id = uri.replace("edict://task/", "")
        task = await client.get_task(task_id)
        return {
            "content": task.model_dump_json(indent=2),
            "mime_type": "application/json"
        }
    
    # Agent 详情（模板）
    elif uri.startswith("edict://agent/"):
        agent_id = uri.replace("edict://agent/", "")
        agent = await client.get_agent(agent_id)
        return {
            "content": agent.model_dump_json(indent=2),
            "mime_type": "application/json"
        }
    
    else:
        raise ValueError(f"Unknown resource: {uri}")
