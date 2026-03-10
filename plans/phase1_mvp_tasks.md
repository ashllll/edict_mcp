# 第一阶段 MVP 实施任务清单

## 目标
构建一个基础的 MCP Server，使 Kilo Code 能够通过 Edict API 创建和管理任务。

---

## 任务清单

### 1. 项目初始化

- [ ] **1.1 创建项目目录结构**
  - 创建 `kilo-edict-mcp/` 目录
  - 创建子目录：`src/edict_mcp/`, `tests/`, `docs/`
  
- [ ] **1.2 初始化 Python 项目**
  - 创建 `pyproject.toml`
  - 配置项目元数据（名称、版本、作者）
  - 配置打包工具（setuptools 或 hatch）

- [ ] **1.3 添加依赖**
  - 核心依赖：`mcp>=1.0.0`, `httpx>=0.27.0`, `pydantic>=2.0`
  - 开发依赖：`pytest`, `pytest-asyncio`, `black`, `ruff`
  - 创建 `requirements.txt` 和 `requirements-dev.txt`

- [ ] **1.4 创建基础目录结构**
  ```
  kilo-edict-mcp/
  ├── src/
  │   └── edict_mcp/
  │       ├── __init__.py          # 版本号和主入口
  │       ├── server.py            # MCP Server 主类
  │       ├── __main__.py          # python -m 入口
  │       ├── client/
  │       │   ├── __init__.py
  │       │   └── api.py           # Edict API 客户端
  │       ├── tools/
  │       │   ├── __init__.py
  │       │   └── tasks.py         # 任务管理 Tools
  │       └── models/
  │           ├── __init__.py
  │           ├── task.py          # Task 数据模型
  │           └── common.py        # 通用模型和枚举
  ├── tests/
  │   ├── __init__.py
  │   ├── conftest.py              # pytest 配置和 fixtures
  │   ├── test_client.py           # API 客户端测试
  │   └── test_tools.py            # Tools 测试
  ├── README.md
  ├── pyproject.toml
  └── .gitignore
  ```

---

### 2. 数据模型定义

- [ ] **2.1 创建 TaskState 枚举**
  ```python
  class TaskState(str, Enum):
      TAZI = "Taizi"           # 太子分拣
      ZHONGSHU = "Zhongshu"    # 中书省规划
      MENXIA = "Menxia"        # 门下省审议
      ASSIGNED = "Assigned"    # 已派发
      DOING = "Doing"          # 执行中
      REVIEW = "Review"        # 待审查
      DONE = "Done"            # 已完成
      BLOCKED = "Blocked"      # 已阻塞
      CANCELLED = "Cancelled"  # 已取消
  ```

- [ ] **2.2 创建 Task 模型**
  ```python
  class Task(BaseModel):
      id: str
      title: str
      description: str = ""
      state: TaskState
      org: Optional[str] = None
      official: Optional[str] = None
      created_at: datetime
      updated_at: datetime
      flow_log: List[FlowLogEntry] = []
      progress_log: List[ProgressLogEntry] = []
      todos: List[TodoItem] = []
  ```

- [ ] **2.3 创建辅助模型**
  - `FlowLogEntry` - 流转日志条目
  - `ProgressLogEntry` - 进展日志条目
  - `TodoItem` - 子任务项
  - `CreateTaskRequest` - 创建任务请求

---

### 3. Edict API 客户端

- [ ] **3.1 实现 EdictAPIClient 类**
  ```python
  class EdictAPIClient:
      def __init__(self, base_url: str, timeout: int = 30):
          self.base_url = base_url.rstrip("/")
          self.timeout = timeout
          self.client = httpx.AsyncClient(timeout=timeout)
  ```

- [ ] **3.2 实现基础 HTTP 方法**
  - `_get(path, params)` - GET 请求
  - `_post(path, json)` - POST 请求
  - `_put(path, json)` - PUT 请求
  - `_delete(path)` - DELETE 请求

- [ ] **3.3 实现错误处理**
  - 处理 HTTP 错误（4xx, 5xx）
  - 实现重试机制（指数退避）
  - 自定义异常类：`EdictAPIError`, `EdictNotFoundError`, `EdictValidationError`

- [ ] **3.4 实现任务相关 API 方法**
  - `create_task(data: CreateTaskRequest) -> Task`
  - `get_task(task_id: str) -> Task`
  - `list_tasks(state: str = None, limit: int = 20) -> List[Task]`
  - `cancel_task(task_id: str) -> bool`

---

### 4. MCP Tools 实现

- [ ] **4.1 实现 `create_task` Tool**
  ```python
  @mcp.tool()
  async def create_task(
      ctx: Context,
      title: str,
      description: str = "",
      priority: str = "normal"
  ) -> str:
      """
      在 Edict 系统中创建一个新任务。
      
      任务创建后会进入"太子"分拣阶段，由系统自动流转到后续流程。
      
      Args:
          title: 任务标题（必填）
          description: 任务详细描述
          priority: 优先级，可选值为 low/normal/high/urgent
          
      Returns:
          创建的任务 ID 和初始状态信息
      """
  ```

- [ ] **4.2 实现 `get_task` Tool**
  ```python
  @mcp.tool()
  async def get_task(
      ctx: Context,
      task_id: str
  ) -> str:
      """
      获取指定任务的详细信息和当前状态。
      
      返回内容包括：
      - 任务基本信息（标题、描述、状态）
      - 当前负责部门和官员
      - 完整流转历史
      - 子任务列表和进度
      
      Args:
          task_id: 任务 ID（格式：EDCT-YYYYMMDD-NNN 或 UUID）
          
      Returns:
          格式化的任务详情文本
      """
  ```

- [ ] **4.3 实现 `list_tasks` Tool**
  ```python
  @mcp.tool()
  async def list_tasks(
      ctx: Context,
      state: str = None,
      limit: int = 10
  ) -> str:
      """
      列出 Edict 系统中的任务。
      
      可以按状态过滤，支持的状态：
      - Taizi: 太子分拣中
      - Zhongshu: 中书省规划中
      - Menxia: 门下省审议中
      - Assigned: 已派发
      - Doing: 执行中
      - Review: 待审查
      - Done: 已完成
      
      Args:
          state: 过滤状态（可选）
          limit: 返回最大数量（默认 10，最大 50）
          
      Returns:
          任务列表摘要
      """
  ```

- [ ] **4.4 实现 `cancel_task` Tool**
  ```python
  @mcp.tool()
  async def cancel_task(
      ctx: Context,
      task_id: str,
      reason: str = ""
  ) -> str:
      """
      取消指定的任务。
      
      注意：只能取消未完成（非 Done）的任务。
      已取消的任务可以重新创建。
      
      Args:
          task_id: 要取消的任务 ID
          reason: 取消原因（可选）
          
      Returns:
          取消操作结果
      """
  ```

---

### 5. MCP Server 主入口

- [ ] **5.1 实现 EdictMCPServer 类**
  ```python
  class EdictMCPServer:
      def __init__(self, edict_url: str):
          self.client = EdictAPIClient(edict_url)
          self.mcp = Server("edict-mcp")
          self._register_tools()
      
      def _register_tools(self):
          # 注册所有 tools
          pass
      
      async def run(self):
          # 启动 server
          pass
  ```

- [ ] **5.2 实现命令行入口**
  ```python
  def main():
      parser = argparse.ArgumentParser(description="Edict MCP Server")
      parser.add_argument("--edict-url", default=os.getenv("EDICT_API_URL", "http://localhost:7891"))
      parser.add_argument("--port", type=int, default=0)  # stdio 模式
      args = parser.parse_args()
      
      server = EdictMCPServer(args.edict_url)
      asyncio.run(server.run())
  ```

- [ ] **5.3 配置 stdio 传输**
  ```python
  from mcp.server.stdio import stdio_server
  
  async with stdio_server() as (read_stream, write_stream):
      await server.run(
          read_stream,
          write_stream,
          InitializationOptions(
              server_name="edict-mcp",
              server_version="0.1.0",
              capabilities=server.get_capabilities()
          )
      )
  ```

---

### 6. 测试

- [ ] **6.1 配置 pytest**
  - 创建 `conftest.py`
  - 配置 asyncio 模式
  - 创建 mock fixtures

- [ ] **6.2 编写 API 客户端测试**
  - 测试 `create_task` 成功/失败场景
  - 测试 `get_task` 成功/404场景
  - 测试重试机制
  - 使用 `respx` 或 `pytest-httpx` mock HTTP

- [ ] **6.3 编写 Tools 测试**
  - 测试 `create_task` tool 调用
  - 测试参数验证
  - 测试错误处理

---

### 7. 文档

- [ ] **7.1 编写 README.md**
  - 项目简介
  - 安装说明
  - 配置指南
  - 使用示例
  - 开发指南

- [ ] **7.2 编写 Kilo Code 配置示例**
  ```json
  {
    "mcpServers": {
      "edict": {
        "command": "python",
        "args": ["-m", "edict_mcp"],
        "env": {
          "EDICT_API_URL": "http://localhost:7891"
        }
      }
    }
  }
  ```

- [ ] **7.3 编写使用示例**
  - 基础任务创建示例
  - 查询任务示例
  - 常见问题排查

---

### 8. 验证和发布

- [ ] **8.1 本地验证**
  - 安装到虚拟环境
  - 测试所有 tools 调用
  - 验证 MCP 协议兼容性

- [ ] **8.2 代码检查**
  - 运行 `black` 格式化
  - 运行 `ruff` 检查
  - 确保无警告

- [ ] **8.3 提交代码**
  - 初始化 git 仓库
  - 编写 .gitignore
  - 提交初始版本

---

## 验收标准

### 功能验收
- [ ] `create_task` 能成功创建任务并返回任务 ID
- [ ] `get_task` 能正确查询任务详情
- [ ] `list_tasks` 能列出任务列表
- [ ] `cancel_task` 能取消未完成任务
- [ ] 所有 tools 都有清晰的 docstring

### 质量验收
- [ ] 单元测试覆盖率 > 70%
- [ ] 代码通过 black 和 ruff 检查
- [ ] README 文档完整
- [ ] 可以在 Kilo Code 中成功配置和使用

---

## 依赖条件

- Python 3.10+
- Edict 后端服务已启动（默认 http://localhost:7891）
- 网络可以访问 Edict API

---

## 参考文件

- [完整实施计划](./kilo_edict_implementation_plan.md)
- [Edict 架构分析](./edict_architecture_analysis.md)
