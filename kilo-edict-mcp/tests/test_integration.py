"""
集成测试

测试 MCP 协议兼容性和 Edict 集成
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from edict_mcp.config import EdictConfig
from edict_mcp.client import EdictClient
from edict_mcp.models import MCPTask, MCPAgent, TaskState
from edict_mcp.tools.tasks import (
    handle_create_task,
    handle_get_task,
    handle_list_tasks,
)
from edict_mcp.tools.agents import handle_list_agents
from edict_mcp.tools.events import handle_list_events
from edict_mcp.prompts.templates import handle_get_prompt
from edict_mcp.resources.status import handle_read_resource as handle_resource_read


class TestToolIntegration:
    """测试工具集成"""
    
    @pytest.fixture
    def mock_client(self):
        """创建模拟的 EdictClient"""
        client = MagicMock(spec=EdictClient)
        return client
    
    @pytest.mark.asyncio
    async def test_create_task_handler(self, mock_client):
        """测试创建任务处理器"""
        # 模拟返回
        mock_task = MCPTask(
            id="task-001",
            title="测试任务",
            state=TaskState.TAIZI,
        )
        mock_client.create_task = AsyncMock(return_value=mock_task)
        
        # 执行
        result = await handle_create_task(
            mock_client,
            {"title": "测试任务", "description": "测试描述"}
        )
        
        # 验证
        assert len(result) == 1
        assert "测试任务" in result[0].text
        mock_client.create_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_task_handler(self, mock_client):
        """测试获取任务处理器"""
        mock_task = MCPTask(
            id="task-001",
            title="测试任务",
            state=TaskState.TAIZI,
        )
        mock_client.get_task = AsyncMock(return_value=mock_task)
        
        result = await handle_get_task(mock_client, {"task_id": "task-001"})
        
        assert len(result) == 1
        assert "task-001" in result[0].text
        mock_client.get_task.assert_called_once_with("task-001")
    
    @pytest.mark.asyncio
    async def test_list_tasks_handler(self, mock_client):
        """测试任务列表处理器"""
        mock_tasks = [
            MCPTask(id="task-001", title="任务1", state=TaskState.TAIZI),
            MCPTask(id="task-002", title="任务2", state=TaskState.DOING),
        ]
        mock_client.list_tasks = AsyncMock(return_value=mock_tasks)
        
        result = await handle_list_tasks(mock_client, {})
        
        assert len(result) == 1
        assert "2" in result[0].text
        assert "任务1" in result[0].text
        assert "任务2" in result[0].text
    
    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, mock_client):
        """测试空任务列表"""
        mock_client.list_tasks = AsyncMock(return_value=[])
        
        result = await handle_list_tasks(mock_client, {})
        
        assert len(result) == 1
        assert "没有找到任务" in result[0].text


class TestAgentIntegration:
    """测试 Agent 集成"""
    
    @pytest.fixture
    def mock_client(self):
        client = MagicMock(spec=EdictClient)
        return client
    
    @pytest.mark.asyncio
    async def test_list_agents_handler(self, mock_client):
        """测试 Agent 列表处理器"""
        mock_agents = [
            MCPAgent(id="agent-001", name="中书省", status="idle"),
            MCPAgent(id="agent-002", name="门下省", status="busy"),
        ]
        mock_client.list_agents = AsyncMock(return_value=mock_agents)
        
        result = await handle_list_agents(mock_client, {})
        
        assert len(result) == 1
        assert "2" in result[0].text
        assert "中书省" in result[0].text


class TestPromptIntegration:
    """测试 Prompt 集成"""
    
    @pytest.fixture
    def mock_client(self):
        client = MagicMock(spec=EdictClient)
        return client
    
    @pytest.mark.asyncio
    async def test_create_task_prompt(self, mock_client):
        """测试创建任务 Prompt"""
        result = await handle_get_prompt(
            mock_client,
            "create_task",
            {"title": "新任务", "description": "描述"}
        )
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert "新任务" in result["messages"][0]["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_task_status_prompt(self, mock_client):
        """测试任务状态 Prompt"""
        result = await handle_get_prompt(
            mock_client,
            "task_status",
            {"task_id": "task-123"}
        )
        
        assert "messages" in result
        assert "task-123" in result["messages"][0]["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_list_agents_prompt(self, mock_client):
        """测试 Agent 列表 Prompt"""
        result = await handle_get_prompt(mock_client, "list_agents", {})
        
        assert "messages" in result
        assert "list_agents" in result["messages"][0]["content"]["text"]


class TestResourceIntegration:
    """测试 Resource 集成"""
    
    @pytest.fixture
    def mock_client(self):
        client = MagicMock(spec=EdictClient)
        return client
    
    @pytest.mark.asyncio
    async def test_system_status_resource(self, mock_client):
        """测试系统状态 Resource"""
        from edict_mcp.models import SystemStatus
        
        mock_status = SystemStatus(
            version="0.1.0",
            api_status="healthy",
            tasks_total=10,
            agents_total=5,
        )
        mock_client.get_system_status = AsyncMock(return_value=mock_status)
        
        result = await handle_resource_read(mock_client, "edict://system/status")
        
        assert "content" in result
        assert "application/json" in result["mime_type"]
        data = json.loads(result["content"])
        assert data["version"] == "0.1.0"
    
    @pytest.mark.asyncio
    async def test_agents_list_resource(self, mock_client):
        """测试 Agent 列表 Resource"""
        mock_agents = [
            MCPAgent(id="agent-001", name="中书省"),
        ]
        mock_client.list_agents = AsyncMock(return_value=mock_agents)
        
        result = await handle_resource_read(mock_client, "edict://agents/list")
        
        assert "content" in result
        agents = json.loads(result["content"])
        assert len(agents) == 1
        assert agents[0]["name"] == "中书省"


class TestEdictClient:
    """测试 EdictClient"""
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """测试客户端上下文管理器"""
        config = EdictConfig(api_url="http://localhost:8000")
        
        async with EdictClient(config) as client:
            assert client._client is not None
        
        # 上下文管理器退出后应该关闭客户端
        # 注意：由于我们使用 mock，这里只验证逻辑
    
    def test_client_url_helpers(self):
        """测试客户端 URL 辅助方法"""
        config = EdictConfig(api_url="http://localhost:8000")
        client = EdictClient(config)
        
        assert client.config.get_tasks_url() == "http://localhost:8000/api/tasks"
        assert client.config.get_task_url("123") == "http://localhost:8000/api/tasks/123"
        assert client.config.get_agents_url() == "http://localhost:8000/api/agents"


class TestErrorHandling:
    """测试错误处理"""
    
    @pytest.fixture
    def mock_client(self):
        client = MagicMock(spec=EdictClient)
        return client
    
    @pytest.mark.asyncio
    async def test_task_not_found_error(self, mock_client):
        """测试任务未找到错误"""
        from edict_mcp.exceptions import EdictTaskNotFoundError
        
        mock_client.get_task = AsyncMock(
            side_effect=EdictTaskNotFoundError("task-999")
        )
        
        result = await handle_get_task(mock_client, {"task_id": "task-999"})
        
        assert len(result) == 1
        assert "不存在" in result[0].text
        assert "task-999" in result[0].text
