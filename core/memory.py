# Fix for core/memory.py lines 1-30
from core.chroma_helper import get_chroma_client, get_global_chroma_client

"""
Vector memory system using RAGFlow-based storage
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from utils import get_logger, MemoryError, generate_id
from app_config import config
from core.llm import LLMInterface

logger = get_logger(__name__, config.log_file, config.log_level)

class VectorMemory:
    """RAGFlow-based vector memory for context and retrieval"""
    
    def __init__(self):
        # Use the helper instead of direct chromadb import
        self.client = get_global_chroma_client()
        
        self.collection = self.client.get_or_create_collection(
            name=config.memory.collection_name,
            metadata={"description": "Nexus EVO memory store"}
        )
        
        logger.info(f"Memory initialized: {self.collection.count()} items")
        
        logger.info(f"Memory initialized: {self.collection.count()} items")
    
    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Store content in vector memory
        
        Args:
            content: Text content to store
            metadata: Optional metadata dictionary
            doc_id: Optional custom document ID
            
        Returns:
            Document ID
        """
        try:
            if not doc_id:
                doc_id = generate_id("mem_")
            
            # Generate embedding
            embedding = LLMInterface().generate_embedding(content)
            
            # Add timestamp to metadata
            meta = metadata or {}
            meta["timestamp"] = datetime.utcnow().isoformat()
            meta["content_length"] = len(content)
            
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            
            logger.debug(f"Stored memory: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Memory storage error: {e}")
            raise MemoryError(f"Storage failed: {e}")
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vector memory for relevant content
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of matching documents with metadata
        """
        try:
            # Generate query embedding
            query_embedding = LLMInterface().generate_embedding(query_text)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            formatted = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted.append({
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.debug(f"Query returned {len(formatted)} results")
            return formatted
            
        except Exception as e:
            logger.error(f"Memory query error: {e}")
            raise MemoryError(f"Query failed: {e}")
    
    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document by ID"""
        try:
            results = self.collection.get(ids=[doc_id])
            
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Memory retrieval error: {e}")
            return None
    
    def update(self, doc_id: str, content: str, metadata: Optional[Dict] = None):
        """Update existing memory"""
        try:
            embedding = LLMInterface().generate_embedding(content)
            
            meta = metadata or {}
            meta["updated_at"] = datetime.utcnow().isoformat()
            
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            
            logger.debug(f"Updated memory: {doc_id}")
            
        except Exception as e:
            logger.error(f"Memory update error: {e}")
            raise MemoryError(f"Update failed: {e}")
    
    def delete(self, doc_id: str):
        """Delete memory by ID"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted memory: {doc_id}")
            
        except Exception as e:
            logger.error(f"Memory deletion error: {e}")
            raise MemoryError(f"Deletion failed: {e}")
    
    def count(self) -> int:
        """Get total number of stored memories"""
        return self.collection.count()
    
    def clear(self):
        """Clear all memories (use with caution)"""
        try:
            self.client.delete_collection(config.memory.collection_name)
            self.collection = self.client.create_collection(
                name=config.memory.collection_name,
                metadata={"description": "Nexus EVO memory store"}
            )
            logger.warning("Memory cleared")
            
        except Exception as e:
            logger.error(f"Memory clear error: {e}")
            raise MemoryError(f"Clear failed: {e}")


class ConversationMemory:
    """Manage conversation history with context window"""
    
    def __init__(self, max_messages: int = None):
        self.max_messages = max_messages or config.memory.max_context_messages
        self.messages: List[Dict[str, str]] = []
        logger.info(f"Conversation memory initialized (max: {self.max_messages})")
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Trim if exceeds max
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self, include_system: bool = False) -> List[Dict[str, str]]:
        """Get conversation messages formatted for LLM"""
        if include_system:
            return [{"role": m["role"], "content": m["content"]} for m in self.messages]
        else:
            return [
                {"role": m["role"], "content": m["content"]}
                for m in self.messages
                if m["role"] != "system"
            ]
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []
        logger.debug("Conversation memory cleared")
    
    def get_context_summary(self) -> str:
        """Generate summary of conversation context"""
        if not self.messages:
            return "No conversation history"
        
        summary_parts = []
        for msg in self.messages[-5:]:  # Last 5 messages
            role = msg["role"].upper()
            content = msg["content"][:100]  # Truncate
            summary_parts.append(f"{role}: {content}")
        
        return "\n".join(summary_parts)


# Global memory instances
vector_memory = VectorMemory()
