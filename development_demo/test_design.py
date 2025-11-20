"""
Simple test script for the PCB Design Generator
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.design_orchestrator import DesignOrchestrator

def test_design_generation():
    """Test the design generation with example query."""
    query = "temperature sensor with wifi and 5V-USBC"
    
    print(f"Testing design generation with query: '{query}'")
    print("=" * 60)
    
    try:
        orchestrator = DesignOrchestrator()
        design = orchestrator.generate_design(query)
        
        if "error" in design:
            print(f"ERROR: {design['error']}")
            return False
        
        print("\n✓ Design generated successfully!")
        print(f"\nSelected Parts: {len(design.get('selected_parts', {}))}")
        for block_name, part_data in design.get('selected_parts', {}).items():
            print(f"  - {block_name}: {part_data.get('name', 'N/A')} ({part_data.get('mfr_part_number', 'N/A')})")
        
        print(f"\nExternal Components: {len(design.get('external_components', []))}")
        for comp in design.get('external_components', [])[:5]:  # Show first 5
            print(f"  - {comp.get('value', 'N/A')} {comp.get('type', 'N/A')} ({comp.get('purpose', '')})")
        
        print(f"\nConnections: {len(design.get('connections', []))} nets")
        for net in design.get('connections', [])[:3]:  # Show first 3
            print(f"  - {net.get('net_name', 'N/A')}: {len(net.get('connections', []))} connections")
        
        print(f"\nBOM Items: {len(design.get('bom', []))}")
        for item in design.get('bom', [])[:5]:  # Show first 5
            print(f"  - {item.get('designator', 'N/A')}: {item.get('description', 'N/A')} (Qty: {item.get('qty', 1)})")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_design_generation()
    sys.exit(0 if success else 1)

