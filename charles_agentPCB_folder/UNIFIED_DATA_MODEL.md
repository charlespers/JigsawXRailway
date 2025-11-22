# Unified Data Model Specification

## Overview

This document defines the unified data model used by both frontend and backend to ensure perfect compatibility.

## Core Data Structures

### 1. PartObject (Frontend/Backend Compatible)

```typescript
interface PartObject {
  // Core identification
  componentId: string; // CRITICAL: Maps to backend block_name
  mpn: string;
  manufacturer: string;
  description: string;

  // Pricing
  price: number;
  currency?: string;
  quantity?: number;

  // Electrical
  voltage?: string;
  interfaces?: string[];

  // Physical
  package?: string;
  footprint?: string;
  mounting_type?: string;

  // Lifecycle
  lifecycle_status?: string;
  availability_status?: string;
  lead_time_days?: number;
  rohs_compliant?: boolean;

  // Extended
  datasheet?: string;
  category?: string;
  tolerance?: string;
  msl_level?: string | number;
  assembly_side?: "top" | "bottom" | "both";
  alternate_part_numbers?: string[];
  distributor_part_numbers?: Record<string, string>;
  temperature_rating?: string;
  test_point?: boolean;
  fiducial?: boolean;
  assembly_notes?: string;
}
```

### 2. Backend Design State

```python
design_state = {
    "requirements": Dict[str, Any],
    "architecture": Dict[str, Any],
    "selected_parts": Dict[str, Dict[str, Any]],  # block_name -> full_part_data
    "external_components": List[Dict[str, Any]],
    "compatibility_results": Dict[str, Dict[str, Any]],
    "intermediaries": Dict[str, str],  # block_name -> intermediary_block_name
    "connections": List[Dict[str, Any]],
    "bom": Dict[str, Any],
    "design_analysis": Dict[str, Any]
}
```

### 3. Frontend Design State

```typescript
interface DesignState {
  parts: PartObject[]; // Array with componentId preserved
  selectedComponents: Map<string, ComponentNode>; // componentId -> ComponentNode
  connections: Connection[];
  query?: string;
  timestamp?: string;
}
```

### 4. ComponentNode (Frontend Visualization)

```typescript
interface ComponentNode {
  id: string; // Same as componentId
  label: string;
  status: "pending" | "reasoning" | "selected" | "validated";
  reasoning: string[];
  hierarchyLevel: number;
  partData?: PartObject;
  compatibilityWarnings?: string[];
  compatibleAlternatives?: PartObject[];
}
```

## Data Flow

### Backend → Frontend (Selection Event)

1. **Backend**: `selected_parts[block_name] = full_part_data`
2. **Backend**: `part_object = part_data_to_part_object(full_part_data)`
3. **Backend**: Add `componentId: block_name` to part_object
4. **Backend**: Emit `{"type": "selection", "componentId": block_name, "partData": part_object}`
5. **Frontend**: Receive event, extract `componentId` and `partData`
6. **Frontend**: Store in `parts` array with `componentId` preserved
7. **Frontend**: Store in `selectedComponents` Map with `componentId` as key

### Frontend → Backend (Export/Import)

1. **Export**: Include `componentId` in each PartObject
2. **Import**: Reconstruct `selected_parts` dict using `componentId` as key
3. **Import**: Reconstruct `selectedComponents` Map using `componentId` as key

## Key Principles

1. **componentId = block_name**: Always maintain this mapping
2. **Preserve Full Data**: Backend keeps full part data, frontend gets simplified view
3. **Bidirectional Conversion**: Can convert between formats without data loss
4. **Single Source of Truth**: Backend `selected_parts` is authoritative
