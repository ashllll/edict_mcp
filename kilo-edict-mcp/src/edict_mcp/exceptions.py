"""
自定义异常模块

定义 Edict MCP 集成所需的异常类型
"""


class EdictError(Exception):
    """Edict 基础异常类"""
    pass


class EdictAPIError(EdictError):
    """Edict API 异常
    
    当 Edict API 返回错误响应时抛出
    """
    def __init__(self, message: str, status_code: int = 0, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}
    
    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {super().__str__()}"
        return super().__str__()


class EdictConnectionError(EdictError):
    """Edict 连接异常
    
    当无法连接到 Edict API 时抛出
    """
    pass


class EdictTimeoutError(EdictError):
    """Edict 超时异常
    
    当请求 Edict API 超时时抛出
    """
    pass


class EdictTaskNotFoundError(EdictError):
    """任务不存在异常
    
    当请求的任务 ID 不存在时抛出
    """
    def __init__(self, task_id: str):
        super().__init__(f"Task not found: {task_id}")
        self.task_id = task_id


class EdictAgentNotFoundError(EdictError):
    """Agent 不存在异常
    
    当请求的 Agent ID 不存在时抛出
    """
    def __init__(self, agent_id: str):
        super().__init__(f"Agent not found: {agent_id}")
        self.agent_id = agent_id


class EdictInvalidTransitionError(EdictError):
    """无效状态流转异常
    
    当尝试无效的状态流转时抛出
    """
    def __init__(self, from_state: str, to_state: str):
        super().__init__(f"Invalid transition: {from_state} -> {to_state}")
        self.from_state = from_state
        self.to_state = to_state


class EdictValidationError(EdictError):
    """数据验证异常
    
    当输入数据验证失败时抛出
    """
    pass


class EdictWebSocketError(EdictError):
    """WebSocket 异常
    
    当 WebSocket 连接或通信出错时抛出
    """
    pass


class EdictWebSocketClosedError(EdictWebSocketError):
    """WebSocket 关闭异常
    
    当 WebSocket 连接被关闭时抛出
    """
    def __init__(self, code: int = 0, reason: str = ""):
        super().__init__(f"WebSocket closed: {code} - {reason}")
        self.code = code
        self.reason = reason
