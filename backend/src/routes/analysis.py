"""
Analysis-related routes
"""

import logging
import asyncio
import os
import time
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from api.schemas.analysis import (
    CostAnalysisRequest,
    CostAnalysisResponse,
    SupplyChainAnalysisRequest,
    SupplyChainAnalysisResponse,
    PowerAnalysisRequest,
    PowerAnalysisResponse,
    ThermalAnalysisRequest,
    ThermalAnalysisResponse,
    SignalIntegrityAnalysisRequest,
    SignalIntegrityAnalysisResponse,
    ManufacturingReadinessRequest,
    ManufacturingReadinessResponse,
    DesignValidationRequest,
    DesignValidationResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BOMInsightsRequest,
    BOMInsightsResponse,
    ComplianceAnalysisRequest,
    ComplianceAnalysisResponse
)
from core.exceptions import AgentException

# Import agents - try new structure first, fall back to old
try:
    from agents.analysis.cost_optimizer_agent import CostOptimizerAgent
    from agents.analysis.supply_chain_agent import SupplyChainAgent
    from agents.analysis.power_calculator_agent import PowerCalculatorAgent
    from agents.analysis.thermal_analysis_agent import ThermalAnalysisAgent
    from agents.analysis.signal_integrity_agent import SignalIntegrityAgent
    from agents.analysis.manufacturing_readiness_agent import ManufacturingReadinessAgent
    from agents.analysis.design_validator_agent import DesignValidatorAgent
    from agents.utilities.bom_insights_agent import BOMInsightsAgent
    from agents.utilities.compliance_agent import ComplianceAgent
    from agents.utilities.auto_fix_agent import AutoFixAgent
except ImportError:
    # Fall back to old structure
    from agents.cost_optimizer_agent import CostOptimizerAgent
    from agents.supply_chain_agent import SupplyChainAgent
    from agents.power_calculator_agent import PowerCalculatorAgent
    from agents.thermal_analysis_agent import ThermalAnalysisAgent
    from agents.signal_integrity_agent import SignalIntegrityAgent
    from agents.manufacturing_readiness_agent import ManufacturingReadinessAgent
    from agents.design_validator_agent import DesignValidatorAgent
    from agents.bom_insights_agent import BOMInsightsAgent
    from agents.compliance_agent import ComplianceAgent
    from agents.auto_fix_agent import AutoFixAgent

logger = logging.getLogger(__name__)

# Create router with explicit prefix - this will be combined with /api/v1 from parent
router = APIRouter(prefix="/analysis", tags=["analysis"])

# Log router creation for debugging
logger.info(f"[ANALYSIS_ROUTER] Router created with prefix='/analysis'. Router ID: {id(router)}")


@router.post("/test")
async def analysis_test_endpoint():
    """
    Lightweight diagnostics endpoint so deployments can verify analysis routes quickly.
    Returns summary metadata instead of calling any downstream agents.
    """
    try:
        analysis_routes = [
            {
                "path": route.path,
                "name": route.name,
                "methods": sorted(
                    list({m for m in getattr(route, "methods", set()) if m not in {"OPTIONS", "HEAD"}})
                ),
            }
            for route in router.routes
            if getattr(route, "path", "").startswith("/analysis/")
        ]
        return {
            "status": "ok",
            "analysis_routes_count": len(analysis_routes),
            "routes": analysis_routes,
        }
    except Exception as err:
        logger.error(f"[ANALYSIS_TEST] Failed to enumerate analysis routes: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail="Diagnostics failed")


@router.post("/cost", response_model=CostAnalysisResponse)
async def analyze_cost(request: CostAnalysisRequest):
    """Analyze BOM cost and suggest optimizations."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.cost_optimizer_agent import CostOptimizerAgent
        
        agent = CostOptimizerAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        analysis = agent.analyze_bom_cost(bom_items)
        # Ensure all numeric fields are actually numbers, not dicts
        if isinstance(analysis.get("total_cost"), dict):
            analysis["total_cost"] = analysis["total_cost"].get("value") or analysis["total_cost"].get("cost") or 0.0
        analysis["total_cost"] = float(analysis.get("total_cost", 0.0))
        return CostAnalysisResponse(**analysis)
    except AgentException as e:
        logger.error(f"[COST_ANALYSIS] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cost analysis agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[COST_ANALYSIS] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[COST_ANALYSIS] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in cost analysis: {str(e)}")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/supply-chain", response_model=SupplyChainAnalysisResponse)
async def analyze_supply_chain(request: SupplyChainAnalysisRequest):
    """Analyze supply chain risks."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.supply_chain_agent import SupplyChainAgent
        
        agent = SupplyChainAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        analysis = agent.analyze_supply_chain(bom_items)
        return SupplyChainAnalysisResponse(**analysis)
    except AgentException as e:
        logger.error(f"[SUPPLY_CHAIN] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Supply chain analysis agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[SUPPLY_CHAIN] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[SUPPLY_CHAIN] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in supply chain analysis: {str(e)}")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/power", response_model=PowerAnalysisResponse)
async def analyze_power(request: PowerAnalysisRequest):
    """Calculate power consumption."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.power_calculator_agent import PowerCalculatorAgent
        
        calculator = PowerCalculatorAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        connections = [
            {
                "net_name": conn.net_name,
                "components": conn.components,
                "pins": conn.pins
            }
            for conn in request.connections
        ]
        
        analysis = calculator.calculate_power_consumption(
            bom_items,
            request.operating_modes or {}
        )
        
        # Ensure all numeric fields are actually numbers, not dicts
        if isinstance(analysis.get("total_power"), dict):
            analysis["total_power"] = analysis["total_power"].get("value") or analysis["total_power"].get("watts") or 0.0
        analysis["total_power"] = float(analysis.get("total_power", 0.0))
        
        # If battery capacity provided, estimate battery life
        if request.battery_capacity_mah:
            battery_life = calculator.estimate_battery_life(
                analysis["total_power"],
                request.battery_capacity_mah,
                request.battery_voltage
            )
            analysis["battery_life"] = battery_life
        
        return PowerAnalysisResponse(**analysis)
    except AgentException as e:
        logger.error(f"[POWER_ANALYSIS] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Power analysis agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[POWER_ANALYSIS] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[POWER_ANALYSIS] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in power analysis: {str(e)}")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/thermal", response_model=ThermalAnalysisResponse)
async def analyze_thermal(request: ThermalAnalysisRequest):
    """Perform detailed thermal analysis."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.thermal_analysis_agent import ThermalAnalysisAgent
        
        agent = ThermalAnalysisAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        analysis = agent.analyze_thermal(
            bom_items,
            request.ambient_temp,
            request.pcb_area_cm2
        )
        return ThermalAnalysisResponse(**analysis)
    except AgentException as e:
        logger.error(f"Agent error in thermal analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in thermal analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/signal-integrity", response_model=SignalIntegrityAnalysisResponse)
async def analyze_signal_integrity(request: SignalIntegrityAnalysisRequest):
    """Perform signal integrity and EMI/EMC analysis."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.signal_integrity_agent import SignalIntegrityAgent
        
        agent = SignalIntegrityAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        connections = [
            {
                "net_name": conn.net_name,
                "components": conn.components,
                "pins": conn.pins
            }
            for conn in request.connections
        ]
        analysis = agent.analyze_signal_integrity(
            bom_items,
            connections,
            request.pcb_thickness_mm,
            request.trace_width_mils
        )
        return SignalIntegrityAnalysisResponse(**analysis)
    except AgentException as e:
        logger.error(f"Agent error in signal integrity analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in signal integrity analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/manufacturing-readiness", response_model=ManufacturingReadinessResponse)
async def analyze_manufacturing_readiness(request: ManufacturingReadinessRequest):
    """Perform manufacturing readiness analysis."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.manufacturing_readiness_agent import ManufacturingReadinessAgent
        
        agent = ManufacturingReadinessAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        connections = [
            {
                "net_name": conn.net_name,
                "components": conn.components,
                "pins": conn.pins
            }
            for conn in request.connections
        ]
        analysis = agent.analyze_manufacturing_readiness(bom_items, connections)
        return ManufacturingReadinessResponse(**analysis)
    except AgentException as e:
        logger.error(f"Agent error in manufacturing readiness analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in manufacturing readiness analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/validation", response_model=DesignValidationResponse)
async def validate_design(request: DesignValidationRequest):
    """Validate design against industry standards."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.design_validator_agent import DesignValidatorAgent
        from agents.auto_fix_agent import AutoFixAgent
        
        validator = DesignValidatorAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        connections = [
            {
                "net_name": conn.net_name,
                "components": conn.components,
                "pins": conn.pins
            }
            for conn in request.connections
        ]
        
        validation = validator.validate_design(bom_items, connections)
        
        # Get auto-fix suggestions
        auto_fix = AutoFixAgent()
        fix_suggestions = auto_fix.suggest_fixes(validation.get("issues", []), bom_items)
        fix_suggestions.extend(auto_fix.suggest_missing_footprints(bom_items))
        fix_suggestions.extend(auto_fix.suggest_missing_msl(bom_items))
        
        validation["fix_suggestions"] = fix_suggestions
        
        return DesignValidationResponse(**validation)
    except AgentException as e:
        logger.error(f"[VALIDATION] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Design validation agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[VALIDATION] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[VALIDATION] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in design validation: {str(e)}")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/bom-insights", response_model=BOMInsightsResponse)
async def analyze_bom_insights(request: BOMInsightsRequest):
    """Get comprehensive BOM insights and statistics."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.bom_insights_agent import BOMInsightsAgent
        
        agent = BOMInsightsAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        insights = agent.analyze_bom(bom_items)
        return BOMInsightsResponse(**insights)
    except AgentException as e:
        logger.error(f"[BOM_INSIGHTS] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"BOM insights agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[BOM_INSIGHTS] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[BOM_INSIGHTS] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in BOM insights: {str(e)}")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/compliance", response_model=ComplianceAnalysisResponse)
async def analyze_compliance(request: ComplianceAnalysisRequest):
    """Check design compliance with environmental and regulatory standards."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.compliance_agent import ComplianceAgent
        
        agent = ComplianceAgent()
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        
        compliance = agent.check_compliance(bom_items, request.regions)
        return ComplianceAnalysisResponse(**compliance)
    except AgentException as e:
        logger.error(f"[COMPLIANCE] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Compliance analysis agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[COMPLIANCE] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[COMPLIANCE] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in compliance analysis: {str(e)}")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/batch", response_model=BatchAnalysisResponse)
async def batch_analysis(request: BatchAnalysisRequest):
    """Run multiple analyses in parallel."""
    # Set provider before creating agents
    provider = request.provider or "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        from agents.cost_optimizer_agent import CostOptimizerAgent
        from agents.supply_chain_agent import SupplyChainAgent
        from agents.power_calculator_agent import PowerCalculatorAgent
        from agents.thermal_analysis_agent import ThermalAnalysisAgent
        from agents.signal_integrity_agent import SignalIntegrityAgent
        from agents.manufacturing_readiness_agent import ManufacturingReadinessAgent
        from agents.design_validator_agent import DesignValidatorAgent
        
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        connections = [
            {
                "net_name": conn.net_name,
                "components": conn.components,
                "pins": conn.pins
            }
            for conn in request.connections
        ]
        
        results = {}
        errors = {}
        tasks = {}
        
        # Create tasks for parallel execution
        if "cost" in request.analysis_types:
            cost_agent = CostOptimizerAgent()
            tasks["cost"] = asyncio.create_task(
                asyncio.to_thread(cost_agent.analyze_bom_cost, bom_items)
            )
        
        if "supply_chain" in request.analysis_types:
            supply_agent = SupplyChainAgent()
            tasks["supply_chain"] = asyncio.create_task(
                asyncio.to_thread(supply_agent.analyze_supply_chain, bom_items)
            )
        
        if "power" in request.analysis_types:
            power_agent = PowerCalculatorAgent()
            tasks["power"] = asyncio.create_task(
                asyncio.to_thread(power_agent.calculate_power_consumption, bom_items, {})
            )
        
        if "thermal" in request.analysis_types:
            thermal_agent = ThermalAnalysisAgent()
            tasks["thermal"] = asyncio.create_task(
                asyncio.to_thread(thermal_agent.analyze_thermal, bom_items, 25.0, None)
            )
        
        if "signal_integrity" in request.analysis_types:
            signal_agent = SignalIntegrityAgent()
            tasks["signal_integrity"] = asyncio.create_task(
                asyncio.to_thread(signal_agent.analyze_signal_integrity, bom_items, connections, 1.6, 5.0)
            )
        
        if "manufacturing" in request.analysis_types:
            mfg_agent = ManufacturingReadinessAgent()
            tasks["manufacturing"] = asyncio.create_task(
                asyncio.to_thread(mfg_agent.analyze_manufacturing_readiness, bom_items, connections)
            )
        
        if "validation" in request.analysis_types:
            validator = DesignValidatorAgent()
            tasks["validation"] = asyncio.create_task(
                asyncio.to_thread(validator.validate_design, bom_items, connections)
            )
        
        # Wait for all tasks to complete with timeout
        try:
            # Use asyncio.wait_for to add overall timeout (60 seconds for all analyses)
            completed_tasks = await asyncio.wait_for(
                asyncio.gather(*tasks.values(), return_exceptions=True),
                timeout=60.0
            )
            
            # Process results
            for (analysis_type, task), result in zip(tasks.items(), completed_tasks):
                if isinstance(result, Exception):
                    errors[analysis_type] = str(result)
                    logger.error(f"[BATCH_ANALYSIS] Error in {analysis_type} analysis: {result}")
                else:
                    results[analysis_type] = result
        except asyncio.TimeoutError:
            logger.error("[BATCH_ANALYSIS] Batch analysis timed out after 60s")
            # Cancel remaining tasks
            for task in tasks.values():
                if not task.done():
                    task.cancel()
            # Collect partial results
            for analysis_type, task in tasks.items():
                if task.done() and not task.cancelled():
                    try:
                        result = await task
                        results[analysis_type] = result
                    except Exception as e:
                        errors[analysis_type] = str(e)
                else:
                    errors[analysis_type] = "Analysis timed out"
            raise HTTPException(status_code=504, detail="Batch analysis timed out after 60 seconds")
        
        return BatchAnalysisResponse(
            results=results,
            completed=list(results.keys()),
            errors=errors if errors else None
        )
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider

