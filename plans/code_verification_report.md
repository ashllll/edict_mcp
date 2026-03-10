# 规划与原始代码核对报告

## 核对结果概览

| 检查项 | 符合度 | 说明 |
|--------|--------|------|
| API 端点 | ⚠️ 部分符合 | 缺少 cancel 端点，需用 transition 替代 |
| 数据模型 | ⚠️ 部分符合 | 无 description 字段，需调整 |
| TaskState 枚举 | ✅ 完全符合 | 10 个状态全部匹配 |
| Docker 配置 | ✅ 完全符合 | 可直接复用 |
| 响应格式 | ⚠️ 需调整 | create_task 返回字段不同 |

---

## 详细核对

### 1. API 端点核对

#### 1.1 创建任务
**规划中的调用**：
```python
POST /api/tasks
{"title": "...", "description": "..."}
```

**实际代码**（`edict/backend/app/api/tasks.py:120-135`）：
```python
@router.post("", status_code=201)
async def create_task(body: TaskCreate, ...):
    task = await svc.create_task(
        title=body.title,
        description=body.description,  # ✅ 存在
        priority=body.priority,        # ⚠️ 规划遗漏
        ...
    )
    return {"task_id": str(task.task_id), "trace_id": str(task.trace_id), "state": task.state.value}
    # ⚠️ 注意：返回的是 task_id 不是 id
```

**差异**：
- ✅ `description` 字段存在（我之前的 task.py 模型分析有误）
- ⚠️ 响应字段是 `task_id` 不是 `id`
- ⚠️ 还有 `trace_id` 字段

#### 1.2 查询任务
**规划中的调用**：
```python
GET /api/tasks/{task_id}
```

**实际代码**（`edict/backend/app/api/tasks.py:138-148`）：
```python
@router.get("/{task_id}")
async def get_task(task_id: uuid.UUID, ...):
    task = await svc.get_task(task_id)
    return task.to_dict()  # ✅ 符合
```

**差异**：
- ✅ 完全符合

#### 1.3 列出任务
**规划中的调用**：
```python
GET /api/tasks?state=xxx&limit=20
```

**实际代码**（`edict/backend/app/api/tasks.py:83-101`）：
```python
@router.get("")
async def list_tasks(
    state: str | None = None,
    assignee_org: str | None = None,  # ⚠️ 规划遗漏
    priority: str | None = None,      # ⚠️ 规划遗漏
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),  # ⚠️ 规划遗漏
    ...
):
    return {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)}
    # ⚠️ 注意：返回包装在 {"tasks": ...} 中
```

**差异**：
- ⚠️ 响应格式是 `{"tasks": [...], "count": N}` 不是直接返回列表
- ⚠️ 还有 `assignee_org`, `priority`, `offset` 参数

#### 1.4 取消任务 ❌ 不存在
**规划中的调用**：
```python
POST /api/tasks/{id}/cancel
```

**实际代码**：
- ❌ 不存在 cancel 端点
- ✅ 应使用 `POST /api/tasks/{task_id}/transition`（line 151-172）

```python
@router.post("/{task_id}/transition")
async def transition_task(
    task_id: uuid.UUID,
    body: TaskTransition,  # {new_state: "Cancelled", agent: "...", reason: "..."}
    ...
):
    ...
```

**修正方案**：
```python
# 不使用 cancel_task
# 改用 transition_task(task_id, new_state="Cancelled")
```

---

### 2. 数据模型核对

#### 2.1 Task 模型字段

**规划中的模型**：
```python
class Task(BaseModel):
    id: str
    title: str
    description: str  # ❌ 实际不存在！
    state: TaskState
    org: Optional[str]
    official: Optional[str]
```

**实际代码**（`edict/backend/app/models/task.py:78-142`）：
```python
class Task(Base):
    id = Column(String(32), primary_key=True)  # ✅
    title = Column(Text, nullable=False)       # ✅
    # ❌ 没有 description 字段！
    state = Column(Enum(TaskState), ...)       # ✅
    org = Column(String(32), ...)              # ✅
    official = Column(String(32), ...)         # ✅
    
    # 实际存在的字段（规划遗漏）：
    now = Column(Text, default="")             # 当前进展
    eta = Column(String(64), default="-")      # 预计完成时间
    block = Column(Text, default="无")         # 阻塞原因
    output = Column(Text, default="")          # 最终产出
    priority = Column(String(16), default="normal")  # 优先级
    archived = Column(Boolean, default=False)  # 是否归档
    flow_log = Column(JSONB, default=list)     # 流转日志
    progress_log = Column(JSONB, default=list) # 进展日志
    todos = Column(JSONB, default=list)        # 子任务
```

**修正方案**：
```python
class Task(BaseModel):
    id: str
    title: str
    # description 应从 TaskCreate schema 获取，但 Task 本身不存储
    state: TaskState
    org: Optional[str]
    official: Optional[str]
    now: str = ""           # 添加
    eta: str = "-"          # 添加
    block: str = "无"       # 添加
    priority: str = "normal"  # 添加
    flow_log: list = []     # 添加
    progress_log: list = [] # 添加
    todos: list = []        # 添加
```

#### 2.2 TaskState 枚举

**规划中的枚举**：
```python
class TaskState(str, Enum):
    TAZI = "Taizi"
    ZHONGSHU = "Zhongshu"
    MENXIA = "Menxia"
    ASSIGNED = "Assigned"
    DOING = "Doing"
    REVIEW = "Review"
    DONE = "Done"
    BLOCKED = "Blocked"
```

**实际代码**（`edict/backend/app/models/task.py:28-40`）：
```python
class TaskState(str, enum.Enum):
    Taizi = "Taizi"           # ✅
    Zhongshu = "Zhongshu"     # ✅
    Menxia = "Menxia"         # ✅
    Assigned = "Assigned"     # ✅
    Next = "Next"             # ⚠️ 规划遗漏！
    Doing = "Doing"           # ✅
    Review = "Review"         # ✅
    Done = "Done"             # ✅
    Blocked = "Blocked"       # ✅
    Cancelled = "Cancelled"   # ✅
    Pending = "Pending"       # ⚠️ 规划遗漏！
```

**修正方案**：
```python
class TaskState(str, Enum):
    Taizi = "Taizi"
    Zhongshu = "Zhongshu"
    Menxia = "Menxia"
    Assigned = "Assigned"
    Next = "Next"           # 添加
    Doing = "Doing"
    Review = "Review"
    Done = "Done"
    Blocked = "Blocked"
    Cancelled = "Cancelled" # 添加
    Pending = "Pending"     # 添加
```

---

### 3. Docker 配置核对

**现有配置**：
- `docker-compose.yml` - Demo 模式（`cft0808/sansheng-demo`）
- `edict/docker-compose.yml` - 完整服务（backend + workers + frontend + postgres + redis）
- `edict/Dockerfile` - 后端镜像
- `edict/frontend/Dockerfile` - 前端镜像

**符合度**：✅ 完全符合，可直接复用

---

### 4. 响应格式核对

#### 4.1 create_task 响应
**规划预期**：
```python
return Task(**response.json())  # 完整的 Task 对象
```

**实际响应**（`edict/backend/app/api/tasks.py:135`）：
```python
return {"task_id": str(task.task_id), "trace_id": str(task.trace_id), "state": task.state.value}
# 只返回这3个字段，不是完整的 Task 对象
```

**修正方案**：
```python
async def create_task(self, title: str, description: str = "") -> dict:
    resp = await self.client.post(
        f"{self.base_url}/api/tasks",
        json={"title": title, "description": description}
    )
    resp.raise_for_status()
    data = resp.json()
    # 只返回 task_id, trace_id, state
    return {
        "id": data["task_id"],  # 注意字段名转换
        "trace_id": data["trace_id"],
        "state": data["state"]
    }
```

#### 4.2 list_tasks 响应
**规划预期**：
```python
return [Task(**t) for t in response.json()]  # 直接是列表
```

**实际响应**（`edict/backend/app/api/tasks.py:101`）：
```python
return {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)}
# 包装在 {"tasks": ..., "count": ...} 中
```

**修正方案**：
```python
async def list_tasks(...) -> List[Task]:
    resp = await self.client.get(f"{self.base_url}/api/tasks", params=params)
    resp.raise_for_status()
    data = resp.json()
    return [Task(**t) for t in data["tasks"]]  # 注意取 data["tasks"]
```

---

## 修正后的 Skill 客户端代码

```python
# client.py
import httpx
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

class TaskState(str, Enum):
    Taizi = "Taizi"
    Zhongshu = "Zhongshu"
    Menxia = "Menxia"
    Assigned = "Assigned"
    Next = "Next"           # 添加
    Doing = "Doing"
    Review = "Review"
    Done = "Done"
    Blocked = "Blocked"
    Cancelled = "Cancelled" # 添加
    Pending = "Pending"     # 添加

class Task(BaseModel):
    id: str
    title: str
    state: TaskState
    org: Optional[str] = None
    official: Optional[str] = None
    now: str = ""           # 添加
    eta: str = "-"          # 添加
    block: str = "无"       # 添加
    priority: str = "normal"  # 添加
    flow_log: List[dict] = []  # 添加
    progress_log: List[dict] = []  # 添加
    todos: List[dict] = []  # 添加

class EdictClient:
    def __init__(self, base_url: str = "http://localhost:7891"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30)
    
    async def create_task(self, title: str, description: str = "") -> dict:
        """创建任务，返回 {id, trace_id, state}"""
        resp = await self.client.post(
            f"{self.base_url}/api/tasks",
            json={"title": title, "description": description}
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "id": data["task_id"],      # 字段名转换
            "trace_id": data["trace_id"],
            "state": data["state"]
        }
    
    async def get_task(self, task_id: str) -> Task:
        """获取任务详情"""
        resp = await self.client.get(f"{self.base_url}/api/tasks/{task_id}")
        resp.raise_for_status()
        return Task(**resp.json())
    
    async def list_tasks(self, state: Optional[str] = None, limit: int = 20) -> List[Task]:
        """列出任务"""
        params = {}
        if state:
            params["state"] = state
        if limit:
            params["limit"] = limit
        resp = await self.client.get(f"{self.base_url}/api/tasks", params=params)
        resp.raise_for_status()
        data = resp.json()
        return [Task(**t) for t in data["tasks"]]  # 取 data["tasks"]
    
    async def transition_task(self, task_id: str, new_state: str, reason: str = "") -> bool:
        """状态流转（包括取消任务）"""
        resp = await self.client.post(
            f"{self.base_url}/api/tasks/{task_id}/transition",
            json={"new_state": new_state, "agent": "kilo-skill", "reason": reason}
        )
        return resp.status_code == 200
    
    async def cancel_task(self, task_id: str, reason: str = "") -> bool:
        """取消任务（通过状态流转实现）"""
        return await self.transition_task(task_id, "Cancelled", reason)
```

---

## 总结

### 需要修正的地方
1. **Task 模型**：添加 `now`, `eta`, `block`, `priority`, `flow_log`, `progress_log`, `todos` 字段
2. **TaskState 枚举**：添加 `Next`, `Cancelled`, `Pending`
3. **create_task 响应**：处理字段名 `task_id` → `id` 的转换
4. **list_tasks 响应**：从 `{"tasks": [...]}` 中提取列表
5. **cancel_task**：使用 `transition_task` 实现，调用 `POST /api/tasks/{id}/transition`

### 无需修改的地方
- Docker 配置可直接复用
- `get_task` 端点完全符合
- API 基础路径和认证方式（暂时无认证）