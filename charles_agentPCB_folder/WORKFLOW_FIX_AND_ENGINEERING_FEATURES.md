# Workflow Fix & Engineering-Focused Features Plan

## Problem 1: Workflow Hanging After First Part

### Root Causes Identified

1. **Parallel Task Execution Issue** (lines 459-477 in `server.py`):
   - All independent blocks get the same `hierarchy_level` value
   - No timeout on individual tasks - if one hangs, entire workflow blocks
   - Exceptions in tasks may not be properly caught
   - No progress updates during parallel processing

2. **Design Analyzer May Hang** (lines 525-535):
   - Synchronous `design_analyzer.analyze_design` wrapped in `asyncio.to_thread`
   - 15s timeout may not catch all blocking operations
   - No progress updates during analysis

3. **Missing Error Recovery**:
   - If a task fails, workflow may not continue
   - No summary of what succeeded/failed

## Problem 2: Missing Engineering-Focused Features

### Current State
- Basic auto-fix agent exists but is limited
- Validation errors shown but no one-click fixes
- No real-time error detection during design
- No part replacement suggestions
- No intelligent error-to-part mapping

### Desired Features
1. **Real-time Error Detection**: Detect errors as parts are added
2. **Intelligent Auto-Fix**: Suggest specific parts to fix each error
3. **One-Click Apply Fix**: Add suggested parts directly to BOM
4. **Part Replacement Suggestions**: Suggest better alternatives for existing parts
5. **Error-to-Part Mapping**: Smart matching of errors to fix parts
6. **Live Validation**: Continuous validation as design evolves

## Implementation Plan

### Phase 1: Fix Workflow Hanging (Critical)

#### 1.1 Fix Parallel Task Execution
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/api/server.py` (lines 449-482)

**Changes**:
- Add individual timeouts (30s) to each parallel task using `asyncio.wait_for`
- Assign unique hierarchy levels: `hierarchy_level + i` for each block
- Add progress updates: "Processing block X of Y: [name]"
- Improve error handling: catch `asyncio.TimeoutError` separately
- Track which blocks succeeded/failed
- Increment hierarchy level after each block (not at end)

**Code**:
```python
# Process independent blocks in parallel
if independent_blocks:
    await queue.put({
        "type": "reasoning",
        "componentId": "architecture",
        "componentName": "Architecture",
        "reasoning": f"Processing {len(independent_blocks)} independent component(s) in parallel...",
        "hierarchyLevel": 0
    })
    
    # Create tasks with unique hierarchy levels and timeouts
    tasks = []
    for i, block in enumerate(independent_blocks):
        block_hierarchy = hierarchy_level + i
        block_name = block.get("description", block.get("type", ""))
        
        await queue.put({
            "type": "reasoning",
            "componentId": "architecture",
            "componentName": "Architecture",
            "reasoning": f"[{i+1}/{len(independent_blocks)}] Processing {block_name}...",
            "hierarchyLevel": 0
        })
        
        task = asyncio.create_task(
            asyncio.wait_for(
                _process_block_async(block, expanded_requirements, requirements, orchestrator, anchor_part, queue, block_hierarchy),
                timeout=30.0
            )
        )
        tasks.append((block, task, block_hierarchy))
    
    # Wait for all independent blocks with proper error handling
    completed_count = 0
    for block, task, block_hierarchy in tasks:
        block_name = block.get("description", block.get("type", ""))
        try:
            await task
            completed_count += 1
            await queue.put({
                "type": "reasoning",
                "componentId": "architecture",
                "componentName": "Architecture",
                "reasoning": f"✓ [{completed_count}/{len(independent_blocks)}] Completed {block_name}",
                "hierarchyLevel": 0
            })
        except asyncio.TimeoutError:
            await queue.put({
                "type": "error",
                "message": f"Timeout processing {block_name} after 30s. Continuing with other components..."
            })
        except Exception as e:
            await queue.put({
                "type": "error",
                "message": f"Error processing {block_name}: {str(e)}. Continuing..."
            })
    
    hierarchy_level += len(independent_blocks)
```

#### 1.2 Add Progress Tracking for Dependent Blocks
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/api/server.py` (lines 479-482)

**Changes**:
- Add progress updates before/after each dependent block
- Add timeout protection (30s) for dependent blocks too

#### 1.3 Improve Design Analyzer Timeout
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/api/server.py` (lines 525-597)

**Changes**:
- Increase timeout to 30s
- Add progress updates during analysis
- Ensure timeout actually cancels operation
- Add fallback if analysis fails

#### 1.4 Ensure Completion Event Always Emits
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/api/server.py` (lines 599-610)

**Changes**:
- Wrap entire workflow in try-finally
- Always emit "complete" event with summary
- Include count of processed/failed blocks

### Phase 2: Enhanced Auto-Fix System

#### 2.1 Enhance AutoFixAgent
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/agents/auto_fix_agent.py`

**New Features**:
- **Smart Error-to-Part Mapping**: Use LLM to understand error context and suggest best parts
- **Compatibility-Aware Suggestions**: Ensure suggested parts are compatible with existing design
- **Cost-Aware Suggestions**: Consider cost when suggesting fixes
- **Availability-Aware Suggestions**: Prefer in-stock parts
- **Multiple Fix Options**: Provide 3-5 options ranked by suitability
- **Fix Confidence Score**: Rate how well each part fixes the issue

**New Methods**:
```python
def suggest_intelligent_fixes(
    self,
    validation_issues: List[Dict[str, Any]],
    bom_items: List[Dict[str, Any]],
    design_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Use LLM to understand error context and suggest best fixes."""
    
def suggest_part_replacements(
    self,
    part_to_replace: Dict[str, Any],
    reason: str,
    design_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Suggest better alternatives for existing parts."""
    
def get_fix_confidence(
    self,
    suggested_part: Dict[str, Any],
    issue: Dict[str, Any]
) -> float:
    """Rate how well a part fixes an issue (0-1)."""
```

#### 2.2 Add Real-Time Error Detection
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/api/server.py`

**New Endpoint**:
```python
@app.post("/api/validation/realtime")
async def validate_realtime(request: Request):
    """Validate design in real-time as parts are added."""
    # Run validation on current design state
    # Return errors with immediate fix suggestions
```

#### 2.3 Add Fix Application Endpoint
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/api/server.py`

**New Endpoint**:
```python
@app.post("/api/fix/apply")
async def apply_fix(request: Request):
    """Apply a suggested fix by adding/replacing parts."""
    # Add suggested part to design
    # Update design state
    # Return updated design
```

### Phase 3: Frontend Auto-Fix UI

#### 3.1 Create AutoFixPanel Component
**File**: `yc_jigsaw_demo/frontend/src/demo/components/AutoFixPanel.tsx` (NEW)

**Features**:
- Display validation errors with severity
- Show suggested fix parts with confidence scores
- One-click "Apply Fix" button for each suggestion
- Preview of what will change
- Cost impact of fixes
- Compatibility check before applying

**UI Elements**:
- Error cards with severity badges
- Suggested part cards with:
  - Part name, MPN, manufacturer
  - Confidence score (visual indicator)
  - Cost impact
  - Compatibility status
  - "Apply Fix" button
- Summary of all fixes
- "Apply All Safe Fixes" button

#### 3.2 Enhance BOMInsights Component
**File**: `yc_jigsaw_demo/frontend/src/demo/components/BOMInsights.tsx`

**Enhancements**:
- Add "Auto-Fix" section at top
- Show real-time validation errors
- Display fix suggestions inline
- Add "Apply Fix" buttons
- Show fix preview before applying
- Add undo/redo for fixes

#### 3.3 Add Real-Time Validation
**File**: `yc_jigsaw_demo/frontend/src/demo/JigsawDemo.tsx`

**Changes**:
- Call validation API when parts change
- Display errors in real-time
- Show fix suggestions immediately
- Auto-refresh validation after fixes applied

#### 3.4 Add Part Replacement UI
**File**: `yc_jigsaw_demo/frontend/src/demo/components/PartsList.tsx`

**Enhancements**:
- "Replace" button on each part
- Show replacement suggestions on click
- Preview compatibility and cost impact
- One-click replacement

### Phase 4: Engineering Best Practices

#### 4.1 Add Design Health Score
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/agents/design_review_agent.py`

**Enhancements**:
- Calculate overall design health score (0-100)
- Break down by category (power, thermal, compliance, etc.)
- Show in UI with visual indicator
- Update in real-time

#### 4.2 Add Design Recommendations Engine
**File**: `yc_jigsaw_demo/charles_agentPCB_folder/agents/design_analyzer.py`

**New Method**:
```python
def generate_actionable_recommendations(
    self,
    selected_parts: Dict[str, Dict[str, Any]],
    analysis_results: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate specific, actionable recommendations with part suggestions."""
    # Each recommendation includes:
    # - Issue description
    # - Suggested parts to fix
    # - Expected improvement
    # - Cost impact
    # - Priority level
```

#### 4.3 Add Part Compatibility Warnings
**File**: `yc_jigsaw_demo/frontend/src/demo/components/ComponentGraph.tsx`

**Features**:
- Show compatibility warnings on parts
- Suggest compatible alternatives
- One-click swap incompatible parts

#### 4.4 Add Design Comparison
**File**: `yc_jigsaw_demo/frontend/src/demo/components/DesignComparison.tsx` (NEW)

**Features**:
- Compare current design with previous versions
- Show what changed
- Suggest optimizations
- A/B test different part selections

### Phase 5: Modern UX Enhancements

#### 5.1 Add Toast Notifications
**File**: `yc_jigsaw_demo/frontend/src/demo/components/Toast.tsx` (NEW)

**Features**:
- Success notifications when fixes applied
- Error notifications with retry options
- Info notifications for design updates
- Auto-dismiss with manual dismiss option

#### 5.2 Add Keyboard Shortcuts
**File**: `yc_jigsaw_demo/frontend/src/demo/JigsawDemo.tsx`

**Shortcuts**:
- `Ctrl/Cmd + S`: Save design
- `Ctrl/Cmd + Z`: Undo
- `Ctrl/Cmd + Shift + Z`: Redo
- `Ctrl/Cmd + F`: Focus search
- `Esc`: Dismiss modals/panels

#### 5.3 Add Design Templates
**File**: `yc_jigsaw_demo/frontend/src/demo/components/DesignTemplates.tsx` (NEW)

**Features**:
- Pre-built design templates
- Common circuit patterns
- One-click apply template
- Customize template

#### 5.4 Add Export/Import
**File**: `yc_jigsaw_demo/frontend/src/demo/JigsawDemo.tsx`

**Features**:
- Export design to JSON
- Import design from JSON
- Export BOM to CSV/Excel
- Export to KiCad (via EDA assets)

## Implementation Order

### Week 1: Critical Fixes
1. Fix parallel task execution (1.1)
2. Add progress tracking (1.2)
3. Improve design analyzer timeout (1.3)
4. Ensure completion event (1.4)
5. Test workflow with multiple parts

### Week 2: Auto-Fix Backend
1. Enhance AutoFixAgent (2.1)
2. Add real-time validation endpoint (2.2)
3. Add fix application endpoint (2.3)
4. Test auto-fix suggestions

### Week 3: Auto-Fix Frontend
1. Create AutoFixPanel (3.1)
2. Enhance BOMInsights (3.2)
3. Add real-time validation (3.3)
4. Add part replacement UI (3.4)

### Week 4: Engineering Features
1. Add design health score (4.1)
2. Add recommendations engine (4.2)
3. Add compatibility warnings (4.3)
4. Add design comparison (4.4)

### Week 5: UX Polish
1. Add toast notifications (5.1)
2. Add keyboard shortcuts (5.2)
3. Add design templates (5.3)
4. Add export/import (5.4)

## Files to Create/Modify

### Backend
- `yc_jigsaw_demo/charles_agentPCB_folder/api/server.py` - Fix workflow, add endpoints
- `yc_jigsaw_demo/charles_agentPCB_folder/agents/auto_fix_agent.py` - Enhance with intelligent fixes
- `yc_jigsaw_demo/charles_agentPCB_folder/agents/design_analyzer.py` - Add actionable recommendations

### Frontend
- `yc_jigsaw_demo/frontend/src/demo/components/AutoFixPanel.tsx` - NEW: Auto-fix UI
- `yc_jigsaw_demo/frontend/src/demo/components/Toast.tsx` - NEW: Toast notifications
- `yc_jigsaw_demo/frontend/src/demo/components/DesignTemplates.tsx` - NEW: Design templates
- `yc_jigsaw_demo/frontend/src/demo/components/DesignComparison.tsx` - NEW: Design comparison
- `yc_jigsaw_demo/frontend/src/demo/components/BOMInsights.tsx` - Enhance with auto-fix
- `yc_jigsaw_demo/frontend/src/demo/components/PartsList.tsx` - Add part replacement
- `yc_jigsaw_demo/frontend/src/demo/components/ComponentGraph.tsx` - Add compatibility warnings
- `yc_jigsaw_demo/frontend/src/demo/JigsawDemo.tsx` - Add real-time validation, keyboard shortcuts
- `yc_jigsaw_demo/frontend/src/demo/services/analysisApi.ts` - Add auto-fix endpoints

## Success Criteria

1. ✅ Workflow processes all parts without hanging
2. ✅ Progress updates shown for each step
3. ✅ Errors detected in real-time
4. ✅ Fix suggestions appear immediately
5. ✅ One-click apply fixes works
6. ✅ Part replacements suggested and applied
7. ✅ Design health score visible
8. ✅ All fixes are compatible with existing design
9. ✅ Cost impact shown before applying fixes
10. ✅ Undo/redo works for fixes

