#!/usr/bin/env python3
"""
Comprehensive import check script
Run this to verify all imports work before deploying
"""
import sys
import traceback

def check_imports():
    """Check all critical imports"""
    errors = []
    
    checks = [
        ("app.main", "Main application"),
        ("app.api.routes", "API routes"),
        ("app.services.orchestrator", "Design orchestrator"),
        ("app.domain.part_database", "Part database"),
        ("app.core.config", "Configuration"),
        ("app.agents.base", "Base agent"),
        ("app.agents.compatibility", "Compatibility agent"),
        ("app.agents.intelligent_matcher", "Intelligent matcher"),
        ("app.agents.supply_chain_intelligence", "Supply chain agent"),
        ("app.agents.design_templates", "Design templates"),
    ]
    
    for module_name, description in checks:
        try:
            __import__(module_name)
            print(f"✅ {description}")
        except Exception as e:
            error_msg = f"❌ {description}: {e}"
            print(error_msg)
            errors.append((module_name, str(e)))
            traceback.print_exc()
    
    if errors:
        print(f"\n❌ Found {len(errors)} import errors:")
        for module, error in errors:
            print(f"  - {module}: {error}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

if __name__ == "__main__":
    success = check_imports()
    sys.exit(0 if success else 1)

