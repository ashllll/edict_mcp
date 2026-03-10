# Docker + Skill 方式接入 Edict 实施计划

## 架构设计理念

采用**完全解耦**的架构：
1. **Edict 服务**：以 Docker 容器独立运行，提供标准 REST API
2. **Skill 项目**：独立 MCP Server/Tool 封装，作为 Edict 的客户端
3. **Kilo Code**：通过 Skill 调用 Edict 全部功能

```mermaid
flowchart TB
    subgraph KiloCode["Kilo Code 环境"]
        Agent[Kilo Code Agent]
        MCP[MCP Client]
    end
    
    subgraph SkillProject["Skill 项目<br/>edict-skill"]
        MCPServer[MCP Server]
        Tools[Edict Tools]
        APIClient[Edict API Client]
    end
    
    subgraph Docker["Docker 环境"]
        EdictContainer[Edict 容器<br/>cft0808/edict]
        Postgres[(PostgreSQL)]
        Redis[(Redis)]
    end
    
    Agent --> MCP
    MCP -->|stdio| MCPServer
    MCPServer --> Tools
    Tools --> APIClient
    APIClient -->|HTTP| EdictContainer
    EdictContainer --> Postgres
    EdictContainer --> Redis
```

---

## 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **Docker + Skill** | 完全解耦、独立升级、多实例支持 | 需要维护两个项目 | ✅ 推荐方案 |
| 直接集成 | 架构简单、调用直接 | 耦合度高、难以升级 | 快速原型 |
| 修改 Edict 源码 | 深度定制 | 维护成本高 | 深度定制需求 |

---

## 实施步骤

### 阶段一：Docker 部署 Edict

#### 1.1 准备 Docker 环境
- [ ] 确认 Docker 和 Docker Compose 已安装
- [ ] 创建项目目录 `edict-docker-stack/`

#### 1.2 创建 Docker Compose 配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  edict:
    image: cft0808/edict:latest
    ports:
      - "7891:7891"
    environment:
      - EDICT_API_PORT=7891
      - DATABASE_URL=postgresql://edict:edict@postgres:5432/edict
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - edict_data:/app/data
      
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=edict
      - POSTGRES_PASSWORD=edict
      - POSTGRES_DB=edict
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  edict_data:
  postgres_data:
  redis_data:
```

#### 1.3 启动 Edict 服务
```bash
cd edict-docker-stack
docker-compose up -d
```

#### 1.4 验证部署
- [ ] 访问 http://localhost:7891 确认看板正常
- [ ] 测试 API 端点：`curl http://localhost:7891/api/live-status`

---

### 阶段二：创建 Skill 项目

#### 2.1 Skill 项目结构
```
edict-skill/
├── src/
│   └── edict_skill/
│       ├── __init__.py
│       ├── server.py          # MCP Server 入口
│       ├── tools.py           # Edict Tools 定义
│       ├── client.py          # Edict API 客户端
│       └── models.py          # 数据模型
├── docker-compose.skill.yml   # Skill 容器配置（可选）
├── Dockerfile.skill           # Skill 容器镜像（可选）
├── pyproject.toml
├── README.md
└── tests/
```

#### 2.2 Skill 核心实现

**models.py** - 数据模型
```python
from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
from datetime import datetime

class TaskState(str, Enum):
    TAZI = "Taizi"
    ZHONGSHU = "Zhongshu"
    MENXIA = "Menxia"
    ASSIGNED = "Assigned"
    DOING = "Doing"
    REVIEW = "Review"
    DONE = "Done"
    BLOCKED = "Blocked"

class Task(BaseModel):
    id: str
    title: str
    description: str
    state: TaskState
    org: Optional[str]
    official: Optional[str]
    created_at: datetime
    updated_at: datetime
```

**client.py** - Edict API 客户端
```python
import httpx
from typing import Optional, List
from .models import Task, TaskState

class EdictClient:
    """Edict API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:7891"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30)
    
    async def create_task(self, title: str, description: str = "") -> Task:
        """创建新任务"""
        response = await self.client.post(
            f"{self.base_url}/api/tasks",
            json={"title": title, "description": description}
        )
        response.raise_for_status()
        return Task(**response.json())
    
    async def get_task(self, task_id: str) -> Task:
        """获取任务详情"""
        response = await self.client.get(f"{self.base_url}/api/tasks/{task_id}")
        response.raise_for_status()
        return Task(**response.json())
    
    async def list_tasks(self, state: Optional[str] = None) -> List[Task]:
        """列出任务"""
        params = {"state": state} if state else {}
        response = await self.client.get(
            f"{self.base_url}/api/tasks",
            params=params
        )
        response.raise_for_status()
        return [Task(**t) for t in response.json()]
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        response = await self.client.post(
            f"{self.base_url}/api/tasks/{task_id}/cancel"
        )
        return response.status_code == 200
```

**tools.py** - MCP Tools 定义
```python
from mcp.server import Server
from mcp.types import TextContent
from .client import EdictClient
from .models import TaskState

class EdictTools:
    """Edict Skill Tools"""
    
    def __init__(self, edict_url: str = "http://localhost:7891"):
        self.client = EdictClient(edict_url)
    
    async def create_task(self, title: str, description: str = "") -> str:
        """
        在 Edict 三省六部系统中创建新任务。
        
        任务创建后将进入太子分拣阶段，自动流转到：
        太子 → 中书省 → 门下省 → 尚书省 → 六部执行
        
        Args:
            title: 任务标题（必填）
            description: 任务描述，支持 Markdown
            
        Returns:
            任务创建结果，包含任务 ID 和状态
        """
        task = await self.client.create_task(title, description)
        return f"""
✅ 任务创建成功

📋 任务 ID: {task.id}
📌 标题: {task.title}
📊 状态: {task.state.value}
👤 当前负责人: {task.official or '待分配'}
🕐 创建时间: {task.created_at}

任务已进入太子分拣阶段，系统将自动流转到后续流程。
可通过 get_task 查询最新进展。
"""
    
    async def get_task(self, task_id: str) -> str:
        """
        查询任务详细信息和当前状态。
        
        Args:
            task_id: 任务 ID（如 EDCT-20260310-001）
            
        Returns:
            任务详情、状态、流转历史
        """
        task = await self.client.get_task(task_id)
        return f"""
📋 任务详情

ID: {task.id}
标题: {task.title}
状态: {task.state.value}
部门: {task.org or '-'}
负责人: {task.official or '-'}

📝 描述:
{task.description or '(无)'}

⏱️ 时间:
创建: {task.created_at}
更新: {task.updated_at}
"""
    
    async def list_tasks(self, state: str = None, limit: int = 10) -> str:
        """
        列出 Edict 系统中的任务。
        
        Args:
            state: 按状态过滤（Taizi/Zhongshu/Menxia/Assigned/Doing/Review/Done/Blocked）
            limit: 返回数量限制（默认 10）
            
        Returns:
            任务列表摘要
        """
        tasks = await self.client.list_tasks(state)
        tasks = tasks[:limit]
        
        if not tasks:
            return "暂无任务"
        
        lines = ["📋 任务列表\n"]
        for t in tasks:
            lines.append(f"• [{t.state.value:10}] {t.id}: {t.title[:40]}")
        
        return "\n".join(lines)
```

**server.py** - MCP Server 入口
```python
import asyncio
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent
from .tools import EdictTools

class EdictMCPServer:
    """Edict MCP Server"""
    
    def __init__(self):
        self.server = Server("edict-skill")
        self.edict_url = os.getenv("EDICT_URL", "http://localhost:7891")
        self.tools = EdictTools(self.edict_url)
        self._register_tools()
    
    def _register_tools(self):
        @self.server.call_tool()
        async def handle_tool(name: str, arguments: dict):
            if name == "create_task":
                result = await self.tools.create_task(
                    arguments["title"],
                    arguments.get("description", "")
                )
                return [TextContent(type="text", text=result)]
            
            elif name == "get_task":
                result = await self.tools.get_task(arguments["task_id"])
                return [TextContent(type="text", text=result)]
            
            elif name == "list_tasks":
                result = await self.tools.list_tasks(
                    arguments.get("state"),
                    arguments.get("limit", 10)
                )
                return [TextContent(type="text", text=result)]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
        
        @self.server.list_tools()
        async def list_tools():
            return [
                {
                    "name": "create_task",
                    "description": "在 Edict 系统中创建新任务",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "任务标题"},
                            "description": {"type": "string", "description": "任务描述"}
                        },
                        "required": ["title"]
                    }
                },
                {
                    "name": "get_task",
                    "description": "查询任务详情",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "任务 ID"}
                        },
                        "required": ["task_id"]
                    }
                },
                {
                    "name": "list_tasks",
                    "description": "列出任务",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string", "description": "状态过滤"},
                            "limit": {"type": "integer", "description": "数量限制"}
                        }
                    }
                }
            ]
    
    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

def main():
    server = EdictMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
```

---

### 阶段三：Kilo Code 配置

#### 3.1 安装 Skill
```bash
# 方式一：pip 安装（如果发布到 PyPI）
pip install edict-skill

# 方式二：本地安装
cd edict-skill
pip install -e .
```

#### 3.2 Kilo Code MCP 配置
在 Kilo Code 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "edict": {
      "command": "python",
      "args": ["-m", "edict_skill"],
      "env": {
        "EDICT_URL": "http://localhost:7891"
      }
    }
  }
}
```

#### 3.3 使用示例

**创建任务**
```
用户：帮我创建一个任务，分析这个项目的性能瓶颈

Kilo Code：
[调用 create_task]
- title: "分析项目性能瓶颈"
- description: "对当前项目进行全面的性能分析..."

✅ 任务创建成功
📋 任务 ID: EDCT-20260310-001
📌 标题: 分析项目性能瓶颈
📊 状态: Taizi
任务已进入太子分拣阶段...
```

**查询任务**
```
用户：查看任务 EDCT-20260310-001 的进展

Kilo Code：
[调用 get_task]

📋 任务详情
ID: EDCT-20260310-001
标题: 分析项目性能瓶颈
状态: Doing
部门: 兵部
负责人: bingbu

任务正在兵部执行中...
```

---

### 阶段四：扩展功能（可选）

#### 4.1 添加更多 Tools
- `transition_task` - 状态流转
- `dispatch_task` - 手动派发
- `cancel_task` - 取消任务
- `list_agents` - 列出 Agent
- `get_agent_status` - 查询 Agent 状态

#### 4.2 WebSocket 实时监听
```python
async def subscribe_task_events(task_id: str):
    """订阅任务实时事件"""
    async with websockets.connect(f"{WS_URL}/ws/task/{task_id}") as ws:
        async for message in ws:
            event = json.loads(message)
            yield event
```

#### 4.3 Skill 容器化（可选）
```dockerfile
# Dockerfile.skill
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

ENV EDICT_URL=http://edict:7891

CMD ["python", "-m", "edict_skill"]
```

---

## 部署架构

### 单机部署
```mermaid
flowchart LR
    KC[Kilo Code] -->|stdio| Skill[edict-skill]
    Skill -->|HTTP| Edict[Edict Docker]
    Edict --> Postgres[(Postgres)]
    Edict --> Redis[(Redis)]
```

### 分布式部署
```mermaid
flowchart LR
    subgraph Host1["主机 1"]
        KC[Kilo Code]
    end
    
    subgraph Host2["主机 2"]
        Skill[edict-skill]
    end
    
    subgraph Host3["主机 3 - Docker"]
        Edict[Edict]
        Postgres[(Postgres)]
        Redis[(Redis)]
    end
    
    KC -->|stdio| Skill
    Skill -->|HTTP| Edict
    Edict --> Postgres
    Edict --> Redis
```

---

## 验收清单

### 阶段一验收
- [ ] Docker Compose 能正常启动 Edict
- [ ] 看板可通过 http://localhost:7891 访问
- [ ] API 测试通过

### 阶段二验收
- [ ] Skill 项目结构完整
- [ ] MCP Server 能正常启动
- [ ] Tools 调用成功
- [ ] 单元测试通过

### 阶段三验收
- [ ] Kilo Code 配置成功
- [ ] 能成功创建任务
- [ ] 能查询任务状态
- [ ] 能列出任务列表

---

## 下一步行动

1. **确认方案**：审查此 Docker + Skill 方案
2. **开始实施**：按阶段逐步实施
3. **阶段一**：创建 Docker Compose 配置并部署 Edict
4. **阶段二**：创建 Skill 项目实现核心功能
5. **阶段三**：配置 Kilo Code 并测试

是否需要我开始实施第一阶段（Docker 部署）？