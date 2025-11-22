# Agent Execution Analysis

## Current Execution Flow (Sequential)

### Main Design Generation Workflow (`generate_design_stream`)

**Step 1: Requirements Agent** (Sequential, Required)

- `requirements_agent.extract_requirements(query)` - Synchronous LLM call
- **Dependencies**: None
- **Can parallelize?**: No (must be first)

**Step 2: Architecture Agent** (Sequential, Required)

- `architecture_agent.build_architecture(requirements)` - Synchronous LLM call
- **Dependencies**: Requires Step 1 output
- **Can parallelize?**: No (depends on requirements)

**Step 3: Anchor Part Selection** (Sequential, Required)

- `_select_anchor_part(anchor_block, requirements)` - Database search
- **Dependencies**: Requires Step 2 output
- **Can parallelize?**: No (needed before supporting parts)

**Step 4: Expand Requirements** (Sequential, Required)

- `_expand_requirements(anchor_part, architecture)` - Synchronous
- **Dependencies**: Requires Step 3 output
- **Can parallelize?**: No (needed for supporting part selection)

**Step 5: Supporting Parts Selection** (Currently Sequential, Can Parallelize!)

- **Loop through child_blocks** - Each block processed one at a time
- For each block:
  1. `_select_supporting_part()` - Database search (now async with timeout)
  2. `compatibility_agent.check_compatibility()` - LLM call (now async with timeout)
  3. `_resolve_voltage_mismatch()` - LLM call (now async with timeout)
  4. `get_recommended_external_components()` - Database lookup
- **Dependencies**:
  - Each block needs anchor_part (from Step 3)
  - Blocks may depend on each other (via `depends_on` field)
- **Can parallelize?**: **YES!** - Independent blocks can run in parallel

**Step 6: Datasheet Enrichment** (Sequential, Optional)

- `_enrich_parts_with_datasheets()` - Synchronous
- **Dependencies**: Requires all selected parts
- **Can parallelize?**: Partially - can fetch multiple datasheets in parallel

**Step 7: Output Generation** (Sequential, Required)

- `output_generator.generate_connections()` - Synchronous
- `output_generator.generate_bom()` - Synchronous
- **Dependencies**: Requires all parts and connections
- **Can parallelize?**: Yes - connections and BOM can be generated in parallel

### Advanced Analysis Agents (Separate API Endpoints)

These are called individually via separate endpoints and are NOT part of the main workflow:

- `AlternativeFinderAgent` - `/api/parts/alternatives/{part_id}`
- `CostOptimizerAgent` - `/api/analysis/cost`
- `SupplyChainAgent` - `/api/analysis/supply-chain`
- `PowerCalculatorAgent` - `/api/analysis/power`
- `DesignValidatorAgent` - `/api/validation/design`
- `AutoFixAgent` - `/api/auto-fix/suggest`
- `BOMInsightsAgent` - `/api/analysis/bom-insights`
- `ThermalAnalysisAgent` - `/api/analysis/thermal`
- `SignalIntegrityAgent` - `/api/analysis/signal-integrity`
- `ManufacturingReadinessAgent` - `/api/analysis/manufacturing-readiness`
- `DesignReviewAgent` - `/api/review/design`
- `ComplianceAgent` - `/api/compliance/check`
- `DesignComparisonAgent` - `/api/design/compare`
- `ObsolescenceForecastAgent` - `/api/forecast/obsolescence`
- `DesignReuseAgent` - `/api/analysis/design-reuse`
- `CostForecastAgent` - `/api/forecast/cost`

**Can parallelize?**: Yes - if called together, they can run in parallel

## Parallelization Opportunities

### 1. **Supporting Parts Selection** (High Impact)

**Current**: Sequential loop through child_blocks
**Opportunity**: Process independent blocks in parallel

**Implementation**:

- Group blocks by dependencies
- Process independent groups in parallel
- Use `asyncio.gather()` for parallel execution

**Expected Speedup**: 2-5x for designs with 3+ independent blocks

### 2. **Compatibility Checks** (Medium Impact)

**Current**: Sequential power + interface checks
**Opportunity**: Run power and interface checks in parallel

**Expected Speedup**: ~2x for each part

### 3. **External Component Fetching** (Low Impact)

**Current**: Sequential database lookups
**Opportunity**: Fetch all external components in parallel

**Expected Speedup**: 1.5-2x

### 4. **Datasheet Enrichment** (Medium Impact)

**Current**: Sequential datasheet fetching
**Opportunity**: Fetch multiple datasheets in parallel

**Expected Speedup**: 3-5x for designs with many parts

### 5. **Output Generation** (Low Impact)

**Current**: Sequential connection + BOM generation
**Opportunity**: Generate connections and BOM in parallel

**Expected Speedup**: ~2x

### 6. **Advanced Analysis Agents** (High Impact if called together)

**Current**: Called individually via separate endpoints
**Opportunity**: Batch endpoint that runs multiple analyses in parallel

**Expected Speedup**: 5-10x if running 5+ analyses

## Dependency Graph

```
Requirements Agent
    ↓
Architecture Agent
    ↓
Anchor Part Selection
    ↓
Expand Requirements
    ↓
Supporting Parts Selection (CAN PARALLELIZE)
    ├─ Block 1 (sensor) ──┐
    ├─ Block 2 (power) ────┼─→ Independent blocks can run in parallel
    └─ Block 3 (connector)─┘
    ↓
Datasheet Enrichment (CAN PARALLELIZE)
    ↓
Output Generation (CAN PARALLELIZE)
    ├─ Generate Connections
    └─ Generate BOM
```

## Implementation Plan

### Phase 1: Parallel Supporting Parts Selection

- Identify independent blocks (no dependencies on other blocks)
- Use `asyncio.gather()` to process independent blocks in parallel
- Maintain sequential processing for dependent blocks

### Phase 2: Parallel Compatibility Checks

- Run power and interface compatibility checks in parallel
- Use `asyncio.gather()` for both checks

### Phase 3: Parallel Datasheet Enrichment

- Fetch all datasheets in parallel using `asyncio.gather()`

### Phase 4: Parallel Output Generation

- Generate connections and BOM in parallel

### Phase 5: Batch Analysis Endpoint

- Create `/api/analysis/batch` endpoint
- Run multiple analysis agents in parallel
