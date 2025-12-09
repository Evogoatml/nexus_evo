"""
Configuration management for nexus_evo                        """
import os
from pathlib import Path                                      
from typing import Optional
from dataclasses import dataclass, field

OPENAI_MODEL_NAME="gpt-4o-mini"  # Much higher TPM limit      
@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_observation_tokens: int = 5000  # Max tokens per tool output
    max_tokens: int = 8000                                        
    timeout: int = 60
                                                                  
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")


@dataclass
class MemoryConfig:
    """Vector memory configuration"""
    persist_directory: str = "./nexus_evo_data/chromadb"
    collection_name: str = "nexus_memory"
    embedding_model: str = "text-embedding-3-small"
    max_context_messages: int = 20


@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    token: Optional[str] = None
    allowed_users: list = field(default_factory=list)

    def __post_init__(self):
        if not self.token:
            self.token = os.getenv("TELEGRAM_BOT_TOKEN")


@dataclass                                                    
class MacroConfig:
    """Macro recording configuration"""
    storage_path: str = "./nexus_evo_data/macros"
    max_steps: int = 100
    auto_save: bool = True


@dataclass
class AgentConfig:
    """Agent behavior configuration"""
    max_reasoning_steps: int = 15
    max_tool_retries: int = 3
    enable_parallel_execution: bool = False
    nanoagent_timeout: int = 30

                                                              
@dataclass
class NexusConfig:
    """Main nexus_evo configuration"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    macros: MacroConfig = field(default_factory=MacroConfig)      
    agent: AgentConfig = field(default_factory=AgentConfig)

    data_dir: str = "./nexus_evo_data"
    log_level: str = "INFO"
    log_file: str = "./nexus_evo_data/nexus.log"

    def __post_init__(self):
        # Create data directories
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.memory.persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.macros.storage_path).mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


# Global config instance
config = NexusConfig()
