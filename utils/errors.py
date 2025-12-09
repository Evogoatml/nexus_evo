"""
Custom exceptions for nexus_evo
"""


class NexusError(Exception):
    """Base exception for nexus_evo"""
    pass


class LLMError(NexusError):
    """LLM API errors"""
    pass


class ToolExecutionError(NexusError):
    """Tool execution failures"""
    pass


class MemoryError(NexusError):
    """Memory/vector DB errors"""
    pass


class ReasoningError(NexusError):
    """ReAct reasoning loop errors"""
    pass


class MacroError(NexusError):
    """Macro recording/playback errors"""
    pass


class ConfigurationError(NexusError):
    """Configuration errors"""
    pass


class AgentTimeoutError(NexusError):
    """Agent execution timeout"""
    pass


class ValidationError(NexusError):
    """Input validation errors"""
    pass
