"""
Utility helper functions for nexus_evo
"""
import json
import hashlib
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from functools import wraps


def generate_id(prefix: str = "") -> str:
    """Generate unique ID with timestamp"""
    timestamp = str(time.time()).encode()
    hash_obj = hashlib.sha256(timestamp)
    short_hash = hash_obj.hexdigest()[:12]
    return f"{prefix}{short_hash}" if prefix else short_hash


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON with fallback"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, indent: int = 2) -> str:
    """Safely serialize to JSON"""
    try:
        return json.dumps(data, indent=indent, default=str)
    except (TypeError, ValueError) as e:
        return json.dumps({"error": str(e), "data_type": str(type(data))})


def timestamp() -> str:
    """Get current timestamp as ISO string"""
    return datetime.utcnow().isoformat()


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def parse_command(text: str) -> tuple[str, List[str], Dict[str, str]]:
    """
    Parse command string into command, args, and kwargs
    Example: "scan --target 192.168.1.1 --port 80" -> ("scan", [], {"target": "192.168.1.1", "port": "80"})
    """
    parts = text.split()
    if not parts:
        return "", [], {}
    
    command = parts[0]
    args = []
    kwargs = {}
    
    i = 1
    while i < len(parts):
        if parts[i].startswith('--'):
            key = parts[i][2:]
            if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                kwargs[key] = parts[i + 1]
                i += 2
            else:
                kwargs[key] = "true"
                i += 1
        else:
            args.append(parts[i])
            i += 1
    
    return command, args, kwargs


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result
