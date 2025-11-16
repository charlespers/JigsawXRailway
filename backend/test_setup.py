"""
Quick test to verify setup is correct
"""

import sys
import os

def test_environment():
    """Test environment setup."""
    print("=" * 60)
    print("YC DEMO - Setup Verification")
    print("=" * 60)
    print()
    
    # Check Python version
    print(f"[TEST] Python Version: {sys.version}")
    if sys.version_info < (3, 10):
        print("  [FAIL] Python 3.10+ required")
        return False
    print("  [PASS] Python version OK")
    print()
    
    # Check XAI API key
    xai_key = os.getenv("XAI_API_KEY")
    if not xai_key:
        print("[TEST] XAI API Key")
        print("  [FAIL] XAI_API_KEY not set")
        print("  Required: export XAI_API_KEY='your_key'")
        return False
    print("[TEST] XAI API Key")
    print(f"  [PASS] Set (length: {len(xai_key)})")
    print()
    
    # Check imports
    print("[TEST] Dependencies")
    required = [
        "streamlit",
        "plotly",
        "numpy",
        "requests"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  [PASS] {package}")
        except ImportError:
            print(f"  [FAIL] {package}")
            missing.append(package)
    
    if missing:
        print()
        print(f"[FAIL] Missing: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    print()
    
    # Check file structure
    print("[TEST] File Structure")
    required_files = [
        "Home.py",
        "pages/Simulator.py",
        "components/component_agent.py",
        "components/component_registry.py",
        "utils/config.py",
        "utils/visualizer.py",
        "requirements.txt",
        "Dockerfile",
        "README.md"
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  [PASS] {file}")
        else:
            print(f"  [FAIL] {file}")
            all_exist = False
    
    if not all_exist:
        return False
    print()
    
    # Test component imports
    print("[TEST] Component Imports")
    try:
        sys.path.insert(0, os.getcwd())
        from components.component_agent import ComponentAgent
        from components.component_registry import ComponentRegistry
        from utils.config import load_config
        from utils.visualizer import create_pcb_sim_visualization
        print("  [PASS] All components import successfully")
    except Exception as e:
        print(f"  [FAIL] Import error: {e}")
        return False
    print()
    
    # Test config loading
    print("[TEST] Configuration")
    try:
        config = load_config()
        print(f"  [PASS] Config loaded")
        print(f"    Model: {config['xai_model']}")
        print(f"    Temperature: {config['xai_temperature']}")
        print(f"    Max Components: {config['max_components']}")
    except Exception as e:
        print(f"  [FAIL] Config error: {e}")
        return False
    print()
    
    # Summary
    print("=" * 60)
    print("[SUCCESS] All tests passed!")
    print()
    print("Ready to run:")
    print("  ./run.sh")
    print()
    print("Or manually:")
    print("  streamlit run Home.py")
    print()
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_environment()
    sys.exit(0 if success else 1)

