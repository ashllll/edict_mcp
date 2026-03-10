"""
Prompt 模板

定义工作流模板的 MCP Prompts
"""

import logging
from typing import Any

from mcp.types import Prompt, PromptArgument
from mcp.server import Server

from edict_mcp.client import EdictClient

logger = logging.getLogger(__name__)


def get_prompts(server: Server, client: EdictClient) -> list[Prompt]:
    """获取所有 Prompts
    
    Args:
        server: MCP Server 实例
        client: EdictClient 实例
        
    Returns:
        list[Prompt]: Prompts 列表
    """
    return [
        Prompt(
            name="create_task",
            description="创建一个新任务并开始执行三省六部流程",
            arguments=[
                PromptArgument(
                    name="title",
                    description="任务标题",
                    required=True,
                ),
                PromptArgument(
                    name="description",
                    description="任务详细描述",
                    required=False,
                ),
                PromptArgument(
                    name="priority",
                    description="优先级：低/中/高/紧急",
                    required=False,
                ),
            ],
        ),
        Prompt(
            name="task_status",
            description="查询任务当前状态和完整进度",
            arguments=[
                PromptArgument(
                    name="task_id",
                    description="任务 ID",
                    required=True,
                ),
            ],
        ),
        Prompt(
            name="transition_task",
            description="将任务转换到下一个阶段",
            arguments=[
                PromptArgument(
                    name="task_id",
                    description="任务 ID",
                    required=True,
                ),
                PromptArgument(
                    name="new_state",
                    description="目标状态",
                    required=True,
                ),
                PromptArgument(
                    name="reason",
                    description="转换原因",
                    required=False,
                ),
            ],
        ),
        Prompt(
            name="dispatch_to_agent",
            description="将任务派发给指定的 Agent 执行",
            arguments=[
                PromptArgument(
                    name="task_id",
                    description="任务 ID",
                    required=True,
                ),
                PromptArgument(
                    name="agent_id",
                    description="Agent ID",
                    required=True,
                ),
                PromptArgument(
                    name="instruction",
                    description="派发指令",
                    required=False,
                ),
            ],
        ),
        Prompt(
            name="list_all_tasks",
            description="列出所有任务或按状态过滤",
            arguments=[
                PromptArgument(
                    name="state",
                    description="任务状态过滤",
                    required=False,
                ),
                PromptArgument(
                    name="limit",
                    description="返回数量限制",
                    required=False,
                ),
            ],
        ),
        Prompt(
            name="list_agents",
            description="列出所有可用的 Agent",
            arguments=[],
        ),
    ]


async def handle_get_prompt(
    client: EdictClient,
    name: str,
    arguments: dict[str, Any] | None,
) -> dict[str, Any]:
    """处理 Prompt 获取请求
    
    Args:
        client: EdictClient 实例
        name: Prompt 名称
        arguments: Prompt 参数
        
    Returns:
        dict: Prompt 内容，包含 messages
    """
    args = arguments or {}
    
    if name == "create_task":
        title = args.get("title", "")
        description = args.get("description", "")
        priority = args.get("priority", "中")
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""请帮我创建一个新任务：

标题：{title}
描述：{description}
优先级：{priority}

请使用 create_task 工具创建这个任务。"""
                    }
                }
            ]
        }
    
    elif name == "task_status":
        task_id = args.get("task_id", "")
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""请帮我查询任务 {task_id} 的当前状态和进度。

请使用 get_task 工具获取任务详情。"""
                    }
                }
            ]
        }
    
    elif name == "transition_task":
        task_id = args.get("task_id", "")
        new_state = args.get("new_state", "")
        reason = args.get("reason", "")
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""请将任务 {task_id} 转换到状态 {new_state}。

原因：{reason}

请使用 transition_task 工具执行状态转换。"""
                    }
                }
            ]
        }
    
    elif name == "dispatch_to_agent":
        task_id = args.get("task_id", "")
        agent_id = args.get("agent_id", "")
        instruction = args.get("instruction", "")
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""请将任务 {task_id} 派发给 Agent {agent_id}。

指令：{instruction}

请使用 dispatch_task 工具派发任务。"""
                    }
                }
            ]
        }
    
    elif name == "list_all_tasks":
        state = args.get("state", "")
        limit = args.get("limit", 100)
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""请帮我列出任务{'，状态为 ' + state if state else ''}。

请使用 list_tasks 工具，limit={limit}。"""
                    }
                }
            ]
        }
    
    elif name == "list_agents":
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": """请帮我列出所有可用的 Agent。

请使用 list_agents 工具。"""
                    }
                }
            ]
        }
    
    else:
        raise ValueError(f"Unknown prompt: {name}")
