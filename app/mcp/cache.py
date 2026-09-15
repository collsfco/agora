import time
from typing import Dict, Any, Tuple, Optional

class MCPCacheManager:
    """In-memory TTLCache for MCP read tool responses."""
    def __init__(self):
        self._cache: Dict[Tuple[str, str, str], Tuple[float, Dict[str, Any]]] = {}

    def get(self, profile_id: str, tool_name: str, args_key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
        if ttl_seconds <= 0:
            return None
        
        key = (profile_id, tool_name, args_key)
        if key in self._cache:
            created_at, data = self._cache[key]
            if time.time() - created_at < ttl_seconds:
                return data
            else:
                del self._cache[key]
        return None

    def set(self, profile_id: str, tool_name: str, args_key: str, data: Dict[str, Any]):
        key = (profile_id, tool_name, args_key)
        self._cache[key] = (time.time(), data)

    def invalidate_domain(self, domain: str):
        """Invalidates cache entries for write events."""
        # Simple flush of cache on write actions
        self._cache.clear()

mcp_cache = MCPCacheManager()
