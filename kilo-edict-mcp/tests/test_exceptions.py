"""
异常模块测试

测试自定义异常类
"""

import pytest
from edict_mcp.exceptions import (
    EdictError,
    EdictAPIError,
    EdictConnectionError,
    EdictTimeoutError,
    EdictTaskNotFoundError,
    EdictAgentNotFoundError,
    EdictInvalidTransitionError,
    EdictValidationError,
    EdictWebSocketError,
    EdictWebSocketClosedError,
)


class TestEdictError:
    """测试 EdictError 基类"""
    
    def test_error_message(self):
        """测试错误消息"""
        error = EdictError("测试错误")
        assert str(error) == "测试错误"
    
    def test_error_inheritance(self):
        """测试异常继承关系"""
        error = EdictError("基础错误")
        assert isinstance(error, Exception)


class TestEdictAPIError:
    """测试 EdictAPIError"""
    
    def test_api_error_creation(self):
        """测试 API 错误创建"""
        error = EdictAPIError("API 错误", status_code=500, response={"detail": "Server Error"})
        
        assert str(error) == "[500] API 错误"
        assert error.status_code == 500
        assert error.response["detail"] == "Server Error"
    
    def test_api_error_without_status(self):
        """测试无状态码的 API 错误"""
        error = EdictAPIError("API 错误")
        
        assert error.status_code == 0
        assert str(error) == "API 错误"


class TestEdictTaskNotFoundError:
    """测试 EdictTaskNotFoundError"""
    
    def test_task_not_found(self):
        """测试任务未找到错误"""
        error = EdictTaskNotFoundError("task-123")
        
        assert str(error) == "Task not found: task-123"
        assert error.task_id == "task-123"


class TestEdictAgentNotFoundError:
    """测试 EdictAgentNotFoundError"""
    
    def test_agent_not_found(self):
        """测试 Agent 未找到错误"""
        error = EdictAgentNotFoundError("agent-456")
        
        assert str(error) == "Agent not found: agent-456"
        assert error.agent_id == "agent-456"


class TestEdictInvalidTransitionError:
    """测试 EdictInvalidTransitionError"""
    
    def test_invalid_transition(self):
        """测试无效状态转换错误"""
        error = EdictInvalidTransitionError("Taizi", "Done")
        
        assert "Invalid transition" in str(error)
        assert error.from_state == "Taizi"
        assert error.to_state == "Done"


class TestEdictWebSocketClosedError:
    """测试 EdictWebSocketClosedError"""
    
    def test_websocket_closed(self):
        """测试 WebSocket 关闭错误"""
        error = EdictWebSocketClosedError(code=1000, reason="Normal closure")
        
        assert "WebSocket closed" in str(error)
        assert error.code == 1000
        assert error.reason == "Normal closure"


class TestExceptionHierarchy:
    """测试异常继承层次"""
    
    def test_all_exceptions_inherit_from_edict_error(self):
        """测试所有异常都继承自 EdictError"""
        exceptions = [
            EdictAPIError("test"),
            EdictConnectionError("test"),
            EdictTimeoutError("test"),
            EdictTaskNotFoundError("test"),
            EdictAgentNotFoundError("test"),
            EdictInvalidTransitionError("a", "b"),
            EdictValidationError("test"),
            EdictWebSocketError("test"),
            EdictWebSocketClosedError(),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, EdictError)
