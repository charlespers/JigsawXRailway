"""
PCB Design Agents Package
Backward compatibility re-exports for new src/ structure
"""

import sys
from pathlib import Path

# Add src to path if it exists
src_dir = Path(__file__).parent.parent / "src"
if src_dir.exists() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Try new structure first, fall back to old structure
try:
    # Core agents
    from agents.core.design_orchestrator import DesignOrchestrator
    from agents.core.requirements_agent import RequirementsAgent
    from agents.core.architecture_agent import ArchitectureAgent
    from agents.core.query_router_agent import QueryRouterAgent
    
    # Analysis agents
    from agents.analysis.cost_optimizer_agent import CostOptimizerAgent
    from agents.analysis.cost_forecast_agent import CostForecastAgent
    from agents.analysis.supply_chain_agent import SupplyChainAgent
    from agents.analysis.power_calculator_agent import PowerCalculatorAgent
    from agents.analysis.thermal_analysis_agent import ThermalAnalysisAgent
    from agents.analysis.signal_integrity_agent import SignalIntegrityAgent
    from agents.analysis.manufacturing_readiness_agent import ManufacturingReadinessAgent
    from agents.analysis.design_validator_agent import DesignValidatorAgent
    
    # Design agents
    from agents.design.design_analyzer import DesignAnalyzer, safe_float_extract
    from agents.design.design_review_agent import DesignReviewAgent
    from agents.design.design_comparison_agent import DesignComparisonAgent
    from agents.design.design_reuse_agent import DesignReuseAgent
    from agents.design.output_generator import OutputGenerator
    
    # Parts agents
    from agents.parts.part_search_agent import PartSearchAgent
    from agents.parts.alternative_finder_agent import AlternativeFinderAgent
    from agents.parts.compatibility_agent import CompatibilityAgent
    from agents.parts.datasheet_agent import DatasheetAgent
    from agents.parts.intermediary_agent import IntermediaryAgent
    
    # Utility agents
    from agents.utilities.auto_fix_agent import AutoFixAgent
    from agents.utilities.bom_insights_agent import BOMInsightsAgent
    from agents.utilities.compliance_agent import ComplianceAgent
    from agents.utilities.eda_asset_agent import EDAAssetAgent
    from agents.utilities.obsolescence_forecast_agent import ObsolescenceForecastAgent
    from agents.utilities.testpoint_fiducial_agent import TestPointFiducialAgent
    from agents.utilities.reasoning_agent import ReasoningAgent
    
    # Shared utilities
    from agents._agent_helpers import *
except ImportError:
    # Fall back to old structure if new structure doesn't exist
    try:
        from .design_orchestrator import DesignOrchestrator
        from .requirements_agent import RequirementsAgent
        from .architecture_agent import ArchitectureAgent
        from .query_router_agent import QueryRouterAgent
        from .cost_optimizer_agent import CostOptimizerAgent
        from .cost_forecast_agent import CostForecastAgent
        from .supply_chain_agent import SupplyChainAgent
        from .power_calculator_agent import PowerCalculatorAgent
        from .thermal_analysis_agent import ThermalAnalysisAgent
        from .signal_integrity_agent import SignalIntegrityAgent
        from .manufacturing_readiness_agent import ManufacturingReadinessAgent
        from .design_validator_agent import DesignValidatorAgent
        from .design_analyzer import DesignAnalyzer, safe_float_extract
        from .design_review_agent import DesignReviewAgent
        from .design_comparison_agent import DesignComparisonAgent
        from .design_reuse_agent import DesignReuseAgent
        from .output_generator import OutputGenerator
        from .part_search_agent import PartSearchAgent
        from .alternative_finder_agent import AlternativeFinderAgent
        from .compatibility_agent import CompatibilityAgent
        from .datasheet_agent import DatasheetAgent
        from .intermediary_agent import IntermediaryAgent
        from .auto_fix_agent import AutoFixAgent
        from .bom_insights_agent import BOMInsightsAgent
        from .compliance_agent import ComplianceAgent
        from .eda_asset_agent import EDAAssetAgent
        from .obsolescence_forecast_agent import ObsolescenceForecastAgent
        from .testpoint_fiducial_agent import TestPointFiducialAgent
        from .reasoning_agent import ReasoningAgent
        from ._agent_helpers import *
    except ImportError:
        pass

__all__ = [
    # Core
    "DesignOrchestrator",
    "RequirementsAgent",
    "ArchitectureAgent",
    "QueryRouterAgent",
    # Analysis
    "CostOptimizerAgent",
    "CostForecastAgent",
    "SupplyChainAgent",
    "PowerCalculatorAgent",
    "ThermalAnalysisAgent",
    "SignalIntegrityAgent",
    "ManufacturingReadinessAgent",
    "DesignValidatorAgent",
    # Design
    "DesignAnalyzer",
    "safe_float_extract",
    "DesignReviewAgent",
    "DesignComparisonAgent",
    "DesignReuseAgent",
    "OutputGenerator",
    # Parts
    "PartSearchAgent",
    "AlternativeFinderAgent",
    "CompatibilityAgent",
    "DatasheetAgent",
    "IntermediaryAgent",
    # Utilities
    "AutoFixAgent",
    "BOMInsightsAgent",
    "ComplianceAgent",
    "EDAAssetAgent",
    "ObsolescenceForecastAgent",
    "TestPointFiducialAgent",
    "ReasoningAgent",
]
