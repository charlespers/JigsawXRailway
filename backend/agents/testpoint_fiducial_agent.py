"""
Test Point and Fiducial Agent
Automatically generates test points for power rails and fiducial marks for automated assembly
"""

from typing import Dict, Any, List, Set, Optional
from collections import defaultdict


class TestPointFiducialAgent:
    """Agent that generates test points and fiducial marks for PCB designs."""
    
    def __init__(self):
        pass
    
    def generate_test_points(
        self,
        connections: List[Dict[str, Any]],
        selected_parts: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate test points for all power rails and critical signals.
        
        Args:
            connections: List of net connections
            selected_parts: Dictionary of selected parts
        
        Returns:
            List of test point entries with designator, net_name, and location info
        """
        test_points = []
        test_point_counter = 1
        
        # Identify power rails that need test points
        power_nets = set()
        critical_signals = set()
        
        for net in connections:
            net_name = net.get("net_name", "")
            net_class = net.get("net_class", "")
            
            # Add all power and ground nets
            if net_class in ["power", "ground"]:
                power_nets.add(net_name)
            
            # Add critical signals (clocks, reset, enable)
            if net_class == "clock" or "RESET" in net_name.upper() or "ENABLE" in net_name.upper() or "EN" in net_name.upper():
                critical_signals.add(net_name)
        
        # Generate test points for power rails
        for net_name in sorted(power_nets):
            test_points.append({
                "designator": f"TP{test_point_counter}",
                "net_name": net_name,
                "type": "power" if net_name != "GND" else "ground",
                "description": f"Test point for {net_name}",
                "package": "TEST_POINT_0402",  # Standard test point package
                "footprint": "TESTPOINT_0402",
                "assembly_side": "top",
                "recommended_location": "edge_of_board",  # Place near board edge for easy access
                "notes": f"Add test point for {net_name} rail - place near board edge for debugging"
            })
            test_point_counter += 1
        
        # Generate test points for critical signals (limit to 3 most critical)
        critical_list = sorted(list(critical_signals))[:3]
        for net_name in critical_list:
            test_points.append({
                "designator": f"TP{test_point_counter}",
                "net_name": net_name,
                "type": "signal",
                "description": f"Test point for {net_name}",
                "package": "TEST_POINT_0402",
                "footprint": "TESTPOINT_0402",
                "assembly_side": "top",
                "recommended_location": "near_component",
                "notes": f"Test point for {net_name} signal - place near related component"
            })
            test_point_counter += 1
        
        return test_points
    
    def generate_fiducials(
        self,
        board_size: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate fiducial marks for automated assembly.
        
        IPC standard requires minimum 3 fiducials:
        - 2 on opposite corners (diagonal)
        - 1 additional for orientation
        
        Args:
            board_size: Optional dict with "width" and "height" in mm
        
        Returns:
            List of fiducial entries
        """
        fiducials = []
        
        # Standard fiducial specifications (IPC-7351)
        fiducial_spec = {
            "package": "FIDUCIAL_1MM",
            "footprint": "FIDUCIAL_1MM",
            "diameter_mm": 1.0,
            "solder_mask_opening_mm": 2.0,
            "clearance_mm": 2.0,  # Clearance from board edge
            "assembly_side": "top"
        }
        
        # Generate 3 fiducials (minimum for automated assembly)
        # FID1: Top-left corner
        fiducials.append({
            "designator": "FID1",
            "type": "fiducial",
            "description": "Fiducial mark - top-left corner",
            "package": fiducial_spec["package"],
            "footprint": fiducial_spec["footprint"],
            "diameter_mm": fiducial_spec["diameter_mm"],
            "solder_mask_opening_mm": fiducial_spec["solder_mask_opening_mm"],
            "clearance_mm": fiducial_spec["clearance_mm"],
            "assembly_side": fiducial_spec["assembly_side"],
            "recommended_location": "top_left_corner",
            "notes": "Place 2mm from top and left edges. Required for automated assembly."
        })
        
        # FID2: Bottom-right corner (diagonal from FID1)
        fiducials.append({
            "designator": "FID2",
            "type": "fiducial",
            "description": "Fiducial mark - bottom-right corner",
            "package": fiducial_spec["package"],
            "footprint": fiducial_spec["footprint"],
            "diameter_mm": fiducial_spec["diameter_mm"],
            "solder_mask_opening_mm": fiducial_spec["solder_mask_opening_mm"],
            "clearance_mm": fiducial_spec["clearance_mm"],
            "assembly_side": fiducial_spec["assembly_side"],
            "recommended_location": "bottom_right_corner",
            "notes": "Place 2mm from bottom and right edges. Required for automated assembly."
        })
        
        # FID3: Additional fiducial for orientation (top-right)
        fiducials.append({
            "designator": "FID3",
            "type": "fiducial",
            "description": "Fiducial mark - top-right corner (orientation)",
            "package": fiducial_spec["package"],
            "footprint": fiducial_spec["footprint"],
            "diameter_mm": fiducial_spec["diameter_mm"],
            "solder_mask_opening_mm": fiducial_spec["solder_mask_opening_mm"],
            "clearance_mm": fiducial_spec["clearance_mm"],
            "assembly_side": fiducial_spec["assembly_side"],
            "recommended_location": "top_right_corner",
            "notes": "Place 2mm from top and right edges. Provides orientation reference."
        })
        
        return fiducials
    
    def add_test_points_to_bom(
        self,
        bom_items: List[Dict[str, Any]],
        test_points: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add test points to BOM items list.
        
        Args:
            bom_items: Existing BOM items
            test_points: List of test point entries
        
        Returns:
            Updated BOM items with test points added
        """
        for tp in test_points:
            bom_items.append({
                "designator": tp["designator"],
                "qty": 1,
                "manufacturer": "Generic",
                "mfr_part_number": "TEST_POINT_0402",
                "description": tp["description"],
                "category": "test_point",
                "package": tp["package"],
                "footprint": tp["footprint"],
                "value": "",
                "tolerance": "",
                "temperature_rating": "",
                "rohs_compliant": True,
                "lifecycle_status": "active",
                "availability_status": "in_stock",
                "lead_time_days": None,
                "distributor_part_numbers": {},
                "mounting_type": "SMT",
                "assembly_side": tp["assembly_side"],
                "msl_level": None,
                "datasheet_url": "",
                "alternate_part_numbers": [],
                "assembly_notes": tp.get("notes", ""),
                "test_point": True,
                "fiducial": False,
                "unit_cost": 0.01,  # Very low cost for test points
                "extended_cost": 0.01,
                "notes": tp.get("notes", "")
            })
        
        return bom_items
    
    def add_fiducials_to_bom(
        self,
        bom_items: List[Dict[str, Any]],
        fiducials: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add fiducial marks to BOM items list.
        
        Args:
            bom_items: Existing BOM items
            fiducials: List of fiducial entries
        
        Returns:
            Updated BOM items with fiducials added
        """
        for fid in fiducials:
            bom_items.append({
                "designator": fid["designator"],
                "qty": 1,
                "manufacturer": "Generic",
                "mfr_part_number": "FIDUCIAL_1MM",
                "description": fid["description"],
                "category": "fiducial",
                "package": fid["package"],
                "footprint": fid["footprint"],
                "value": "",
                "tolerance": "",
                "temperature_rating": "",
                "rohs_compliant": True,
                "lifecycle_status": "active",
                "availability_status": "in_stock",
                "lead_time_days": None,
                "distributor_part_numbers": {},
                "mounting_type": "SMT",
                "assembly_side": fid["assembly_side"],
                "msl_level": None,
                "datasheet_url": "",
                "alternate_part_numbers": [],
                "assembly_notes": fid.get("notes", ""),
                "test_point": False,
                "fiducial": True,
                "unit_cost": 0.01,  # Very low cost for fiducials
                "extended_cost": 0.01,
                "notes": fid.get("notes", "")
            })
        
        return bom_items

