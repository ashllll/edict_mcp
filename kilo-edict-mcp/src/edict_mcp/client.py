"""
EdictClient 模块

封装与 Edict 后端 API 的所有交互
"""

import asyncio
import logging
from typing import Any, Optional
import httpx

from edict_mcp.config import EdictConfig, get_config
from edict_mcp.models import (
    MCPTask,
    MCPAgent,
    MCPEvent,
    MCPStreamInfo,
    SystemStatus,
    CreateTaskRequest,
    TransitionTaskRequest,
    DispatchTaskRequest,
    AddProgressRequest,
    UpdateTodosRequest,
)
from edict_mcp.exceptions import (
    EdictAPIError,
    EdictConnectionError,
    EdictTimeoutError,
    EdictTaskNotFoundError,
    EdictAgentNotFoundError,
    EdictInvalidTransitionError,
)

logger = logging.getLogger(__name__)


class EdictClient:
    """Edict API 客户端
    
    封装与 Edict FastAPI 后端的所有 HTTP 交互
    """
    
    def __init__(self, config: Optional[EdictConfig] = None):
        """初始化 EdictClient
        
        Args:
            config: EdictConfig 配置实例，默认使用全局配置
        """
        self.config = config or get_config()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.api_base_url,
                timeout=self.config.api_timeout,
            )
        return self._client
    
    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        await self._get_client()  # 初始化 HTTP 客户端
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # ==================== 任务管理 ====================
    
    async def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "中",
        creator: str = "mcp-client",
    ) -> MCPTask:
        """创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            priority: 优先级
            creator: 创建者
            
        Returns:
            MCPTask: 创建的任务对象
        """
        request = CreateTaskRequest(
            title=title,
            description=description,
            priority=priority,
            creator=creator,
        )
        
        response = await self._request(
            "POST",
            "/api/tasks",
            json=request.model_dump(exclude_none=True),
        )
        
        return self._parse_task(response)
    
    async def get_task(self, task_id: str) -> MCPTask:
        """获取任务详情
        
        Args:
            task_id: 任务 ID
            
        Returns:
            MCPTask: 任务对象
        """
        response = await self._request(
            "GET",
            f"/api/tasks/{task_id}",
        )
        
        if response.get("error") == "Task not found":
            raise EdictTaskNotFoundError(task_id)
        
        return self._parse_task(response)
    
    async def list_tasks(
        self,
        state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MCPTask]:
        """获取任务列表
        
        Args:
            state: 按状态过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            list[MCPTask]: 任务列表
        """
        params = {"limit": limit, "offset": offset}
        if state:
            params["state"] = state
        
        response = await self._request(
            "GET",
            "/api/tasks",
            params=params,
        )
        
        tasks = response if isinstance(response, list) else response.get("tasks", [])
        return [self._parse_task(task) for task in tasks]
    
    async def delete_task(self, task_id: str) -> bool:
        """删除任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否删除成功
        """
        await self._request(
            "DELETE",
            f"/api/tasks/{task_id}",
        )
        return True
    
    async def transition_task(
        self,
        task_id: str,
        new_state: str,
        agent: str = "mcp-client",
        reason: str = "",
    ) -> MCPTask:
        """转换任务状态
        
        Args:
            task_id: 任务 ID
            new_state: 目标状态
            agent: 操作代理
            reason: 转换原因
            
        Returns:
            MCPTask: 转换后的任务对象
        """
        request = TransitionTaskRequest(
            new_state=new_state,
            agent=agent,
            reason=reason,
        )
        
        try:
            response = await self._request(
                "POST",
                f"/api/tasks/{task_id}/transition",
                json=request.model_dump(exclude_none=True),
            )
            return self._parse_task(response)
        except EdictAPIError as e:
            if "Invalid transition" in str(e):
                raise EdictInvalidTransitionError(
                    await self._get_task_state(task_id),
                    new_state,
                )
            raise
    
    async def dispatch_task(
        self,
        task_id: str,
        agent_id: str,
        instruction: str = "",
    ) -> MCPTask:
        """派发任务到 Agent
        
        Args:
            task_id: 任务 ID
            agent_id: 目标 Agent ID
            instruction: 派发指令
            
        Returns:
            MCPTask: 派发后的任务对象
        """
        request = DispatchTaskRequest(
            agent_id=agent_id,
            instruction=instruction,
        )
        
        response = await self._request(
            "POST",
            f"/api/tasks/{task_id}/dispatch",
            json=request.model_dump(exclude_none=True),
        )
        
        return self._parse_task(response)
    
    async def add_progress(
        self,
        task_id: str,
        message: str,
        agent: str = "mcp-client",
    ) -> MCPTask:
        """添加任务进度
        
        Args:
            task_id: 任务 ID
            message: 进度消息
            agent: 操作代理
            
        Returns:
            MCPTask: 更新后的任务对象
        """
        request = AddProgressRequest(
            agent=agent,
            message=message,
        )
        
        response = await self._request(
            "POST",
            f"/api/tasks/{task_id}/progress",
            json=request.model_dump(exclude_none=True),
        )
        
        return self._parse_task(response)
    
    async def update_todos(
        self,
        task_id: str,
        todos: list[dict[str, Any]],
    ) -> MCPTask:
        """更新任务子任务
        
        Args:
            task_id: 任务 ID
            todos: 子任务列表
            
        Returns:
            MCPTask: 更新后的任务对象
        """
        request = UpdateTodosRequest(todos=todos)
        
        response = await self._request(
            "PUT",
            f"/api/tasks/{task_id}/todos",
            json=request.model_dump(exclude_none=True),
        )
        
        return self._parse_task(response)
    
    # ==================== Agent 管理 ====================
    
    async def list_agents(self) -> list[MCPAgent]:
        """获取 Agent 列表
        
        Returns:
            list[MCPAgent]: Agent 列表
        """
        response = await self._request(
            "GET",
            "/api/agents",
        )
        
        agents = response if isinstance(response, list) else response.get("agents", [])
        return [self._parse_agent(agent) for agent in agents]
    
    async def get_agent(self, agent_id: str) -> MCPAgent:
        """获取 Agent 详情
        
        Args:
            agent_id: Agent ID
            
        Returns:
            MCPAgent: Agent 对象
        """
        response = await self._request(
            "GET",
            f"/api/agents/{agent_id}",
        )
        
        if response.get("error") == "Agent not found":
            raise EdictAgentNotFoundError(agent_id)
        
        return self._parse_agent(response)
    
    async def get_agent_config(self, agent_id: str) -> dict[str, Any]:
        """获取 Agent 配置
        
        Args:
            agent_id: Agent ID
            
        Returns:
            dict: Agent 配置信息
        """
        response = await self._request(
            "GET",
            f"/api/agents/{agent_id}/config",
        )
        return response
    
    # ==================== 事件查询 ====================
    
    async def list_events(
        self,
        topic: Optional[str] = None,
        task_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[MCPEvent]:
        """获取事件列表
        
        Args:
            topic: 事件主题过滤
            task_id: 任务 ID 过滤
            limit: 返回数量限制
            
        Returns:
            list[MCPEvent]: 事件列表
        """
        params = {"limit": limit}
        if topic:
            params["topic"] = topic
        if task_id:
            params["task_id"] = task_id
        
        response = await self._request(
            "GET",
            "/api/events",
            params=params,
        )
        
        events = response if isinstance(response, list) else response.get("events", [])
        return [self._parse_event(event) for event in events]
    
    async def list_topics(self) -> list[str]:
        """获取事件主题列表
        
        Returns:
            list[str]: 主题列表
        """
        response = await self._request(
            "GET",
            "/api/events/topics",
        )
        
        if isinstance(response, list):
            return response
        return response.get("topics", [])
    
    async def get_stream_info(self, topic: str = "task_events") -> MCPStreamInfo:
        """获取 Stream 信息
        
        Args:
            topic: Stream 主题
            
        Returns:
            MCPStreamInfo: Stream 信息
        """
        response = await self._request(
            "GET",
            "/api/events/stream-info",
            params={"topic": topic},
        )
        
        return MCPStreamInfo(**response)
    
    # ==================== 系统状态 ====================
    
    async def get_system_status(self) -> SystemStatus:
        """获取系统状态
        
        Returns:
            SystemStatus: 系统状态
        """
        try:
            response = await self._request(
                "GET",
                "/api/tasks/live-status",
            )
            
            return SystemStatus(
                version="0.1.0",
                api_status="healthy",
                tasks_total=response.get("total_tasks", 0),
                tasks_by_state=response.get("tasks_by_state", {}),
                agents_total=response.get("total_agents", 0),
            )
        except Exception as e:
            logger.warning(f"Failed to get system status: {e}")
            return SystemStatus(
                api_status="unhealthy",
            )
    
    # ==================== 私有方法 ====================
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> dict[str, Any]:
        """发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            path: 请求路径
            **kwargs: 其他请求参数
            
        Returns:
            dict: 响应数据
            
        Raises:
            EdictConnectionError: 连接错误
            EdictTimeoutError: 超时错误
            EdictAPIError: API 错误
        """
        client = await self._get_client()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await client.request(method, path, **kwargs)
                
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise EdictAPIError(
                        message=error_data.get("detail", error_data.get("error", "Unknown error")),
                        status_code=response.status_code,
                        response=error_data,
                    )
                
                return response.json() if response.content else {}
                
            except httpx.ConnectError as e:
                if attempt < self.config.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise EdictConnectionError(f"Failed to connect to Edict API: {e}")
            
            except httpx.TimeoutException as e:
                if attempt < self.config.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise EdictTimeoutError(f"Request to Edict API timed out: {e}")
    
    async def _get_task_state(self, task_id: str) -> str:
        """获取任务当前状态"""
        task = await self.get_task(task_id)
        return task.state
    
    def _parse_task(self, data: dict[str, Any]) -> MCPTask:
        """解析任务数据"""
        # 处理 flow_log
        if "flow_log" not in data:
            data["flow_log"] = []
        
        # 处理 progress_log
        if "progress_log" not in data:
            data["progress_log"] = []
        
        # 处理 todos
        if "todos" not in data:
            data["todos"] = []
        
        return MCPTask(**data)
    
    def _parse_agent(self, data: dict[str, Any]) -> MCPAgent:
        """解析 Agent 数据"""
        return MCPAgent(**data)
    
    def _parse_event(self, data: dict[str, Any]) -> MCPEvent:
        """解析事件数据"""
        return MCPEvent(**data)
