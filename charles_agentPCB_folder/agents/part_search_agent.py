"""
Part Search & Ranking Agent
Queries database and ranks candidate parts
"""

from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.part_database import search_parts, get_part_by_id


class PartSearchAgent:
    """Agent that searches and ranks parts from the database."""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager
    
    def search_and_rank(
        self,
        category: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for parts and rank them by relevance.
        
        Args:
            category: Part category filter
            constraints: Hard constraints (must satisfy)
            preferences: Soft preferences (scored)
        
        Returns:
            List of parts with scores, sorted by score (highest first)
        """
        # Check cache first
        if self.cache_manager:
            import hashlib
            import json
            cache_key_data = {
                "category": category,
                "constraints": constraints,
                "preferences": preferences,
            }
            cache_key_str = json.dumps(cache_key_data, sort_keys=True)
            cache_key = f"part_search:{hashlib.sha256(cache_key_str.encode()).hexdigest()[:16]}"
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        # Search parts matching constraints
        candidates = search_parts(category=category, constraints=constraints)
        
        # Score each candidate
        scored_parts = []
        for part in candidates:
            score = self._calculate_score(part, constraints, preferences)
            scored_parts.append({
                "part": part,
                "score": score
            })
        
        # Sort by score (highest first)
        scored_parts.sort(key=lambda x: x["score"], reverse=True)
        
        # Cache result
        if self.cache_manager:
            import hashlib
            import json
            cache_key_data = {
                "category": category,
                "constraints": constraints,
                "preferences": preferences,
            }
            cache_key_str = json.dumps(cache_key_data, sort_keys=True)
            cache_key = f"part_search:{hashlib.sha256(cache_key_str.encode()).hexdigest()[:16]}"
            self.cache_manager.set(cache_key, scored_parts, ttl=7200)  # 2 hours
        
        return scored_parts
    
    def _calculate_score(
        self,
        part: Dict[str, Any],
        constraints: Optional[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate a score for a part based on constraints and preferences.
        Higher score = better match.
        """
        score = 100.0  # Base score
        
        if not preferences:
            return score
        
        # Availability preference
        if "availability" in preferences:
            pref_avail = preferences["availability"]
            part_avail = part.get("availability_status", "unknown")
            if pref_avail == "in_stock" and part_avail == "in_stock":
                score += 20
            elif part_avail != "in_stock":
                score -= 30
        
        # Lifecycle preference (avoid EOL)
        lifecycle = part.get("lifecycle_status", "unknown")
        if lifecycle == "active":
            score += 15
        elif lifecycle in ["eol", "obsolete"]:
            score -= 50
        
        # Cost preference
        if "cost_range" in preferences:
            cost_pref = preferences["cost_range"]
            cost_est = part.get("cost_estimate", {})
            cost_value = cost_est.get("value", 999)
            
            if cost_pref == "low" and cost_value < 1.0:
                score += 10
            elif cost_pref == "medium" and 1.0 <= cost_value < 5.0:
                score += 10
            elif cost_pref == "high":
                score += 5  # High cost is less preferred
        
        # Package preference
        if "package_type" in preferences:
            pref_pkg = preferences["package_type"]
            part_pkg = part.get("package", "").upper()
            
            if pref_pkg == "SMT" and ("QFN" in part_pkg or "SOT" in part_pkg or "0603" in part_pkg or "0805" in part_pkg):
                score += 10
            elif pref_pkg == "through_hole" and ("TO" in part_pkg or "DIP" in part_pkg):
                score += 10
        
        # Prefer integrated solutions (e.g., MCU with WiFi vs separate WiFi module)
        category = part.get("category", "")
        if "mcu_wifi" in category:
            score += 25  # Integrated is better
        elif "wifi_module" in category:
            score += 10  # Module is okay but requires external MCU
        
        # Prefer better documentation (has recommended external components)
        if part.get("recommended_external_components"):
            score += 15
        
        return score
    
    def get_top_candidate(
        self,
        category: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the top-ranked part candidate."""
        ranked = self.search_and_rank(category, constraints, preferences)
        if ranked:
            return ranked[0]["part"]
        return None

