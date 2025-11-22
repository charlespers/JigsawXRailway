# Agent Workflow Diagram

## Overview

This document describes the complete workflow for PCB design generation from user query to final BOM output. The system uses a multi-agent architecture with streaming updates to provide real-time feedback.

## High-Level Flow

```
┌─────────────────┐
│  User Query     │
│  (DesignChat)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  POST /mcp/component-analysis        │
│  (SSE Endpoint)                      │
└────────┬─────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Backend: generate_design_stream()  │
│  (Async Generator)                  │
└────────┬─────────────────────────────┘
         │
         ├─────────────────────────────────────────────────┐
         │                                                 │
         ▼                                                 ▼
┌──────────────────────┐                    ┌──────────────────────┐
│  Step 1: Requirements│                    │  SSE Event Stream     │
│  Agent               │                    │  (Real-time updates)  │
└────────┬─────────────┘                    └──────────┬─────────────┘
         │                                             │
         ▼                                             │
┌──────────────────────┐                              │
│  Step 2: Architecture│                              │
│  Agent               │                              │
└────────┬─────────────┘                              │
         │                                             │
         ▼                                             │
┌──────────────────────┐                              │
│  Step 3: Anchor Part │                              │
│  Selection           │                              │
└────────┬─────────────┘                              │
         │                                             │
         ▼                                             │
┌──────────────────────┐                              │
│  Step 4: Expand       │                              │
│  Requirements        │                              │
└────────┬─────────────┘                              │
         │                                             │
         ▼                                             │
┌──────────────────────┐                              │
│  Step 5: Supporting   │                              │
│  Parts Selection     │                              │
│  (Parallel/Sequential)│                              │
└────────┬─────────────┘                              │
         │                                             │
         ▼                                             │
┌──────────────────────┐                              │
│  Step 6: Datasheet    │                              │
│  Enrichment          │                              │
└────────┬─────────────┘                              │
         │                                             │
         ▼                                             │
┌──────────────────────┐                              │
│  Step 7: Output       │                              │
│  Generation          │                              │
└────────┬─────────────┘                              │
         │                                             │
         ▼                                             │
┌──────────────────────┐                              │
│  Step 8: Engineering  │                              │
│  Analysis            │                              │
└────────┬─────────────┘                              │
         │                                             │
         └─────────────────────────────────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  "complete"     │
                 │  Event          │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Frontend:       │
                 │  Update UI       │
                 │  Display BOM     │
                 └─────────────────┘
```

## Detailed Step-by-Step Workflow

### Step 1: Requirements Extraction

**Agent:** `RequirementsAgent`

**Input:** User query (natural language)

**Process:**
1. Parse user query for functional requirements
2. Extract constraints (voltage, interfaces, power, etc.)
3. Identify functional blocks needed

**Output:**
- `functional_blocks`: List of required components
- `constraints`: Design constraints
- `preferences`: User preferences

**SSE Events:**
- `reasoning`: "Analyzing user query..."
- `reasoning`: "Identified X functional blocks..."

---

### Step 2: Architecture Design

**Agent:** `ArchitectureAgent`

**Input:** Requirements from Step 1

**Process:**
1. Build functional hierarchy
2. Identify anchor component (most connected)
3. Determine dependencies between blocks
4. Group blocks into independent/dependent sets

**Output:**
- `anchor_block`: The central component
- `child_blocks`: Supporting components
- `dependency_graph`: Block dependencies

**SSE Events:**
- `reasoning`: "Building functional hierarchy..."
- `reasoning`: "Selected X as anchor component..."

---

### Step 3: Anchor Part Selection

**Agent:** `PartSearchAgent`

**Input:** Anchor block from Step 2

**Process:**
1. Search part database for anchor component
2. Filter by interfaces, lifecycle, availability
3. Rank by engineering criteria (lifecycle, availability, power efficiency, etc.)
4. Select best match

**Output:**
- `anchor_part`: Selected part data

**SSE Events:**
- `reasoning`: "Searching part database for X..."
- `reasoning`: "Selected [MPN] from [Manufacturer]..."
- `selection`: Part data with hierarchyLevel=0

**Frontend Action:**
- ComponentGraph receives selection event
- Calls `onComponentSelected` callback
- Adds part to `parts` array
- Updates `selectedComponents` Map
- Displays part in ComponentGraph and PartsList

---

### Step 4: Expand Requirements

**Process:**
1. Analyze anchor part capabilities
2. Determine required supporting components
3. Generate expanded requirements for each child block

**Output:**
- `expanded_requirements`: Detailed requirements per block

**SSE Events:**
- None (internal step)

---

### Step 5: Supporting Parts Selection

**Process:** Two-phase approach

#### Phase 5a: Independent Blocks (Parallel Processing)

**For each independent block:**
1. **Part Search Agent** → Find matching part
2. **Compatibility Agent** → Check power/interface compatibility
3. **Intermediary Agent** (if needed) → Resolve voltage mismatches
4. Emit `selection` event

**Parallel Execution:**
- All independent blocks processed concurrently
- Each block gets unique hierarchy level: `hierarchy_level + i`
- Timeout: 30s per block
- Errors don't block other blocks

**SSE Events:**
- `reasoning`: "Processing X independent component(s) in parallel..."
- `reasoning`: "[1/X] Processing [block_name]..."
- `selection`: Part data (one per block)
- `reasoning`: "✓ [1/X] Completed [block_name]"

#### Phase 5b: Dependent Blocks (Sequential Processing)

**For each dependent block:**
1. Same process as independent blocks
2. Process sequentially (may depend on previous blocks)
3. Hierarchy level increments per block

**SSE Events:**
- `reasoning`: "Processing X dependent component(s) sequentially..."
- `reasoning`: "[1/X] Processing dependent component: [block_name]..."
- `selection`: Part data
- `reasoning`: "✓ [1/X] Completed [block_name]"

**Frontend Action (for each selection event):**
- ComponentGraph receives selection
- Calculates hierarchy offset
- Calls `onComponentSelected`
- Adds to parts array (with componentId tracking)
- Updates UI

---

### Step 6: Datasheet Enrichment

**Agent:** `DatasheetAgent`

**Process:**
1. For each selected part, fetch/enrich with datasheet data
2. Fill missing specifications
3. Add application notes

**SSE Events:**
- `reasoning`: "Enriching parts with datasheet data..."

---

### Step 7: Output Generation

**Agent:** `OutputGenerator`

**Process:**
1. Generate connections between parts
2. Generate BOM with quantities
3. Add test points, external components

**SSE Events:**
- `reasoning`: "Generating connections and BOM..."

---

### Step 8: Engineering Analysis

**Agent:** `DesignAnalyzer`

**Process:**
1. Power analysis (consumption per rail)
2. Thermal analysis (junction temperatures)
3. Design rule checks (DRC)
4. Generate recommendations

**SSE Events:**
- `reasoning`: "Performing comprehensive engineering analysis..."
- `reasoning`: "✓ Power analysis complete: X W across Y rails"
- `reasoning`: "✓ Design validation: X errors, Y warnings"

---

### Final Step: Completion

**SSE Event:**
- `complete`: Summary message with statistics

**Frontend Action:**
- `onAnalysisComplete` callback
- `isAnalyzing` set to false
- UI updates to show final state

## Data Flow: Parts List

### Backend → Frontend

1. **Backend:** `orchestrator.design_state["selected_parts"][block_name] = part`
2. **Backend:** `part_object = part_data_to_part_object(part)`
3. **Backend:** `await queue.put({"type": "selection", "partData": part_object, ...})`
4. **SSE Stream:** Event sent via HTTP SSE
5. **Frontend:** `componentAnalysisApi` receives event
6. **Frontend:** `ComponentGraph.handleUpdate()` processes event
7. **Frontend:** `onComponentSelected()` callback invoked
8. **Frontend:** `JigsawDemo.handleComponentSelected()` updates state:
   - Adds to `parts` array (with componentId tracking)
   - Updates `selectedComponents` Map
9. **Frontend:** `PartsList` component displays parts from `parts` prop

### Parts List Structure

**Frontend State:**
```typescript
parts: PartObject[] = [
  {
    mpn: "ESP32-WROOM-32",
    manufacturer: "Espressif",
    description: "...",
    quantity: 1,
    componentId: "anchor", // Tracks which component selected this
    ...
  },
  ...
]
```

**Backend State:**
```python
selected_parts: Dict[str, Dict] = {
  "anchor": {...},
  "sensor_block": {...},
  ...
}
```

## Error Handling

### Timeout Handling
- Each block processing has 30s timeout
- Timeouts don't block other blocks
- Failed blocks are logged and skipped

### Error Recovery
- Errors in one block don't stop workflow
- "complete" event always sent (even on errors)
- Frontend receives error events but continues

### Connection Management
- SSE heartbeat every 15s to keep connection alive
- 60s timeout on queue.get() for long operations
- Task cancellation on connection close

## Hierarchy Level Management

### Anchor Part
- `hierarchyLevel = 0`

### Independent Blocks
- Start at `hierarchy_level + i` (where i is block index)
- Each successful block increments max hierarchy
- Failed blocks don't increment hierarchy

### Dependent Blocks
- Start at `max(successful_independent_hierarchies) + 1`
- Increment sequentially: `hierarchy_level + 1` per block

### Frontend Offset
- Frontend calculates: `baseOffset = max(hierarchy) + 1`
- Adjusted hierarchy: `update.hierarchyLevel + baseOffset`
- Ensures new queries append to existing hierarchy

## Critical Paths

### Selection Event Path (MUST WORK)
1. Backend: `_process_block_async()` → `queue.put({"type": "selection"})`
2. Backend: `event_stream()` → `yield f"data: {json.dumps(event)}\n\n"`
3. Frontend: SSE reader → `onUpdate(data)`
4. Frontend: `ComponentGraph.handleUpdate()` → `onComponentSelected()`
5. Frontend: `JigsawDemo.handleComponentSelected()` → `setParts()`

**If any step fails, part won't appear in UI.**

## Logging Points

### Backend Logging
- `[WORKFLOW]` prefix for workflow events
- Log block start/completion
- Log selection events
- Log errors with stack traces

### Frontend Logging
- `[ComponentGraph]` prefix for component events
- `[SSE]` prefix for stream events
- Log all selection events
- Log callback invocations

## Performance Considerations

### Parallel Processing
- Independent blocks: Process concurrently
- Dependent blocks: Process sequentially
- Timeouts prevent hanging

### SSE Optimization
- Heartbeat keeps connection alive
- Events batched when possible
- Large payloads avoided

### Frontend Optimization
- `requestAnimationFrame` for React batching
- ComponentId tracking prevents duplicate filtering
- State updates batched

## Testing Checklist

- [ ] All 9 parts selected for complex query
- [ ] All parts appear in PartsList
- [ ] No duplicate filtering of valid parts
- [ ] Hierarchy levels correct
- [ ] Selection events received in frontend
- [ ] Complete event always sent
- [ ] Errors don't block workflow
- [ ] Timeouts handled gracefully
- [ ] SSE connection stays alive
- [ ] Logging provides visibility

