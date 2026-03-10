# 深度代码核对报告 - 发现双 API 系统

## 重大发现：Edict 有两套 API

### 系统一：FastAPI 后端（端口 8000）
**代码位置**：`edict/backend/app/api/`
**存储**：PostgreSQL + Redis
**用途**：核心任务管理、事件驱动

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/tasks` | GET/POST | 任务列表/创建 |
| `/api/tasks/{id}` | GET | 任务详情 |
| `/api/tasks/{id}/transition` | POST | 状态流转 |
| `/api/tasks/{id}/dispatch` | POST | 派发任务 |
| `/api/agents` | GET | Agent 列表 |
| `/api/events` | GET | 事件查询 |

### 系统二：看板服务器（端口 7891）
**代码位置**：`dashboard/server.py`
**存储**：文件系统（data/tasks_source.json）
**用途**：看板 UI、人工干预、配置管理

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/create-task` | POST | 创建任务（格式不同） |
| `/api/task-action` | POST | stop/cancel/resume |
| `/api/review-action` | POST | approve/reject |
| `/api/advance-state` | POST | 推进状态 |
| `/api/agents-status` | GET | Agent 状态 |
| `/api/live-status` | GET | 实时状态 |

---

## 关键差异对比

### 1. 创建任务

**FastAPI（8000）**：
```python
POST /api/tasks
{"title": "...", "description": "...", "priority": "中"}

# 响应
{"task_id": "...", "trace_id": "...", "state": "Taizi"}
```

**看板服务器（7891）**：
```python
POST /api/create-task
{"title": "...", "org": "中书省", "official": "中书令", "priority": "normal"}

# 响应
{"ok": True, "taskId": "JJC-20260310-001", "message": "..."}
```

### 2. 任务 ID 格式

**FastAPI**：UUID（如 `550e8400-e29b-41d4-a716-446655440000`）
**看板服务器**：JJC 格式（如 `JJC-20260310-001`）

### 3. 状态流转

**FastAPI**：
```python
POST /api/tasks/{task_id}/transition
{"new_state": "Doing", "agent": "...", "reason": "..."}
```

**看板服务器**：
```python
POST /api/advance-state  # 自动推进到下一状态
{"taskId": "...", "comment": "..."}

POST /api/review-action  # 门下省审批
{"taskId": "...", "action": "approve/reject", "comment": "..."}
```

---

## Docker 配置分析

### Demo 模式（端口 7891）
```yaml
# docker-compose.yml
services:
  sansheng-demo:
    image: cft0808/sansheng-demo:latest
    ports:
      - "7891:7891"
```
- 这是**看板服务器**（文件存储）
- 使用 `dashboard/server.py`
- 数据存储在容器内的 `data/` 目录

### 完整模式（端口 8000 + 3000）
```yaml
# edict/docker-compose.yml
services:
  backend:
    ports:
      - "8000:8000"  # FastAPI
  frontend:
    ports:
      - "3000:3000"  # React
```
- FastAPI 后端（PostgreSQL + Redis）
- 需要额外的 workers（orchestrator + dispatcher）
- 数据持久化在 PostgreSQL

---

## 规划与代码的契合度分析

### ❌ 主要差异

| 规划假设 | 实际情况 | 影响 |
|----------|----------|------|
| 单一 API 系统 | 双 API 系统 | Skill 需要选择连接哪个端口 |
| 统一使用 UUID | 7891 使用 JJC 格式 | ID 格式处理需要兼容 |
| cancel_task 端点 | 不存在，需用 transition | 需要修正 API 调用 |
| 直接操作数据库 | 通过 API 操作 | 符合规划 |

### ⚠️ 需要决策的问题

**问题 1：Skill 应该连接哪个端口？**

选项 A：连接 8000（FastAPI）
- ✅ 标准 REST API
- ✅ 事件驱动架构
- ❌ 需要启动完整 Docker 套件（PostgreSQL + Redis + Workers）
- ❌ 配置复杂

选项 B：连接 7891（看板服务器）
- ✅ 单容器启动简单
- ✅ 有人工干预 API（stop/cancel/resume/advance）
- ❌ 非标准 REST（响应格式 `{ok: True/False}`）
- ❌ 功能受限（没有事件查询）

**推荐：选项 A（FastAPI 8000）**，理由：
1. 更标准的设计
2. 支持 WebSocket 实时事件
3. 与 Edict 架构文档描述一致
4. 更适合自动化集成

---

## 修正后的 Skill 设计

### 方案：连接 FastAPI（端口 8000）

```python
# client.py
class EdictClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30)
    
    async def create_task(self, title: str, description: str = "") -> dict:
        """创建任务"""
        resp = await self.client.post(
            f"{self.base_url}/api/tasks",
            json={
                "title": title,
                "description": description,
                "priority": "中",
                "creator": "kilo-skill"
            }
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "id": data["task_id"],      # 注意：字段名是 task_id
            "trace_id": data["trace_id"],
            "state": data["state"]
        }
    
    async def transition_task(
        self, 
        task_id: str, 
        new_state: str, 
        reason: str = ""
    ) -> bool:
        """状态流转（包括取消）"""
        resp = await self.client.post(
            f"{self.base_url}/api/tasks/{task_id}/transition",
            json={
                "new_state": new_state,
                "agent": "kilo-skill",
                "reason": reason
            }
        )
        return resp.status_code == 200
    
    async def cancel_task(self, task_id: str, reason: str = "") -> bool:
        """取消任务"""
        return await self.transition_task(
            task_id, 
            "Cancelled", 
            reason or "用户取消"
        )
```

---

## 推荐的 Docker 启动方式

使用完整模式（FastAPI）：

```bash
cd edict
docker-compose up -d

# 等待服务启动
sleep 10

# 验证
curl http://localhost:8000/health
```

---

## Skill 配置

```json
{
  "mcpServers": {
    "edict": {
      "command": "python",
      "args": ["-m", "edict_skill"],
      "env": {
        "EDICT_URL": "http://localhost:8000"
      }
    }
  }
}
```

---

## 总结

### 规划与代码的契合度：75%

**符合的部分**：
- ✅ 任务状态流转逻辑
- ✅ Agent 角色定义
- ✅ 整体架构设计

**需要调整的部分**：
- ⚠️ API 端点路径（已修正）
- ⚠️ 响应字段名（task_id vs id）
- ⚠️ 取消任务的实现方式
- ⚠️ Docker 启动方式（需用完整模式）

### 建议

1. **使用 FastAPI（端口 8000）** 作为 Skill 的连接目标
2. **修正 Skill 客户端代码**（参考上面的示例）
3. **使用 `edict/docker-compose.yml`** 启动完整服务
4. **增加 task_id 字段处理**（API 返回 task_id，但 Skill 可以映射为 id）