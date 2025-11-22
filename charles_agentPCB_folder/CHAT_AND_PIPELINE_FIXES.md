# Chat Conversation & Pipeline Fixes

## Problem 1: Chat Resets Request Instead of Continuing Conversation

### Current Issue

- Every new chat message triggers a full component analysis reset
- No distinction between new design vs. follow-up questions
- No conversation context maintained
- No query routing to appropriate agents

### Root Causes

1. `JigsawDemo.tsx` line 97-108: `handleQuerySent` always resets if query differs
2. No query intent classification (new design vs. refinement vs. question)
3. No conversation state management
4. Backend always runs full `generate_design_stream` regardless of query type

### Solution: Query Router & Conversation Management

#### A. Create Query Router Agent

**File**: `charles_agentPCB_folder/agents/query_router_agent.py`

- Classify query intent:

  - `new_design`: Full component analysis needed
  - `refinement`: Modify existing design (change parts, add components)
  - `question`: Answer about current design (cost, power, compatibility)
  - `analysis_request`: Run specific analysis (thermal, signal integrity, etc.)
  - `context_request`: Need more information from user

- Extract action details:
  - Which parts to modify
  - What analysis to run
  - What information is needed

#### B. Conversation State Management

**File**: `charles_agentPCB_folder/api/conversation_manager.py`

- Maintain conversation history per session
- Track current design state
- Store context for follow-up queries
- Session-based state (can use in-memory dict for now, DB later)

#### C. Update Backend API

**File**: `charles_agentPCB_folder/api/server.py`

- Add conversation context parameter
- Route queries based on intent:
  - `new_design` → Full `generate_design_stream`
  - `refinement` → `refine_design_stream` (modify existing)
  - `question` → `answer_question` (use existing design state)
  - `analysis_request` → Run specific agent analysis

#### D. Update Frontend

**Files**:

- `frontend/src/demo/JigsawDemo.tsx`
- `frontend/src/demo/components/DesignChat.tsx`
- `frontend/src/demo/components/ComponentGraph.tsx`

- Maintain conversation session ID
- Pass conversation context with queries
- Don't reset on follow-up queries
- Show conversation history in chat
- Handle different response types (analysis results, answers, part updates)

## Problem 2: Pipeline Gets Stuck After 1-2 Parts

### Current Issue

- Workflow loads first component (anchor) successfully
- May load 1-2 supporting parts
- Then stops processing remaining parts
- No error messages, just hangs

### Root Causes

1. **Dead code block** in `server.py` lines 485-532:

   - Mis-indented code block after Step 5
   - References undefined variables (`block`, `part`, `anchor_part`)
   - This code never executes but may cause confusion

2. **Silent failures** in `_process_block_async`:

   - If part selection fails, function returns early
   - No error propagation to queue
   - Loop continues but appears stuck

3. **Parallel processing issues**:

   - Tasks may fail silently
   - No progress updates if all tasks in a batch fail
   - Hierarchy level increments even if no parts selected

4. **Missing completion signal**:
   - If all parts fail to select, workflow may not emit "complete"
   - Frontend waits indefinitely

### Solution: Fix Workflow & Error Handling

#### A. Remove Dead Code

**File**: `charles_agentPCB_folder/api/server.py` lines 485-532

- Delete the mis-indented dead code block
- Ensure Step 6 (datasheet enrichment) starts correctly

#### B. Improve Error Handling in `_process_block_async`

**File**: `charles_agentPCB_folder/api/server.py`

- Always emit progress updates, even on failures
- Emit error messages to queue instead of silently returning
- Track which blocks succeeded/failed
- Continue processing even if some blocks fail

#### C. Add Workflow Completion Guarantees

**File**: `charles_agentPCB_folder/api/server.py`

- Always emit "complete" event, even if no parts selected
- Include summary of what was processed
- Track and report skipped/failed blocks

#### D. Add Progress Tracking

**File**: `charles_agentPCB_folder/api/server.py`

- Emit progress updates: "Processing block X of Y"
- Show which blocks are being processed
- Report completion status for each block

## Implementation Plan

### Phase 1: Fix Pipeline Hanging (Critical - Do First)

1. Remove dead code block (lines 485-532)
2. Fix error handling in `_process_block_async`
3. Add completion guarantees
4. Add progress tracking
5. Test with multiple components

### Phase 2: Query Router (Enable Conversations)

1. Create `query_router_agent.py`
2. Create `conversation_manager.py`
3. Update backend API to use router
4. Update frontend to maintain conversation state
5. Test conversation flow

### Phase 3: Refinement Operations

1. Create `refine_design_stream` function
2. Implement part modification logic
3. Add UI for showing modifications
4. Test refinement scenarios

### Phase 4: Question Answering

1. Create `answer_question` function
2. Use existing design state to answer questions
3. Route to appropriate analysis agents
4. Display answers in chat

## Files to Modify

### Backend

- `charles_agentPCB_folder/api/server.py` - Remove dead code, fix workflow, add routing
- `charles_agentPCB_folder/agents/query_router_agent.py` - NEW: Query classification
- `charles_agentPCB_folder/api/conversation_manager.py` - NEW: Conversation state
- `charles_agentPCB_folder/core/orchestrator.py` - Add refinement methods

### Frontend

- `frontend/src/demo/JigsawDemo.tsx` - Conversation state management
- `frontend/src/demo/components/DesignChat.tsx` - Show conversation, handle different responses
- `frontend/src/demo/components/ComponentGraph.tsx` - Handle refinement updates
- `frontend/src/demo/services/componentAnalysisApi.ts` - Add conversation context

## Testing Checklist

### Pipeline Fixes

- [ ] Test with query that generates 5+ components
- [ ] Verify all components are processed
- [ ] Verify "complete" event is always emitted
- [ ] Verify progress updates are shown
- [ ] Test with components that fail selection (should continue)

### Conversation Fixes

- [ ] Test new design request (should reset)
- [ ] Test follow-up question (should not reset)
- [ ] Test refinement request (should update, not reset)
- [ ] Test analysis request (should run specific analysis)
- [ ] Verify conversation history is maintained
- [ ] Test multiple conversation turns
