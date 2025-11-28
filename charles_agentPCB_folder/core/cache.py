"""
Caching layer for agent results and API responses
Supports both in-memory and Redis caching
"""

import hashlib
import json
import logging
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache only")


class CacheManager:
    """Manages caching for agent results and API responses"""
    
    def __init__(self, use_redis: bool = False, redis_url: str = None, default_ttl: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            use_redis: Whether to use Redis (requires redis package)
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.redis_client = None
        
        if use_redis and REDIS_AVAILABLE:
            try:
                if redis_url:
                    self.redis_client = redis.from_url(redis_url, decode_responses=True)
                else:
                    self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache only")
                self.redis_client = None
        else:
            logger.info("Using in-memory cache only")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        # Create a deterministic key from arguments
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # Fallback to memory
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            # Check expiration
            if entry["expires_at"] > time.time():
                return entry["value"]
            else:
                # Expired, remove it
                del self.memory_cache[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        
        # Try Redis first
        if self.redis_client:
            try:
                serialized = json.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # Fallback to memory
        self.memory_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        return True
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern"""
        count = 0
        
        if self.redis_client and pattern:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")
        
        if pattern:
            # Clear memory cache matching pattern
            keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.memory_cache[key]
                count += 1
        else:
            # Clear all memory cache
            count = len(self.memory_cache)
            self.memory_cache.clear()
        
        return count
    
    def cache_result(self, prefix: str, ttl: Optional[int] = None):
        """
        Decorator to cache function results.
        
        Usage:
            @cache_manager.cache_result("agent:requirements", ttl=3600)
            def extract_requirements(query: str):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached
                
                # Cache miss, execute function
                logger.debug(f"Cache miss: {cache_key}")
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        # Check for Redis configuration
        import os
        use_redis = os.getenv("USE_REDIS", "false").lower() == "true"
        redis_url = os.getenv("REDIS_URL")
        _cache_manager = CacheManager(use_redis=use_redis, redis_url=redis_url)
    return _cache_manager

