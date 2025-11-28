"""
Cache Manager
In-memory caching with optional Redis support for distributed systems
"""

import hashlib
import json
import time
from typing import Any, Optional, Dict
from threading import Lock

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheManager:
    """Cache manager with in-memory and optional Redis backend."""
    
    def __init__(self, use_redis: bool = False, redis_url: str = "redis://localhost:6379"):
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.memory_cache: Dict[str, tuple[Any, float]] = {}
        self.lock = Lock()
        
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed, falling back to memory cache: {e}")
                self.use_redis = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self.use_redis:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        
        # Fallback to memory cache
        with self.lock:
            if key in self.memory_cache:
                value, expiry = self.memory_cache[key]
                if expiry == 0 or time.time() < expiry:
                    return value
                else:
                    del self.memory_cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with TTL (time to live in seconds)."""
        expiry = time.time() + ttl if ttl > 0 else 0
        
        if self.use_redis:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
                return
            except Exception:
                pass
        
        # Fallback to memory cache
        with self.lock:
            self.memory_cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if self.use_redis:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
        
        with self.lock:
            if key in self.memory_cache:
                del self.memory_cache[key]
    
    def clear(self) -> None:
        """Clear all cache."""
        if self.use_redis:
            try:
                self.redis_client.flushdb()
            except Exception:
                pass
        
        with self.lock:
            self.memory_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "backend": "redis" if self.use_redis else "memory",
            "memory_size": len(self.memory_cache),
        }
        
        if self.use_redis:
            try:
                stats["redis_size"] = self.redis_client.dbsize()
            except Exception:
                pass
        
        return stats


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create cache manager singleton."""
    global _cache_manager
    if _cache_manager is None:
        # Try Redis first, fallback to memory
        use_redis = False
        redis_url = "redis://localhost:6379"
        
        try:
            import os
            redis_url = os.getenv("REDIS_URL", redis_url)
            use_redis = os.getenv("USE_REDIS", "false").lower() == "true"
        except Exception:
            pass
        
        _cache_manager = CacheManager(use_redis=use_redis, redis_url=redis_url)
    
    return _cache_manager
