"""Base tool class for all tools"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseTool(ABC):
    """Base class for all tools"""
    
    name: str = "base_tool"
    description: str = "Base tool"
    enabled: bool = True
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    def validate(self, **kwargs) -> bool:
        """Validate parameters before execution"""
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled
        }
    
    def get_signature(self) -> Dict[str, Any]:
        """Get tool signature for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": getattr(self, 'parameters', {})
        }
