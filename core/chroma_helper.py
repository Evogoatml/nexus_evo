"""RAGFlow-based replacement for ChromaDB helper"""
import logging
import json
from pathlib import Path
from typing import Optional, Any, List, Dict
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class RAGFlowClient:
    """Drop-in replacement for ChromaDB client"""
    
    def __init__(self, persist_directory: str = "./ragflow_data"):
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._collections = {}
        logger.info(f"RAGFlow client initialized: {persist_directory}")
    
    def get_or_create_collection(self, name: str, metadata: dict = None):
        """Get or create a collection"""
        if name not in self._collections:
            self._collections[name] = RAGFlowCollection(name, self.persist_dir, metadata)
        return self._collections[name]
    
    def delete_collection(self, name: str):
        """Delete a collection"""
        if name in self._collections:
            self._collections[name].clear()
            del self._collections[name]

class RAGFlowCollection:
    """Collection interface compatible with ChromaDB"""
    
    def __init__(self, name: str, persist_dir: Path, metadata: dict = None):
        self.name = name
        self.persist_dir = persist_dir / name
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = metadata or {}
        self._data = {}
        self._load()
    
    def _load(self):
        """Load existing data"""
        data_file = self.persist_dir / "data.json"
        if data_file.exists():
            try:
                with open(data_file) as f:
                    self._data = json.load(f)
                logger.info(f"Loaded {len(self._data)} items from {self.name}")
            except Exception as e:
                logger.warning(f"Failed to load {self.name}: {e}")
                self._data = {}
    
    def _save(self):
        """Persist data to disk"""
        try:
            data_file = self.persist_dir / "data.json"
            with open(data_file, 'w') as f:
                json.dump(self._data, f)
        except Exception as e:
            logger.error(f"Failed to save {self.name}: {e}")
    
    def add(self, ids: List[str], documents: List[str] = None, 
            metadatas: List[Dict] = None, embeddings: List[List[float]] = None):
        """Add items to collection (ChromaDB-compatible interface)"""
        if not isinstance(ids, list):
            ids = [ids]
        if documents and not isinstance(documents, list):
            documents = [documents]
        if metadatas and not isinstance(metadatas, list):
            metadatas = [metadatas]
        
        for i, item_id in enumerate(ids):
            self._data[item_id] = {
                "id": item_id,
                "document": documents[i] if documents else None,
                "metadata": metadatas[i] if metadatas else {},
                "embedding": embeddings[i] if embeddings else None
            }
        
        self._save()
        logger.debug(f"Added {len(ids)} items to {self.name}")
    
    def query(self, query_texts: List[str] = None, 
             query_embeddings: List[List[float]] = None,
             n_results: int = 10, where: Dict = None) -> Dict:
        """Query collection (simple keyword matching for now)"""
        results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        if not query_texts:
            return results
        
        query = query_texts[0].lower()
        matches = []
        
        for item_id, item in self._data.items():
            if not item.get("document"):
                continue
            
            doc_lower = item["document"].lower()
            score = 0
            
            # Simple keyword scoring
            for word in query.split():
                if word in doc_lower:
                    score += doc_lower.count(word)
            
            if score > 0:
                matches.append((score, item))
        
        # Sort by score and take top N
        matches.sort(reverse=True, key=lambda x: x[0])
        for score, item in matches[:n_results]:
            results["ids"][0].append(item["id"])
            results["documents"][0].append(item["document"])
            results["metadatas"][0].append(item["metadata"])
            results["distances"][0].append(1.0 / (1.0 + score))  # Convert score to distance
        
        return results
    
    def get(self, ids: List[str] = None, where: Dict = None, limit: int = None) -> Dict:
        """Get items from collection"""
        results = {"ids": [], "documents": [], "metadatas": []}
        
        if ids:
            for item_id in ids:
                if item_id in self._data:
                    item = self._data[item_id]
                    results["ids"].append(item["id"])
                    results["documents"].append(item["document"])
                    results["metadatas"].append(item["metadata"])
        else:
            # Return all items
            for item in list(self._data.values())[:limit] if limit else self._data.values():
                results["ids"].append(item["id"])
                results["documents"].append(item["document"])
                results["metadatas"].append(item["metadata"])
        
        return results
    
    def delete(self, ids: List[str] = None, where: Dict = None):
        """Delete items from collection"""
        if ids:
            for item_id in ids:
                self._data.pop(item_id, None)
            self._save()
    
    def clear(self):
        """Clear all data"""
        self._data.clear()
        self._save()
    
    def count(self) -> int:
        """Get item count"""
        return len(self._data)

# Context manager (maintains backward compatibility)
@contextmanager
def get_chroma_client(path: Optional[str] = None):
    """Context manager for RAGFlow client with automatic cleanup"""
    client = RAGFlowClient(persist_directory=path or "./ragflow_data")
    try:
        yield client
    finally:
        # Cleanup if needed
        pass

# Global singleton
_global_client = None

def get_global_chroma_client():
    """Get or create global RAGFlow client"""
    global _global_client
    if _global_client is None:
        _global_client = RAGFlowClient()
    return _global_client

def cleanup_global_chroma_client():
    """Cleanup global client"""
    global _global_client
    _global_client = None

import atexit
atexit.register(cleanup_global_chroma_client)
