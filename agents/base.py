"""
Base agent class for nexus_evo
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils import get_logger, generate_id
from app_config import config
from core.state import AgentState


logger = get_logger(__name__, config.log_file, config.log_level)


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id or generate_id("agent_")
        self.state = AgentState(self.agent_id)
        self.logger = get_logger(f"agent.{self.name}", config.log_file, config.log_level)
        self.logger.info(f"Agent initialized: {self.agent_id}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description"""
        pass
    
    @abstractmethod
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute agent task
        
        Args:
            task: Task description
            context: Optional context dictionary
            
        Returns:
            Task result
        """
        pass
    
    def update_state(self, **kwargs):
        """Update agent state"""
        self.state.update(**kwargs)
        self.state.save()
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "state": self.state.to_dict()
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name} ({self.agent_id})>"
