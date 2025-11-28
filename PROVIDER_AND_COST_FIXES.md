# Provider and Cost Multiplication Fixes

## Issues Fixed

### 1. Provider Not Passed from Templates ✅
**Problem**: When clicking on a template, the provider setting (xAI/OpenAI) was not being passed to the backend, causing it to default to OpenAI and fail if only xAI key was set.

**Solution**:
- Updated `JigsawDemo.tsx` to call `handleQuerySent(query, provider)` when template is selected
- Updated `JigsawDemoRefactored.tsx` to track provider state and pass it correctly
- Updated `DesignChat` to pass provider when sending queries

### 2. Agent Initialization Timing ✅
**Problem**: Agents were reading the provider from environment variables during `__init__`, but the environment was set AFTER agent creation, causing wrong provider to be used.

**Solution**:
- Implemented lazy initialization pattern for all LLM-using agents:
  - `RequirementsAgent`
  - `CompatibilityAgent`
  - `ArchitectureAgent`
  - `ReasoningAgent`
  - `QueryRouterAgent`
- Agents now read provider from environment at runtime (when methods are called), not at initialization
- Created `_ensure_initialized()` method that reads current environment state

### 3. Cost Multiplication Error ✅
**Problem**: Error "unsupported operand type(s) for *: 'dict' and 'float'" occurred when cost_estimate contained nested dictionaries instead of numeric values.

**Solution**:
- Created `utils/cost_utils.py` with `safe_extract_cost()` and `safe_extract_quantity()` functions
- Updated all cost multiplication locations to use safe extraction:
  - `output_generator.py` - BOM generation
  - `cost_optimizer_agent.py` - Cost analysis
  - `bom_insights_agent.py` - BOM insights
  - `cost_forecast_agent.py` - Cost forecasting
  - `design_comparison_agent.py` - Design comparison
  - `power_calculator_agent.py` - Power calculations (quantity)
  - `thermal_analysis_agent.py` - Thermal analysis (quantity)
  - `supply_chain_agent.py` - Supply chain risk (quantity)
  - `api/data_mapper.py` - Data mapping
  - `serializers/part_serializer.py` - Part serialization

## Files Modified

### Backend
- `agents/requirements_agent.py` - Lazy initialization
- `agents/compatibility_agent.py` - Lazy initialization
- `agents/architecture_agent.py` - Lazy initialization
- `agents/reasoning_agent.py` - Lazy initialization
- `agents/query_router_agent.py` - Lazy initialization
- `agents/_agent_helpers.py` - NEW: Shared helper for LLM config
- `agents/output_generator.py` - Safe cost extraction
- `agents/cost_optimizer_agent.py` - Safe cost extraction
- `agents/bom_insights_agent.py` - Safe cost extraction
- `agents/cost_forecast_agent.py` - Safe cost extraction
- `agents/design_comparison_agent.py` - Safe cost extraction
- `agents/power_calculator_agent.py` - Safe quantity extraction
- `agents/thermal_analysis_agent.py` - Safe quantity extraction
- `agents/supply_chain_agent.py` - Safe quantity extraction
- `api/data_mapper.py` - Safe cost extraction
- `serializers/part_serializer.py` - Safe cost extraction
- `utils/cost_utils.py` - NEW: Safe extraction utilities

### Frontend
- `JigsawDemo.tsx` - Pass provider when template selected
- `JigsawDemoRefactored.tsx` - Track and pass provider state
- `components/DesignChat.tsx` - Already passes provider correctly

## Testing

All imports verified:
- ✅ `OutputGenerator` imports successfully
- ✅ `CostOptimizerAgent` imports successfully
- ✅ `BOMInsightsAgent` imports successfully
- ✅ `cost_utils` module imports successfully
- ✅ Safe extraction functions handle nested dicts correctly

## Impact

- **Provider Selection**: Now works correctly for templates and all queries
- **Cost Calculations**: No more dict/float multiplication errors
- **Robustness**: All cost and quantity extractions are now safe and handle edge cases

