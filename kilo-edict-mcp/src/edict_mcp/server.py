"""
MCP Server 主模块

Edict MCP Server 实现 - 完整的协议支持
"""

import asyncio
import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.types import (
    Tool,
    Resource,
    Prompt,
    ListToolsResult,
    ListResourcesResult,
    ListPromptsResult,
    CallToolResult,
    ReadResourceResult,
    GetPromptResult,
)
from mcp.server.stdio import stdio_server

from edict_mcp.config import EdictConfig, get_config
from edict_mcp.client import EdictClient
from edict_mcp.tools.tasks import (
    get_task_tools,
    TASK_TOOL_HANDLERS,
)
from edict_mcp.tools.agents import (
    get_agent_tools,
    AGENT_TOOL_HANDLERS,
)
from edict_mcp.tools.events import (
    get_event_tools,
    EVENT_TOOL_HANDLERS,
)
from edict_mcp.resources.status import (
    get_system_resources,
    handle_read_resource as handle_resource_read,
)
from edict_mcp.prompts.templates import (
    get_prompts,
    handle_get_prompt as handle_prompt_get,
)

logger = logging.getLogger(__name__)


class EdictMCPServer:
    """Edict MCP Server
    
    整合所有 Tools、Resources、Prompts 的 MCP Server 实现
    支持完整的 MCP 协议
    """
    
    def __init__(self, config: Optional[EdictConfig] = None):
        """初始化 MCP Server
        
        Args:
            config: EdictConfig 配置实例
        """
        self.config = config or get_config()
        self.server = Server(
            name=self.config.server_name,
            version=self.config.server_version,
        )
        self.client: Optional[EdictClient] = None
        self._setup_handlers()
    
    def _get_client(self) -> EdictClient:
        """获取或创建 EdictClient"""
        if self.client is None:
            self.client = EdictClient(self.config)
        return self.client
    
    def _setup_handlers(self):
        """设置 MCP Server 处理器"""
        
        # ==================== Tools ====================
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """列出所有可用的 Tools"""
            client = self._get_client()
            
            tools = []
            tools.extend(get_task_tools(self.server, client))
            tools.extend(get_agent_tools(self.server, client))
            tools.extend(get_event_tools(self.server, client))
            
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def call_tool(
            name: str,
            arguments: dict | None,
        ) -> CallToolResult:
            """调用 Tool"""
            client = self._get_client()
            args = arguments or {}
            
            # 路由到对应的处理器
            if name in TASK_TOOL_HANDLERS:
                result = await TASK_TOOL_HANDLERS[name](client, args)
            elif name in AGENT_TOOL_HANDLERS:
                result = await AGENT_TOOL_HANDLERS[name](client, args)
            elif name in EVENT_TOOL_HANDLERS:
                result = await EVENT_TOOL_HANDLERS[name](client, args)
            else:
                result = [{"type": "text", "text": f"Unknown tool: {name}"}]
            
            return CallToolResult(content=result)
        
        # ==================== Resources ====================
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """列出所有可用的 Resources"""
            client = self._get_client()
            
            resources = get_system_resources(self.server, client)
            
            return ListResourcesResult(resources=resources)
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """读取 Resource"""
            client = self._get_client()
            
            try:
                result = await handle_resource_read(client, uri)
                
                return ReadResourceResult(
                    contents=[
                        {
                            "uri": uri,
                            "mimeType": result.get("mime_type", "application/json"),
                            "text": result["content"],
                        }
                    ]
                )
            except ValueError as e:
                raise RuntimeError(f"Failed to read resource: {e}")
        
        # ==================== Prompts ====================
        
        @self.server.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """列出所有可用的 Prompts"""
            client = self._get_client()
            
            prompts = get_prompts(self.server, client)
            
            return ListPromptsResult(prompts=prompts)
        
        @self.server.get_prompt()
        async def get_prompt(
            name: str,
            arguments: dict | None,
        ) -> GetPromptResult:
            """获取 Prompt"""
            client = self._get_client()
            
            try:
                result = await handle_prompt_get(client, name, arguments)
                
                # 转换消息格式
                messages = []
                for msg in result.get("messages", []):
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", {}),
                    })
                
                return GetPromptResult(messages=messages)
            except ValueError as e:
                raise RuntimeError(f"Failed to get prompt: {e}")
    
    async def run(self):
        """运行 MCP Server"""
        logger.info(f"Starting Edict MCP Server (v{self.config.server_version})...")
        logger.info(f"Connecting to Edict API at {self.config.api_url}")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def main():
    """主入口函数"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    config = get_config()
    server = EdictMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main)
