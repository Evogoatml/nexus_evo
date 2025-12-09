"""Diagnostic and optimization tools"""
from typing import Dict, Any
from .base import BaseTool
from core.diagnostics import diagnostics

class DiagnosticTool(BaseTool):
    """Run system diagnostics"""
    
    name = "diagnostics"
    description = "Run system health check and diagnostics"
    parameters = {}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            result = diagnostics.run_quick_diagnostic()
            
            # Format output
            output = f"""
System Health: {result['health'].upper()}
CPU Usage: {result['cpu_percent']:.1f}%
Memory Usage: {result['memory_percent']:.1f}%
Active Tasks: {result['active_tasks']}
Timestamp: {result['timestamp']}
"""
            return {
                "success": True,
                "output": output.strip(),
                "data": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class SystemStatusTool(BaseTool):
    """Get detailed system status"""
    
    name = "status"
    description = "Get detailed system status and metrics"
    parameters = {}
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            from tools.registry import registry
            from core.memory import vector_memory
            
            diag = diagnostics.run_quick_diagnostic()
            
            status = f"""
=== NEXUS EVO SYSTEM STATUS ===

Health: {diag['health'].upper()}
CPU: {diag['cpu_percent']:.1f}%
Memory: {diag['memory_percent']:.1f}%

Active Tasks: {diag['active_tasks']}
Registered Tools: {len(registry.tools)}
Memory Items: {vector_memory.size()}

Status: OPERATIONAL
"""
            return {
                "success": True,
                "output": status.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
