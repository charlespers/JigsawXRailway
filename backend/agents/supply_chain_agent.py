"""
Supply Chain Risk Analysis Agent
Analyzes supply chain risks and availability
"""

from typing import List, Dict, Any


class SupplyChainAgent:
    """Analyzes supply chain risks for BOM items."""
    
    def analyze_supply_chain(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze supply chain risks for BOM items.
        
        Args:
            bom_items: List of BOM items with part data
        
        Returns:
            Dictionary with supply chain analysis:
            {
                "risks": List[Dict],
                "warnings": List[str],
                "risk_score": float,
                "recommendations": List[str]
            }
        """
        risks = []
        warnings = []
        risk_score = 0.0
        
        from utils.cost_utils import safe_extract_quantity
        
        for item in bom_items:
            part = item.get("part_data", {})
            quantity = safe_extract_quantity(item.get("quantity", 1), default=1)
            
            part_risks = []
            item_risk_score = 0.0
            
            # Availability status
            availability = part.get("availability_status")
            if availability == "out_of_stock":
                part_risks.append("Out of stock")
                item_risk_score += 30.0
                warnings.append(f"{part.get('name')} is out of stock")
            elif availability == "limited_stock":
                part_risks.append("Limited stock")
                item_risk_score += 15.0
            
            # Lifecycle status
            lifecycle = part.get("lifecycle_status")
            if lifecycle == "obsolete":
                part_risks.append("Obsolete")
                item_risk_score += 40.0
                warnings.append(f"{part.get('name')} is obsolete")
            elif lifecycle == "not_recommended":
                part_risks.append("Not recommended for new designs")
                item_risk_score += 25.0
                warnings.append(f"{part.get('name')} is not recommended for new designs")
            elif lifecycle == "end_of_life":
                part_risks.append("End of life")
                item_risk_score += 35.0
                warnings.append(f"{part.get('name')} is end of life")
            
            # Lead time
            lead_time = part.get("lead_time_days")
            if lead_time and lead_time > 30:
                part_risks.append(f"Long lead time ({lead_time} days)")
                item_risk_score += 10.0
                warnings.append(f"{part.get('name')} has {lead_time} day lead time")
            
            # MOQ
            moq = part.get("moq")
            if moq and moq > quantity:
                part_risks.append(f"MOQ ({moq}) exceeds required quantity ({quantity})")
                item_risk_score += 5.0
            
            # Single source risk (check if manufacturer is unique)
            manufacturer = part.get("manufacturer")
            if manufacturer:
                # This is simplified - in real system, would check database
                part_risks.append(f"Single manufacturer: {manufacturer}")
                item_risk_score += 5.0
            
            if part_risks:
                risks.append({
                    "part_id": part.get("id"),
                    "part_name": part.get("name"),
                    "risks": part_risks,
                    "risk_score": item_risk_score,
                    "quantity": quantity
                })
                # quantity already extracted safely above
                risk_score += item_risk_score * quantity
        
        # Normalize risk score (0-100)
        total_items = len(bom_items)
        if total_items > 0:
            risk_score = min(100.0, risk_score / total_items)
        
        # Generate recommendations
        recommendations = []
        
        if any(r.get("risk_score", 0) > 30 for r in risks):
            recommendations.append("Consider finding alternatives for high-risk parts")
        
        if any("obsolete" in str(r.get("risks", [])) for r in risks):
            recommendations.append("Replace obsolete parts with active alternatives")
        
        if any("Out of stock" in str(r.get("risks", [])) for r in risks):
            recommendations.append("Find in-stock alternatives for out-of-stock parts")
        
        if any(r.get("lead_time_days", 0) > 30 for r in risks):
            recommendations.append("Consider parts with shorter lead times for production planning")
        
        return {
            "risks": risks,
            "warnings": warnings,
            "risk_score": risk_score,
            "recommendations": recommendations
        }

