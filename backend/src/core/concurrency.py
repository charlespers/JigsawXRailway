"""
Concurrency Control
Enterprise-grade concurrency limits and resource monitoring
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# Global concurrency limits
MAX_CONCURRENT_LLM_CALLS = 5  # Max parallel LLM API calls
MAX_CONCURRENT_AGENT_OPERATIONS = 10  # Max parallel agent operations
MAX_CONCURRENT_DATASHEET_ENRICHMENTS = 3  # Max parallel datasheet enrichments

# Semaphores for concurrency control
llm_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)
agent_semaphore = asyncio.Semaphore(MAX_CONCURRENT_AGENT_OPERATIONS)
datasheet_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DATASHEET_ENRICHMENTS)

# Resource monitoring
_resource_stats = {
    "llm_calls": {"active": 0, "total": 0, "peak": 0},
    "agent_ops": {"active": 0, "total": 0, "peak": 0},
    "datasheet_ops": {"active": 0, "total": 0, "peak": 0},
}
_stats_lock = Lock()


def get_resource_stats() -> Dict[str, Any]:
    """Get current resource usage statistics."""
    with _stats_lock:
        return {
            "llm": {
                "active": _resource_stats["llm_calls"]["active"],
                "total": _resource_stats["llm_calls"]["total"],
                "peak": _resource_stats["llm_calls"]["peak"],
                "limit": MAX_CONCURRENT_LLM_CALLS,
                "utilization": _resource_stats["llm_calls"]["active"] / MAX_CONCURRENT_LLM_CALLS * 100
            },
            "agent_ops": {
                "active": _resource_stats["agent_ops"]["active"],
                "total": _resource_stats["agent_ops"]["total"],
                "peak": _resource_stats["agent_ops"]["peak"],
                "limit": MAX_CONCURRENT_AGENT_OPERATIONS,
                "utilization": _resource_stats["agent_ops"]["active"] / MAX_CONCURRENT_AGENT_OPERATIONS * 100
            },
            "datasheet_ops": {
                "active": _resource_stats["datasheet_ops"]["active"],
                "total": _resource_stats["datasheet_ops"]["total"],
                "peak": _resource_stats["datasheet_ops"]["peak"],
                "limit": MAX_CONCURRENT_DATASHEET_ENRICHMENTS,
                "utilization": _resource_stats["datasheet_ops"]["active"] / MAX_CONCURRENT_DATASHEET_ENRICHMENTS * 100
            }
        }


async def with_llm_limit(coro):
    """Execute coroutine with LLM concurrency limit."""
    async with llm_semaphore:
        with _stats_lock:
            _resource_stats["llm_calls"]["active"] += 1
            _resource_stats["llm_calls"]["total"] += 1
            if _resource_stats["llm_calls"]["active"] > _resource_stats["llm_calls"]["peak"]:
                _resource_stats["llm_calls"]["peak"] = _resource_stats["llm_calls"]["active"]
        
        try:
            result = await coro
            return result
        finally:
            with _stats_lock:
                _resource_stats["llm_calls"]["active"] -= 1


async def with_agent_limit(coro):
    """Execute coroutine with agent operation concurrency limit."""
    async with agent_semaphore:
        with _stats_lock:
            _resource_stats["agent_ops"]["active"] += 1
            _resource_stats["agent_ops"]["total"] += 1
            if _resource_stats["agent_ops"]["active"] > _resource_stats["agent_ops"]["peak"]:
                _resource_stats["agent_ops"]["peak"] = _resource_stats["agent_ops"]["active"]
        
        try:
            result = await coro
            return result
        finally:
            with _stats_lock:
                _resource_stats["agent_ops"]["active"] -= 1


async def with_datasheet_limit(coro):
    """Execute coroutine with datasheet enrichment concurrency limit."""
    async with datasheet_semaphore:
        with _stats_lock:
            _resource_stats["datasheet_ops"]["active"] += 1
            _resource_stats["datasheet_ops"]["total"] += 1
            if _resource_stats["datasheet_ops"]["active"] > _resource_stats["datasheet_ops"]["peak"]:
                _resource_stats["datasheet_ops"]["peak"] = _resource_stats["datasheet_ops"]["active"]
        
        try:
            result = await coro
            return result
        finally:
            with _stats_lock:
                _resource_stats["datasheet_ops"]["active"] -= 1


class PriorityQueue:
    """Priority queue for task execution with priority levels."""
    
    def __init__(self):
        self._high_priority: asyncio.Queue = asyncio.Queue()
        self._normal_priority: asyncio.Queue = asyncio.Queue()
        self._low_priority: asyncio.Queue = asyncio.Queue()
    
    async def put(self, item: Any, priority: str = "normal"):
        """Add item to queue with specified priority."""
        if priority == "high":
            await self._high_priority.put(item)
        elif priority == "low":
            await self._low_priority.put(item)
        else:
            await self._normal_priority.put(item)
    
    async def get(self) -> Any:
        """Get next item from queue (high priority first)."""
        # Check high priority first
        if not self._high_priority.empty():
            return await self._high_priority.get()
        # Then normal priority
        if not self._normal_priority.empty():
            return await self._normal_priority.get()
        # Finally low priority
        return await self._low_priority.get()
    
    def empty(self) -> bool:
        """Check if all queues are empty."""
        return (self._high_priority.empty() and 
                self._normal_priority.empty() and 
                self._low_priority.empty())

