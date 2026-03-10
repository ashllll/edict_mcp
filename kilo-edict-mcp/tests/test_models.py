"""
数据模型测试

测试 MCP 数据模型
"""

import pytest
from pydantic import ValidationError
from edict_mcp.models import (
    MCPTask,
    MCPAgent,
    MCPEvent,
    TaskState,
    TaskPriority,
    FlowLogEntry,
    ProgressLogEntry,
    TodoItem,
)


class TestMCPTask:
    """测试 MCPTask 模型"""
    
    def test_create_task(self):
        """测试创建任务"""
        task = MCPTask(
            id="task-123",
            title="测试任务",
            description="这是一个测试任务",
            state=TaskState.TAIZI,
            priority=TaskPriority.MEDIUM,
        )
        
        assert task.id == "task-123"
        assert task.title == "测试任务"
        assert task.state == TaskState.TAIZI
        assert task.priority == TaskPriority.MEDIUM
    
    def test_task_with_logs(self):
        """测试带日志的任务"""
        task = MCPTask(
            id="task-456",
            title="带日志的任务",
            state=TaskState.DOING,
            flow_log=[
                FlowLogEntry(
                    from_state="Taizi",
                    to_state="Zhongshu",
                    agent="system",
                    reason="自动流转",
                    timestamp="2024-01-01T00:00:00Z"
                )
            ],
            progress_log=[
                ProgressLogEntry(
                    agent="agent-1",
                    message="开始处理",
                    timestamp="2024-01-01T00:01:00Z"
                )
            ],
        )
        
        assert len(task.flow_log) == 1
        assert len(task.progress_log) == 1
        assert task.flow_log[0].from_state == "Taizi"
    
    def test_task_with_todos(self):
        """测试带子任务的任务"""
        task = MCPTask(
            id="task-789",
            title="带子任务的任务",
            state=TaskState.DOING,
            todos=[
                TodoItem(id="todo-1", content="子任务1", done=False),
                TodoItem(id="todo-2", content="子任务2", done=True),
            ],
        )
        
        assert len(task.todos) == 2
        assert task.todos[0].done is False
        assert task.todos[1].done is True


class TestMCPAgent:
    """测试 MCPAgent 模型"""
    
    def test_create_agent(self):
        """测试创建 Agent"""
        agent = MCPAgent(
            id="agent-001",
            name="中书省",
            role="起草诏令",
            department="中书省",
            status="idle",
        )
        
        assert agent.id == "agent-001"
        assert agent.name == "中书省"
        assert agent.status == "idle"
    
    def test_agent_with_skills(self):
        """测试带技能的 Agent"""
        agent = MCPAgent(
            id="agent-002",
            name="门下省",
            skills=["审核", "封驳", "签署"],
        )
        
        assert len(agent.skills) == 3
        assert "审核" in agent.skills


class TestMCPEvent:
    """测试 MCPEvent 模型"""
    
    def test_create_event(self):
        """测试创建事件"""
        event = MCPEvent(
            id="event-001",
            topic="task_created",
            task_id="task-123",
            data={"title": "测试任务"},
            timestamp="2024-01-01T00:00:00Z",
        )
        
        assert event.id == "event-001"
        assert event.topic == "task_created"
        assert event.task_id == "task-123"


class TestEnums:
    """测试枚举类型"""
    
    def test_task_state_values(self):
        """测试任务状态枚举值"""
        assert TaskState.TAIZI.value == "Taizi"
        assert TaskState.ZHONGSHU.value == "Zhongshu"
        assert TaskState.MENXIA.value == "Menxia"
        assert TaskState.DONE.value == "Done"
        assert TaskState.CANCELLED.value == "Cancelled"
    
    def test_task_priority_values(self):
        """测试任务优先级枚举值"""
        assert TaskPriority.LOW.value == "低"
        assert TaskPriority.MEDIUM.value == "中"
        assert TaskPriority.HIGH.value == "高"
        assert TaskPriority.URGENT.value == "紧急"
