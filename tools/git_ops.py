"""
Git repository operation tools
"""
import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool, ToolParameter, ToolResult
from core.memory import vector_memory
from utils import get_logger, generate_id, sanitize_filename

logger = get_logger(__name__)


class GitCloneTool(BaseTool):
    """Clone a Git repository"""
    
    @property
    def name(self) -> str:
        return "git_clone"
    
    @property
    def description(self) -> str:
        return "Clone a Git repository to local directory"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("repo_url", "string", "Git repository URL", required=True),
            ToolParameter("destination", "string", "Destination directory", default="/tmp"),
            ToolParameter("branch", "string", "Branch to clone", default="main")
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        repo_url = kwargs.get("repo_url")
        destination = kwargs.get("destination", "/tmp")
        branch = kwargs.get("branch", "main")
        
        try:
            # Extract repo name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            clone_path = Path(destination) / repo_name
            
            # Check if already exists
            if clone_path.exists():
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Repository already exists at {clone_path}. Delete it first or use a different destination."
                )
            
            # Clone repository
            result = subprocess.run(
                ["git", "clone", "-b", branch, repo_url, str(clone_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Count files
                files = list(clone_path.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                
                return ToolResult(
                    success=True,
                    output={
                        "clone_path": str(clone_path),
                        "repo_name": repo_name,
                        "file_count": file_count,
                        "branch": branch
                    },
                    metadata={
                        "repo_url": repo_url,
                        "destination": str(clone_path)
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Git clone failed: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output=None, error="Clone timed out after 5 minutes")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class GitRepoIndexTool(BaseTool):
    """Index Git repository contents into vector memory"""
    
    @property
    def name(self) -> str:
        return "git_index"
    
    @property
    def description(self) -> str:
        return "Index repository files into vector memory for semantic search"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("repo_path", "string", "Path to cloned repository", required=True),
            ToolParameter("file_extensions", "list", "File extensions to index (e.g. ['.py', '.md'])", default=None),
            ToolParameter("max_file_size", "integer", "Max file size in KB to index", default=500),
            ToolParameter("exclude_dirs", "list", "Directories to exclude", default=[".git", "node_modules", "__pycache__", ".venv"])
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        repo_path = Path(kwargs.get("repo_path"))
        file_extensions = kwargs.get("file_extensions")
        max_file_size = kwargs.get("max_file_size", 500) * 1024  # Convert to bytes
        exclude_dirs = set(kwargs.get("exclude_dirs", [".git", "node_modules", "__pycache__", ".venv"]))
        
        if not repo_path.exists():
            return ToolResult(success=False, output=None, error=f"Repository path not found: {repo_path}")
        
        try:
            indexed_files = []
            skipped_files = []
            total_size = 0
            
            # Walk through repository
            for file_path in repo_path.rglob("*"):
                # Skip if not a file
                if not file_path.is_file():
                    continue
                
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue
                
                # Check file extension filter
                if file_extensions and file_path.suffix not in file_extensions:
                    continue
                
                # Check file size
                file_size = file_path.stat().st_size
                if file_size > max_file_size:
                    skipped_files.append({
                        "path": str(file_path),
                        "reason": f"too large ({file_size / 1024:.1f} KB)"
                    })
                    continue
                
                # Read file content
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Generate relative path
                    relative_path = file_path.relative_to(repo_path)
                    
                    # Store in vector memory
                    doc_id = generate_id(f"git_{sanitize_filename(str(relative_path))}_")
                    
                    vector_memory.store(
                        content,
                        metadata={
                            "type": "git_file",
                            "repo_path": str(repo_path),
                            "repo_name": repo_path.name,
                            "file_path": str(relative_path),
                            "file_extension": file_path.suffix,
                            "file_size": file_size
                        },
                        doc_id=doc_id
                    )
                    
                    indexed_files.append({
                        "path": str(relative_path),
                        "size": file_size,
                        "doc_id": doc_id
                    })
                    total_size += file_size
                    
                except Exception as e:
                    skipped_files.append({
                        "path": str(file_path),
                        "reason": f"read error: {e}"
                    })
            
            return ToolResult(
                success=True,
                output={
                    "indexed_count": len(indexed_files),
                    "skipped_count": len(skipped_files),
                    "total_size_kb": total_size / 1024,
                    "indexed_files": indexed_files[:20],  # First 20 for display
                    "skipped_files": skipped_files[:10] if skipped_files else []
                },
                metadata={
                    "repo_path": str(repo_path),
                    "repo_name": repo_path.name
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class GitRepoSearchTool(BaseTool):
    """Search indexed Git repository contents"""
    
    @property
    def name(self) -> str:
        return "git_search"
    
    @property
    def description(self) -> str:
        return "Search through indexed repository files using semantic search"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("query", "string", "Search query", required=True),
            ToolParameter("repo_name", "string", "Repository name to filter by", default=None),
            ToolParameter("file_extension", "string", "File extension to filter by (e.g. '.py')", default=None),
            ToolParameter("n_results", "integer", "Number of results to return", default=5)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query")
        repo_name = kwargs.get("repo_name")
        file_extension = kwargs.get("file_extension")
        n_results = kwargs.get("n_results", 5)
        
        try:
            # Build metadata filter
            filter_metadata = {"type": "git_file"}
            if repo_name:
                filter_metadata["repo_name"] = repo_name
            if file_extension:
                filter_metadata["file_extension"] = file_extension
            
            # Search vector memory
            results = vector_memory.query(
                query,
                n_results=n_results,
                filter_metadata=filter_metadata
            )
            
            if not results:
                return ToolResult(
                    success=True,
                    output={"message": "No results found", "results": []},
                    metadata={"query": query}
                )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "file_path": result['metadata'].get('file_path'),
                    "repo_name": result['metadata'].get('repo_name'),
                    "content_preview": result['content'][:300] + "..." if len(result['content']) > 300 else result['content'],
                    "relevance_score": 1 - result.get('distance', 0) if result.get('distance') else None
                })
            
            return ToolResult(
                success=True,
                output={
                    "query": query,
                    "result_count": len(formatted_results),
                    "results": formatted_results
                },
                metadata={"query": query, "filters": filter_metadata}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class GitRepoAnalyzeTool(BaseTool):
    """Analyze Git repository structure and statistics"""
    
    @property
    def name(self) -> str:
        return "git_analyze"
    
    @property
    def description(self) -> str:
        return "Analyze repository structure, file types, and statistics"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("repo_path", "string", "Path to repository", required=True)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        repo_path = Path(kwargs.get("repo_path"))
        
        if not repo_path.exists():
            return ToolResult(success=False, output=None, error=f"Repository not found: {repo_path}")
        
        try:
            file_types = {}
            total_files = 0
            total_size = 0
            largest_files = []
            
            # Analyze repository
            for file_path in repo_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Skip .git directory
                if ".git" in file_path.parts:
                    continue
                
                total_files += 1
                file_size = file_path.stat().st_size
                total_size += file_size
                
                # Track file types
                ext = file_path.suffix or "no_extension"
                if ext not in file_types:
                    file_types[ext] = {"count": 0, "total_size": 0}
                file_types[ext]["count"] += 1
                file_types[ext]["total_size"] += file_size
                
                # Track largest files
                largest_files.append({
                    "path": str(file_path.relative_to(repo_path)),
                    "size": file_size
                })
            
            # Sort and limit largest files
            largest_files.sort(key=lambda x: x["size"], reverse=True)
            largest_files = largest_files[:10]
            
            # Sort file types by count
            file_types_sorted = sorted(
                file_types.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )
            
            return ToolResult(
                success=True,
                output={
                    "repo_name": repo_path.name,
                    "total_files": total_files,
                    "total_size_mb": total_size / (1024 * 1024),
                    "file_types": [
                        {
                            "extension": ext,
                            "count": data["count"],
                            "total_size_kb": data["total_size"] / 1024
                        }
                        for ext, data in file_types_sorted[:20]
                    ],
                    "largest_files": [
                        {
                            "path": f["path"],
                            "size_kb": f["size"] / 1024
                        }
                        for f in largest_files
                    ]
                },
                metadata={"repo_path": str(repo_path)}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class GitRepoDeleteTool(BaseTool):
    """Delete a cloned repository"""
    
    @property
    def name(self) -> str:
        return "git_delete"
    
    @property
    def description(self) -> str:
        return "Delete a cloned repository from disk"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("repo_path", "string", "Path to repository to delete", required=True)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        repo_path = Path(kwargs.get("repo_path"))
        
        if not repo_path.exists():
            return ToolResult(success=False, output=None, error=f"Repository not found: {repo_path}")
        
        try:
            # Safety check - must contain .git directory
            if not (repo_path / ".git").exists():
                return ToolResult(
                    success=False,
                    output=None,
                    error="Not a Git repository (no .git directory found)"
                )
            
            # Delete repository
            shutil.rmtree(repo_path)
            
            return ToolResult(
                success=True,
                output=f"Deleted repository at {repo_path}",
                metadata={"deleted_path": str(repo_path)}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
