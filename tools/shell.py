"""Shell execution tools"""
import subprocess
import shlex
from typing import Dict, Any
from .base import BaseTool

class ShellTool(BaseTool):
    """Execute shell commands"""
    
    name = "shell"
    description = "Execute shell commands"
    parameters = {
        "command": {"type": "string", "required": True, "description": "Shell command to execute"}
    }
    
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

class PingTool(BaseTool):
    """Ping network hosts"""
    
    name = "ping"
    description = "Ping a host to check connectivity"
    parameters = {
        "host": {"type": "string", "required": True, "description": "Host to ping"},
        "count": {"type": "integer", "required": False, "description": "Number of pings", "default": 4}
    }
    
    def execute(self, host: str, count: int = 4, **kwargs) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["ping", "-c", str(count), host],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "host": host
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
