"""
Core Orchestration Service
Centralized orchestrator with dependency injection and enterprise features
"""

import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.design_orchestrator import DesignOrchestrator
from agents.query_router_agent import QueryRouterAgent
from core.cache import get_cache_manager
from core.exceptions import OrchestrationException, AgentException
from api.data_mapper import part_data_to_part_object

logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Enterprise-grade orchestration service with dependency injection,
    caching, and error handling.
    """
    
    def __init__(
        self,
        requirements_agent=None,
        architecture_agent=None,
        part_search_agent=None,
        compatibility_agent=None,
        datasheet_agent=None,
        output_generator=None,
        intermediary_agent=None,
        reasoning_agent=None,
        design_analyzer=None,
        query_router=None,
        cache_manager=None
    ):
        """
        Initialize orchestrator service with dependency injection.
        
        Args:
            *_agent: Optional agent instances (will create defaults if None)
            cache_manager: Optional cache manager (will use global if None)
        """
        # Use dependency injection or create defaults
        self._requirements_agent = requirements_agent
        self._architecture_agent = architecture_agent
        self._part_search_agent = part_search_agent
        self._compatibility_agent = compatibility_agent
        self._datasheet_agent = datasheet_agent
        self._output_generator = output_generator
        self._intermediary_agent = intermediary_agent
        self._reasoning_agent = reasoning_agent
        self._design_analyzer = design_analyzer
        self._query_router = query_router
        
        # Cache manager
        self.cache_manager = cache_manager or get_cache_manager()
        
        # Base orchestrator (will be initialized lazily)
        self._orchestrator: Optional[DesignOrchestrator] = None
    
    @property
    def orchestrator(self) -> DesignOrchestrator:
        """Get or create base orchestrator"""
        if self._orchestrator is None:
            # Create base orchestrator
            self._orchestrator = DesignOrchestrator()
            
            # Override agents if provided via dependency injection
            if self._requirements_agent:
                self._orchestrator.requirements_agent = self._requirements_agent
            if self._architecture_agent:
                self._orchestrator.architecture_agent = self._architecture_agent
            if self._part_search_agent:
                self._orchestrator.part_search_agent = self._part_search_agent
            if self._compatibility_agent:
                self._orchestrator.compatibility_agent = self._compatibility_agent
            if self._datasheet_agent:
                self._orchestrator.datasheet_agent = self._datasheet_agent
            if self._output_generator:
                self._orchestrator.output_generator = self._output_generator
            if self._intermediary_agent:
                self._orchestrator.intermediary_agent = self._intermediary_agent
            if self._reasoning_agent:
                self._orchestrator.reasoning_agent = self._reasoning_agent
            if self._design_analyzer:
                self._orchestrator.design_analyzer = self._design_analyzer
        
        return self._orchestrator
    
    @property
    def query_router(self) -> QueryRouterAgent:
        """Get or create query router"""
        if self._query_router is None:
            self._query_router = QueryRouterAgent()
        return self._query_router
    
    def create_streaming_orchestrator(
        self,
        on_reasoning: Optional[Callable] = None,
        on_selection: Optional[Callable] = None
    ) -> 'StreamingOrchestrator':
        """
        Create a streaming orchestrator with callbacks.
        
        Args:
            on_reasoning: Callback for reasoning events
            on_selection: Callback for selection events
        
        Returns:
            StreamingOrchestrator instance
        """
        from api.server import StreamingOrchestrator
        return StreamingOrchestrator(on_reasoning=on_reasoning, on_selection=on_selection)
    
    def get_cached_requirements(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached requirements if available"""
        cache_key = f"requirements:{hash(query)}"
        return self.cache_manager.get(cache_key)
    
    def cache_requirements(self, query: str, requirements: Dict[str, Any], ttl: int = 3600):
        """Cache requirements extraction result"""
        cache_key = f"requirements:{hash(query)}"
        self.cache_manager.set(cache_key, requirements, ttl)
    
    def get_cached_part_search(
        self,
        category: str,
        constraints: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Optional[list]:
        """Get cached part search results if available"""
        cache_key = f"part_search:{hash(str((category, constraints, preferences)))}"
        return self.cache_manager.get(cache_key)
    
    def cache_part_search(
        self,
        category: str,
        constraints: Dict[str, Any],
        preferences: Dict[str, Any],
        results: list,
        ttl: int = 7200
    ):
        """Cache part search results"""
        cache_key = f"part_search:{hash(str((category, constraints, preferences)))}"
        self.cache_manager.set(cache_key, results, ttl)
    
    def get_cached_compatibility(
        self,
        part1_id: str,
        part2_id: str,
        connection_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached compatibility check result"""
        cache_key = f"compatibility:{part1_id}:{part2_id}:{connection_type}"
        return self.cache_manager.get(cache_key)
    
    def cache_compatibility(
        self,
        part1_id: str,
        part2_id: str,
        connection_type: str,
        result: Dict[str, Any],
        ttl: int = 86400  # 24 hours
    ):
        """Cache compatibility check result"""
        cache_key = f"compatibility:{part1_id}:{part2_id}:{connection_type}"
        self.cache_manager.set(cache_key, result, ttl)
    
    def clear_design_cache(self, design_id: Optional[str] = None):
        """Clear cache related to a design"""
        if design_id:
            pattern = f"*:{design_id}:*"
        else:
            pattern = "requirements:*"
        self.cache_manager.clear(pattern)


# Global orchestrator service instance
_orchestrator_service: Optional[OrchestratorService] = None


def get_orchestrator_service() -> OrchestratorService:
    """Get or create global orchestrator service"""
    global _orchestrator_service
    if _orchestrator_service is None:
        _orchestrator_service = OrchestratorService()
    return _orchestrator_service

