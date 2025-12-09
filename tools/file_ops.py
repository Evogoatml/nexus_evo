"""
File operation tools
"""
import os
from pathlib import Path
from typing import List
from tools.base_tool import BaseTool, ToolParameter, ToolResult


class ReadFileTool(BaseTool):
    """Read file contents"""
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read contents of a file"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("path", "string", "File path to read", required=True)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        
        try:
            file_path = Path(path).expanduser()
            
            if not file_path.exists():
                return ToolResult(success=False, output=None, error=f"File not found: {path}")
            
            if not file_path.is_file():
                return ToolResult(success=False, output=None, error=f"Not a file: {path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                output=content,
                metadata={"size": len(content), "path": str(file_path)}
            )
            
        except UnicodeDecodeError:
            return ToolResult(success=False, output=None, error="File is not text/UTF-8 encoded")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class WriteFileTool(BaseTool):
    """Write content to file"""
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write content to a file (creates or overwrites)"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("path", "string", "File path to write", required=True),
            ToolParameter("content", "string", "Content to write", required=True),
            ToolParameter("append", "boolean", "Append instead of overwrite", default=False)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        content = kwargs.get("content")
        append = kwargs.get("append", False)
        
        try:
            file_path = Path(path).expanduser()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                output=f"Written {len(content)} bytes to {path}",
                metadata={"path": str(file_path), "size": len(content), "mode": mode}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class ListDirectoryTool(BaseTool):
    """List directory contents"""
    
    @property
    def name(self) -> str:
        return "list_directory"
    
    @property
    def description(self) -> str:
        return "List files and directories in a path"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("path", "string", "Directory path to list", required=True),
            ToolParameter("recursive", "boolean", "List recursively", default=False)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        recursive = kwargs.get("recursive", False)
        
        try:
            dir_path = Path(path).expanduser()
            
            if not dir_path.exists():
                return ToolResult(success=False, output=None, error=f"Path not found: {path}")
            
            if not dir_path.is_dir():
                return ToolResult(success=False, output=None, error=f"Not a directory: {path}")
            
            if recursive:
                items = [str(p.relative_to(dir_path)) for p in dir_path.rglob("*")]
            else:
                items = [p.name for p in dir_path.iterdir()]
            
            return ToolResult(
                success=True,
                output=items,
                metadata={"count": len(items), "path": str(dir_path), "recursive": recursive}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class DeleteFileTool(BaseTool):
    """Delete file or directory"""
    
    @property
    def name(self) -> str:
        return "delete_file"
    
    @property
    def description(self) -> str:
        return "Delete a file or directory"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("path", "string", "Path to delete", required=True),
            ToolParameter("recursive", "boolean", "Delete directory recursively", default=False)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        recursive = kwargs.get("recursive", False)
        
        try:
            target_path = Path(path).expanduser()
            
            if not target_path.exists():
                return ToolResult(success=False, output=None, error=f"Path not found: {path}")
            
            if target_path.is_file():
                target_path.unlink()
                return ToolResult(success=True, output=f"Deleted file: {path}")
            elif target_path.is_dir():
                if recursive:
                    import shutil
                    shutil.rmtree(target_path)
                    return ToolResult(success=True, output=f"Deleted directory: {path}")
                else:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="Cannot delete directory without recursive=True"
                    )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class FileInfoTool(BaseTool):
    """Get file information"""
    
    @property
    def name(self) -> str:
        return "file_info"
    
    @property
    def description(self) -> str:
        return "Get information about a file or directory"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("path", "string", "Path to inspect", required=True)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        
        try:
            file_path = Path(path).expanduser()
            
            if not file_path.exists():
                return ToolResult(success=False, output=None, error=f"Path not found: {path}")
            
            stat = file_path.stat()
            info = {
                "path": str(file_path),
                "name": file_path.name,
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "permissions": oct(stat.st_mode)[-3:],
                "is_symlink": file_path.is_symlink()
            }
            
            if file_path.is_file():
                info["extension"] = file_path.suffix
            
            return ToolResult(success=True, output=info, metadata={"path": str(file_path)})
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
