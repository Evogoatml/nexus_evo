"""
Base tool interface for nexus_evo
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from utils import get_logger, generate_id
from app_config import config


logger = get_logger(__name__, config.log_file, config.log_level)


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None


@dataclass
class ToolResult:
    """Tool execution result"""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata or {}
        }


class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    def __init__(self):
        self.execution_count = 0
        self.last_execution = None
        self.logger = get_logger(f"tool.{self.name}", config.log_file, config.log_level)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """Tool parameters"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute tool with given parameters
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult object
        """
        pass
    
    def validate_parameters(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate tool parameters
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        param_dict = {p.name: p for p in self.parameters}
        
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"
        
        # Check parameter types (basic validation)
        for key, value in kwargs.items():
            if key not in param_dict:
                return False, f"Unknown parameter: {key}"
        
        return True, None
    
    def run(self, **kwargs) -> ToolResult:
        """
        Run tool with validation and logging
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult object
        """
        execution_id = generate_id(f"{self.name}_")
        self.logger.info(f"Executing: {execution_id}")
        
        # Validate parameters
        is_valid, error = self.validate_parameters(**kwargs)
        if not is_valid:
            self.logger.error(f"Validation failed: {error}")
            return ToolResult(success=False, output=None, error=error)
        
        try:
            # Execute tool
            result = self.execute(**kwargs)
            
            # Update execution tracking
            self.execution_count += 1
            self.last_execution = execution_id
            
            if result.success:
                self.logger.info(f"Success: {execution_id}")
            else:
                self.logger.warning(f"Failed: {execution_id} - {result.error}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Exception in {execution_id}: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool execution error: {str(e)}"
            )
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in self.parameters
            ],
            "execution_count": self.execution_count,
            "last_execution": self.last_execution
        }
    
    def get_signature(self) -> str:
        """Get tool signature for LLM"""
        params = ", ".join([
            f"{p.name}: {p.type}" + ("*" if p.required else "")
            for p in self.parameters
        ])
        return f"{self.name}({params}) -> {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
