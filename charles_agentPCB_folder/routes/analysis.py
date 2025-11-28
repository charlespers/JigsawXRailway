"""
Analysis-related routes
"""

import logging
import asyncio
import os
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
    BOMInsightsResponse
)
from core.exceptions import AgentException

logger = logging.getLogger(__name__)

# Create router with explicit prefix - this will be combined with /api/v1 from parent
router = APIRouter(prefix="/analysis", tags=["analysis"])

# Log router creation for debugging
logger.info(f"[ANALYSIS_ROUTER] Router created with prefix='/analysis'. Router ID: {id(router)}")


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
        return CostAnalysisResponse(**analysis)
    except AgentException as e:
        logger.error(f"Agent error in cost analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in cost analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
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
        logger.error(f"Agent error in supply chain analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in supply chain analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
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
        logger.error(f"Agent error in power analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in power analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
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
        logger.error(f"Agent error in design validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in design validation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
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
        logger.error(f"Agent error in BOM insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in BOM insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
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
                asyncio.to_thread(cost_agent.optimize_cost, bom_items)
            )
        
        if "supply_chain" in request.analysis_types:
            supply_agent = SupplyChainAgent()
            tasks["supply_chain"] = asyncio.create_task(
                asyncio.to_thread(supply_agent.analyze_supply_chain, bom_items)
            )
        
        if "power" in request.analysis_types:
            power_agent = PowerCalculatorAgent()
            tasks["power"] = asyncio.create_task(
                asyncio.to_thread(power_agent.calculate_power, bom_items, connections)
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
                asyncio.to_thread(mfg_agent.analyze_manufacturing_readiness, bom_items)
            )
        
        if "validation" in request.analysis_types:
            validator = DesignValidatorAgent()
            tasks["validation"] = asyncio.create_task(
                asyncio.to_thread(validator.validate_design, bom_items, connections)
            )
        
        # Wait for all tasks to complete
        for analysis_type, task in tasks.items():
            try:
                results[analysis_type] = await task
            except Exception as e:
                errors[analysis_type] = str(e)
                logger.error(f"Error in {analysis_type} analysis: {e}")
        
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

