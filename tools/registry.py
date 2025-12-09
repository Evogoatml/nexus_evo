"""
Tool registry for dynamic tool management
"""
from typing import Dict, List, Optional, Any
from tools.base_tool import BaseTool, ToolResult
from utils import get_logger
from app_config import config


logger = get_logger(__name__, config.log_file, config.log_level)


class ToolRegistry:
    """Registry for managing and executing tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        logger.info("Tool registry initialized")
    
    def register(self, tool: BaseTool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, tool_name: str):
        """Unregister a tool"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool information"""
        tool = self.get_tool(tool_name)
        return tool.get_info() if tool else None
    
    def get_all_tools_info(self) -> List[Dict[str, Any]]:
        """Get information for all tools"""
        return [tool.get_info() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters
            
        Returns:
            ToolResult object
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            logger.error(f"Tool not found: {tool_name}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool not found: {tool_name}"
            )
        
        return tool.execute(**kwargs)
    
    def get_tools_summary(self) -> str:
        """Get formatted summary of all tools"""
        if not self.tools:
            return "No tools registered"
        
        lines = ["Available Tools:"]
        for tool in self.tools.values():
            lines.append(f"- {tool.get_signature()}")
        
        return "\n".join(lines)
    
    def search_tools(self, query: str) -> List[str]:
        """Search tools by name or description"""
        query_lower = query.lower()
        matches = []
        
        for tool in self.tools.values():
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                matches.append(tool.name)
        
        return matches


# Global registry instance
registry = ToolRegistry()


def register_default_tools():
    """Register all default tools"""
    from tools.file_ops import (
        ReadFileTool, WriteFileTool, ListDirectoryTool,
        DeleteFileTool, FileInfoTool
    )
    from tools.shell import ShellTool, PingTool
    from tools.diagnostic import DiagnosticTool, SystemStatusTool
    from tools.network import (
        HTTPRequestTool, PortScanTool, DNSLookupTool, IPInfoTool
    )
    from tools.crypto import (
        HashTool, EncryptTool, DecryptTool, Base64Tool
    )
    from tools.git_ops import (
        GitCloneTool, GitRepoIndexTool, GitRepoSearchTool,
        GitRepoAnalyzeTool, GitRepoDeleteTool
    )
    
    # Register file tools
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ListDirectoryTool())
    registry.register(DeleteFileTool())
    registry.register(FileInfoTool())
    
    # Register shell tools
    registry.register(ShellTool())
    registry.register(DiagnosticTool())
    registry.register(SystemStatusTool())
    registry.register(PingTool())
    
    # Register network tools
    registry.register(HTTPRequestTool())
    registry.register(PortScanTool())
    registry.register(DNSLookupTool())
    registry.register(IPInfoTool())
    
    # Register crypto tools
    registry.register(HashTool())
    registry.register(EncryptTool())
    registry.register(DecryptTool())
    registry.register(Base64Tool())
    
    # Register Git tools
    registry.register(GitCloneTool())
    registry.register(GitRepoIndexTool())
    registry.register(GitRepoSearchTool())
    registry.register(GitRepoAnalyzeTool())
    registry.register(GitRepoDeleteTool())
    
    logger.info(f"Registered {len(registry.tools)} default tools")
