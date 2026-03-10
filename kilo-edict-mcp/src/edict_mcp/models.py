"""
数据模型模块

定义 MCP 集成所需的数据模型，与 Edict 后端数据模型对应
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskState(str, Enum):
    """任务状态枚举
    
    基于中国古代三省六部制度的任务流转状态
    """
    TAIZI = "Taizi"           # 太子分拣
    ZHONGSHU = "Zhongshu"     # 中书起草
    MENXIA = "Menxia"         # 门下审议
    ASSIGNED = "Assigned"      # 已派发
    NEXT = "Next"             # 待执行
    DOING = "Doing"           # 执行中
    REVIEW = "Review"         # 审查中
    DONE = "Done"             # 已完成
    BLOCKED = "Blocked"        # 已阻塞
    CANCELLED = "Cancelled"    # 已取消
    PENDING = "Pending"       # 待处理


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    URGENT = "紧急"


class FlowLogEntry(BaseModel):
    """流转日志条目"""
    from_state: str = Field(..., description="原状态")
    to_state: str = Field(..., description="新状态")
    agent: str = Field(..., description="操作代理")
    reason: str = Field(default="", description="流转原因")
    timestamp: str = Field(..., description="时间戳")


class ProgressLogEntry(BaseModel):
    """进度日志条目"""
    agent: str = Field(..., description="操作代理")
    message: str = Field(..., description="进度消息")
    timestamp: str = Field(..., description="时间戳")


class TodoItem(BaseModel):
    """子任务项"""
    id: str = Field(..., description="子任务 ID")
    content: str = Field(..., description="子任务内容")
    done: bool = Field(default=False, description="是否完成")


class MCPTask(BaseModel):
    """MCP 任务模型
    
    对应 Edict 后端的 Task 模型
    """
    id: str = Field(..., description="任务 ID")
    title: str = Field(..., description="任务标题")
    description: str = Field(default="", description="任务描述")
    state: TaskState = Field(..., description="任务状态")
    org: str = Field(default="", description="当前部门")
    official: str = Field(default="", description="责任官员")
    now: str = Field(default="", description="当前进展")
    eta: str = Field(default="", description="预计完成时间")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="优先级")
    creator: str = Field(default="", description="创建者")
    flow_log: list[FlowLogEntry] = Field(default_factory=list, description="流转日志")
    progress_log: list[ProgressLogEntry] = Field(default_factory=list, description="进度日志")
    todos: list[TodoItem] = Field(default_factory=list, description="子任务清单")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")
    
    class Config:
        use_enum_values = True


class MCPAgent(BaseModel):
    """MCP Agent 模型
    
    对应 Edict 后端的 Agent 配置
    """
    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent 名称")
    description: str = Field(default="", description="Agent 描述")
    role: str = Field(default="", description="Agent 角色")
    department: str = Field(default="", description="所属部门")
    skills: list[str] = Field(default_factory=list, description="技能列表")
    model: str = Field(default="", description="使用模型")
    status: str = Field(default="idle", description="状态")
    stats: dict[str, Any] = Field(default_factory=dict, description="统计数据")
    config: dict[str, Any] = Field(default_factory=dict, description="配置信息")


class MCPEvent(BaseModel):
    """MCP 事件模型
    
    对应 Edict 后端的事件模型
    """
    id: str = Field(..., description="事件 ID")
    topic: str = Field(..., description="事件主题")
    task_id: Optional[str] = Field(default=None, description="关联任务 ID")
    agent: Optional[str] = Field(default=None, description="关联 Agent")
    data: dict[str, Any] = Field(default_factory=dict, description="事件数据")
    timestamp: str = Field(..., description="时间戳")


class MCPStreamInfo(BaseModel):
    """Redis Stream 信息"""
    name: str = Field(..., description="Stream 名称")
    first_entry_id: str = Field(..., description="首条消息 ID")
    last_entry_id: str = Field(..., description="最后消息 ID")
    entries_count: int = Field(..., description="消息数量")
    consumers: list[dict[str, Any]] = Field(default_factory=list, description="消费者信息")


class MCPResource(BaseModel):
    """MCP Resource 模型"""
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource 名称")
    description: str = Field(default="", description="Resource 描述")
    mime_type: str = Field(default="application/json", description="MIME 类型")
    data: Any = Field(..., description="Resource 数据")


class MCPTool(BaseModel):
    """MCP Tool 模型"""
    name: str = Field(..., description="Tool 名称")
    description: str = Field(..., description="Tool 描述")
    input_schema: dict[str, Any] = Field(..., description="输入模式")


class SystemStatus(BaseModel):
    """系统状态模型"""
    version: str = Field(default="0.1.0", description="版本")
    api_status: str = Field(default="unknown", description="API 状态")
    db_status: str = Field(default="unknown", description="数据库状态")
    redis_status: str = Field(default="unknown", description="Redis 状态")
    tasks_total: int = Field(default=0, description="总任务数")
    tasks_by_state: dict[str, int] = Field(default_factory=dict, description="各状态任务数")
    agents_total: int = Field(default=0, description="总 Agent 数")
    uptime: str = Field(default="", description="运行时间")


# API 请求/响应模型

class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    title: str = Field(..., description="任务标题")
    description: str = Field(default="", description="任务描述")
    priority: str = Field(default="中", description="优先级")
    creator: str = Field(default="mcp-client", description="创建者")


class TransitionTaskRequest(BaseModel):
    """状态流转请求"""
    new_state: str = Field(..., description="新状态")
    agent: str = Field(default="mcp-client", description="操作代理")
    reason: str = Field(default="", description="流转原因")


class DispatchTaskRequest(BaseModel):
    """任务派发请求"""
    agent_id: str = Field(..., description="目标 Agent ID")
    instruction: str = Field(default="", description="派发指令")


class AddProgressRequest(BaseModel):
    """添加进度请求"""
    agent: str = Field(default="mcp-client", description="操作代理")
    message: str = Field(..., description="进度消息")


class UpdateTodosRequest(BaseModel):
    """更新子任务请求"""
    todos: list[dict[str, Any]] = Field(..., description="子任务列表")
