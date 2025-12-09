"""
Main orchestrator agent with ReAct reasoning and nanoagent spawning
"""
from typing import Dict, Any, Optional
from agents.base import BaseAgent
from agents.nanoagent import spawner
from core.reasoning import react_engine
from core.memory import vector_memory, ConversationMemory
from utils import get_logger, generate_id
from app_config import config


logger = get_logger(__name__, config.log_file, config.log_level)


class OrchestratorAgent(BaseAgent):
    """
    Main orchestrator agent
    Uses ReAct reasoning to solve complex tasks
    Can spawn nanoagents for specific subtasks
    """
    
    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id)
        self.conversation = ConversationMemory()
        self.task_history = []
        self.logger.info("Orchestrator agent initialized")
    
    @property
    def name(self) -> str:
        return "nexus_evo_orchestrator"
    
    @property
    def description(self) -> str:
        return "Main orchestrator agent with ReAct reasoning and nanoagent spawning capabilities"
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute task using ReAct reasoning
        
        Args:
            task: Task description
            context: Optional context
            
        Returns:
            Task result
        """
        task_id = generate_id("task_")
        self.logger.info(f"Executing task {task_id}: {task[:100]}")
        
        # Update state
        self.update_state(
            status="reasoning",
            current_task=task,
            task_id=task_id
        )
        
        try:
            # Add to conversation memory
            self.conversation.add_message("user", task)
            
            # Build context string
            context_str = None
            if context:
                context_parts = [f"{k}: {v}" for k, v in context.items()]
                context_str = "\n".join(context_parts)
            
            # Execute ReAct reasoning
            result = react_engine.reason(task, context_str)
            
            # Add result to conversation
            self.conversation.add_message("assistant", result)
            
            # Store in vector memory for future retrieval
            memory_content = f"Task: {task}\nResult: {result}"
            vector_memory.store(
                memory_content,
                metadata={
                    "task_id": task_id,
                    "type": "task_execution",
                    "success": True
                }
            )
            
            # Update state
            self.update_state(
                status="completed",
                last_task=task,
                last_result=result[:500]
            )
            
            # Add to history
            self.task_history.append({
                "task_id": task_id,
                "task": task,
                "result": result,
                "reasoning_steps": len(react_engine.traces)
            })
            
            self.logger.info(f"Task {task_id} completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Task execution failed: {e}"
            self.logger.error(error_msg)
            
            # Update state
            self.update_state(
                status="failed",
                error=str(e)
            )
            
            # Store failure in memory
            vector_memory.store(
                f"Failed task: {task}\nError: {e}",
                metadata={
                    "task_id": task_id,
                    "type": "task_execution",
                    "success": False
                }
            )
            
            return error_msg
    
    def spawn_nanoagent(self, task_type: str, task: str, context: Optional[Dict] = None) -> str:
        """
        Spawn a nanoagent for specific task
        
        Args:
            task_type: Type of nanoagent (file_scan, port_scan, etc.)
            task: Task description
            context: Task context
            
        Returns:
            Nanoagent result
        """
        self.logger.info(f"Spawning nanoagent: {task_type}")
        
        result = spawner.execute(task_type, task, context)
        
        self.logger.info(f"Nanoagent completed: {task_type}")
        return result
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        return self.conversation.get_context_summary()
    
    def clear_conversation(self):
        """Clear conversation memory"""
        self.conversation.clear()
        self.logger.info("Conversation memory cleared")
    
    def get_task_history(self) -> list:
        """Get task execution history"""
        return self.task_history
    
    def get_reasoning_summary(self) -> str:
        """Get last reasoning process summary"""
        return react_engine.get_reasoning_summary()
    
    def interactive_mode(self):
        """Run interactive CLI mode"""
        print(f"\n{'='*60}")
        print(f"Nexus EVO - Interactive Orchestrator")
        print(f"{'='*60}")
        print("Commands:")
        print("  /help - Show this help")
        print("  /status - Show agent status")
        print("  /history - Show task history")
        print("  /reasoning - Show last reasoning trace")
        print("  /clear - Clear conversation")
        print("  /exit - Exit interactive mode")
        print(f"{'='*60}\n")
        
        while True:
            try:
                user_input = input("\n[You] > ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    if user_input == "/exit":
                        print("Exiting interactive mode...")
                        break
                    elif user_input == "/help":
                        print("\nAvailable commands: /help, /status, /history, /reasoning, /clear, /exit")
                    elif user_input == "/status":
                        status = self.get_status()
                        print(f"\nAgent Status: {status['state']['status']}")
                        print(f"Tasks completed: {len(self.task_history)}")
                    elif user_input == "/history":
                        print("\nTask History:")
                        for i, task in enumerate(self.task_history[-5:], 1):
                            print(f"{i}. {task['task'][:80]}... [{task['reasoning_steps']} steps]")
                    elif user_input == "/reasoning":
                        print(f"\n{self.get_reasoning_summary()}")
                    elif user_input == "/clear":
                        self.clear_conversation()
                        print("Conversation cleared")
                    else:
                        print(f"Unknown command: {user_input}")
                    continue
                
                # Execute task
                print("\n[Nexus] Thinking...")
                result = self.execute(user_input)
                print(f"\n[Nexus] {result}")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type /exit to quit.")
            except Exception as e:
                print(f"\nError: {e}")


# Global orchestrator instance
orchestrator = OrchestratorAgent()
