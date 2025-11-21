"""
Design Reuse Agent
Identify reusable design blocks and component libraries
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict


class DesignReuseAgent:
    """Identifies reusable design blocks and component libraries."""
    
    def analyze_reusability(
        self,
        bom_items: List[Dict[str, Any]],
        existing_designs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze design for reusability and identify reusable blocks.
        
        Args:
            bom_items: List of BOM items
            existing_designs: Optional list of existing designs to compare against
        
        Returns:
            Dictionary with reusability analysis:
            {
                "reusable_blocks": List[Dict],
                "component_libraries": Dict,
                "reuse_recommendations": List[str],
                "standardization_score": float
            }
        """
        # Identify common design blocks
        reusable_blocks = self._identify_reusable_blocks(bom_items)
        
        # Analyze component libraries
        component_libraries = self._analyze_component_libraries(bom_items)
        
        # Compare with existing designs if provided
        similarity_analysis = None
        if existing_designs:
            similarity_analysis = self._compare_with_existing_designs(bom_items, existing_designs)
        
        # Calculate standardization score
        standardization_score = self._calculate_standardization_score(bom_items, component_libraries)
        
        # Generate recommendations
        reuse_recommendations = self._generate_reuse_recommendations(
            reusable_blocks, component_libraries, standardization_score
        )
        
        return {
            "reusable_blocks": reusable_blocks,
            "component_libraries": component_libraries,
            "similarity_analysis": similarity_analysis,
            "standardization_score": round(standardization_score, 1),
            "reuse_recommendations": reuse_recommendations
        }
    
    def _identify_reusable_blocks(self, bom_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify reusable design blocks."""
        blocks = []
        
        # Power management block
        power_components = [item for item in bom_items 
                          if "regulator" in str(item.get("part_data", {}).get("category", "")).lower() or
                             "power" in str(item.get("part_data", {}).get("category", "")).lower()]
        if power_components:
            blocks.append({
                "block_type": "power_management",
                "components": [item.get("part_data", {}).get("id") for item in power_components],
                "description": "Power regulation and management",
                "reusability": "high"
            })
        
        # Communication block
        comm_components = [item for item in bom_items 
                          if any(iface in str(item.get("part_data", {}).get("interface_type", [])).lower() 
                                for iface in ["usb", "uart", "i2c", "spi", "ethernet", "wifi", "bluetooth"])]
        if comm_components:
            blocks.append({
                "block_type": "communication",
                "components": [item.get("part_data", {}).get("id") for item in comm_components],
                "description": "Communication interfaces",
                "reusability": "high"
            })
        
        # Sensor block
        sensor_components = [item for item in bom_items 
                           if "sensor" in str(item.get("part_data", {}).get("category", "")).lower()]
        if sensor_components:
            blocks.append({
                "block_type": "sensing",
                "components": [item.get("part_data", {}).get("id") for item in sensor_components],
                "description": "Sensor interfaces",
                "reusability": "medium"
            })
        
        # Protection block
        protection_components = [item for item in bom_items 
                               if "protection" in str(item.get("part_data", {}).get("category", "")).lower() or
                                  "esd" in str(item.get("part_data", {}).get("category", "")).lower() or
                                  "tvs" in str(item.get("part_data", {}).get("id", "")).lower()]
        if protection_components:
            blocks.append({
                "block_type": "protection",
                "components": [item.get("part_data", {}).get("id") for item in protection_components],
                "description": "ESD and overvoltage protection",
                "reusability": "high"
            })
        
        return blocks
    
    def _analyze_component_libraries(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze component libraries and standardization."""
        manufacturers = defaultdict(int)
        package_types = defaultdict(int)
        categories = defaultdict(int)
        
        for item in bom_items:
            part = item.get("part_data", {})
            manufacturer = part.get("manufacturer", "")
            package = part.get("package", "")
            category = part.get("category", "")
            
            if manufacturer:
                manufacturers[manufacturer] += item.get("quantity", 1)
            if package:
                package_types[package] += item.get("quantity", 1)
            if category:
                categories[category] += item.get("quantity", 1)
        
        # Calculate diversity metrics
        total_components = sum(item.get("quantity", 1) for item in bom_items)
        manufacturer_diversity = len(manufacturers)
        package_diversity = len(package_types)
        
        # Identify most common manufacturers
        top_manufacturers = sorted(manufacturers.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "manufacturer_distribution": dict(manufacturers),
            "top_manufacturers": [{"name": m, "count": c} for m, c in top_manufacturers],
            "package_distribution": dict(package_types),
            "category_distribution": dict(categories),
            "diversity_metrics": {
                "manufacturer_count": manufacturer_diversity,
                "package_count": package_diversity,
                "total_components": total_components
            },
            "standardization_recommendation": "Consider standardizing on fewer manufacturers" if manufacturer_diversity > 10 else "Manufacturer diversity is reasonable"
        }
    
    def _compare_with_existing_designs(
        self,
        bom_items: List[Dict[str, Any]],
        existing_designs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare current design with existing designs."""
        current_part_ids = {item.get("part_data", {}).get("id") for item in bom_items}
        
        similarities = []
        for design in existing_designs:
            design_bom = design.get("bom_items", [])
            design_part_ids = {item.get("part_data", {}).get("id") for item in design_bom}
            
            common_parts = current_part_ids.intersection(design_part_ids)
            similarity_percentage = (len(common_parts) / len(current_part_ids) * 100) if current_part_ids else 0
            
            similarities.append({
                "design_name": design.get("metadata", {}).get("name", "Unknown"),
                "common_parts": len(common_parts),
                "similarity_percentage": round(similarity_percentage, 1),
                "reusable_components": list(common_parts)
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity_percentage"], reverse=True)
        
        return {
            "similar_designs": similarities[:5],  # Top 5 most similar
            "average_similarity": sum(s["similarity_percentage"] for s in similarities) / len(similarities) if similarities else 0
        }
    
    def _calculate_standardization_score(
        self,
        bom_items: List[Dict[str, Any]],
        component_libraries: Dict[str, Any]
    ) -> float:
        """Calculate standardization score (0-100)."""
        score = 100.0
        
        # Penalize high manufacturer diversity
        manufacturer_count = component_libraries.get("diversity_metrics", {}).get("manufacturer_count", 0)
        if manufacturer_count > 10:
            score -= (manufacturer_count - 10) * 2
        
        # Penalize high package diversity
        package_count = component_libraries.get("diversity_metrics", {}).get("package_count", 0)
        if package_count > 15:
            score -= (package_count - 15) * 1
        
        return max(0.0, min(100.0, score))
    
    def _generate_reuse_recommendations(
        self,
        reusable_blocks: List[Dict[str, Any]],
        component_libraries: Dict[str, Any],
        standardization_score: float
    ) -> List[str]:
        """Generate reuse recommendations."""
        recommendations = []
        
        if reusable_blocks:
            recommendations.append(f"Identified {len(reusable_blocks)} reusable design block(s) - consider creating library modules")
        
        top_manufacturers = component_libraries.get("top_manufacturers", [])
        if top_manufacturers:
            top_manufacturer = top_manufacturers[0]
            recommendations.append(f"Most common manufacturer: {top_manufacturer['name']} ({top_manufacturer['count']} components) - consider standardizing")
        
        if standardization_score < 70:
            recommendations.append("Low standardization score - consider reducing manufacturer and package diversity")
        
        if not recommendations:
            recommendations.append("Design shows good standardization and reusability potential")
        
        return recommendations

