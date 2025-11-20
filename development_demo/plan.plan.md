<!-- 4ca592f1-6318-4617-86e3-8b872e66741d 271c0090-4564-4fa0-9529-be3de196b0ca -->
# PCB Design Agent System Implementation Plan

## Overview

Implement a multi-agent system that converts natural language PCB design queries (e.g., "temperature sensor with wifi and 5V-USBC") into complete circuit designs with BOMs and connection lists, following the architecture described in `development_demo/questions.txt`.

## Architecture Components

### 1. Part Database (`backend/data/part_database/`)

- **Structure**: JSON-based normalized database with multiple files:
  - `parts_base.json` - Base part cards with common fields (id, name, category, manufacturer, mfr_part_number, datasheet_url, etc.)
  - `parts_mcu.json` - MCU-specific parts (ESP32-S3, ATWINC15x0, etc.)
  - `parts_sensors.json` - Sensor parts (temperature sensors, etc.)
  - `parts_power.json` - Power components (regulators, USB-C connectors, protection)
  - `parts_passives.json` - Passive components (capacitors, resistors)
  - `datasheet_cache.json` - Mock extracted datasheet data (simulates PDF parsing results)

- **Schema**: Each part card includes:
  - Base fields: id, name, category, manufacturer, mfr_part_number, description, datasheet_url
  - Electrical: supply_voltage_range, io_voltage_levels, current_max, power_rating
  - Interfaces: interface_type (I2C, SPI, UART, etc.), pinout
  - Mechanical: package, footprint, operating_temp_range
  - Lifecycle: availability_status, lifecycle_status, cost_estimate
  - Application templates: recommended_external_components, typical_circuit

### 2. Requirements Agent (`backend/agents/requirements_agent.py`)

- **Purpose**: Convert natural language query → structured requirements
- **Input**: User query string
- **Output**: Structured JSON with:
  - Functional blocks (MCU, sensor, power, etc.)
  - Constraints (voltage, current, interfaces, temp range)
  - Preferences (package type, cost, availability)
- **Implementation**: LLM call to XAI API with structured prompt

### 3. Architecture/Topology Agent (`backend/agents/architecture_agent.py`)

- **Purpose**: Build functional hierarchy and select anchor part
- **Input**: Structured requirements
- **Output**: Block diagram with:
  - Anchor part (most connected component, e.g., WiFi MCU)
  - Child blocks (power, sensor, connectors)
  - Dependency graph (which blocks depend on which)
  - Constraints per block (voltage rails, interfaces)
- **Implementation**: LLM-based reasoning with rule base

### 4. Part Search & Ranking Agent (`backend/agents/part_search_agent.py`)

- **Purpose**: Query database and rank candidates
- **Input**: Search criteria (category, constraints)
- **Output**: Ranked list of candidate parts with scores
- **Implementation**: 
  - Database query functions (filter by category, voltage range, interface type)
  - Scoring algorithm (hard constraints vs soft constraints)
  - Integration with part database loader

### 5. Compatibility & Constraint Checking Agent (`backend/agents/compatibility_agent.py`)

- **Purpose**: Verify electrical/mechanical/interface compatibility
- **Input**: Two or more parts + connection requirements
- **Output**: Compatibility result with:
  - compatible: bool
  - reasoning: str
  - risks: List[str]
  - required_buffers: List[str] (e.g., level shifters)
- **Implementation**: 
  - Rule-based checks (voltage ranges, current limits)
  - LLM-based reasoning for complex cases
  - Interface compatibility checking

### 6. Datasheet Parsing & Enrichment Agent (`backend/agents/datasheet_agent.py`)

- **Purpose**: Extract missing attributes from datasheets (mocked)
- **Input**: Part ID or datasheet reference
- **Output**: Enriched part attributes
- **Implementation**: 
  - Mock implementation that queries `datasheet_cache.json`
  - Simulates PDF parsing by returning structured data
  - Can be extended later with real PDF parsing

### 7. Output Generator (`backend/agents/output_generator.py`)

- **Purpose**: Generate connection list (netlist) and BOM
- **Input**: Selected parts + architecture graph
- **Output**: 
  - Connection list: List of nets with (part_id, pin_name) pairs
  - BOM: List with designator, qty, manufacturer, part number, description, etc.
- **Implementation**: 
  - Graph traversal to build nets
  - Designator assignment (U1, U2, R1, C1, etc.)
  - BOM grouping and formatting

### 8. Main Design Orchestrator (`backend/agents/design_orchestrator.py`)

- **Purpose**: Coordinate all agents through the 7-step process
- **Steps**:

  1. Requirements extraction
  2. Architecture/hierarchy building
  3. Anchor part selection
  4. Expand requirements around anchor
  5. Select supporting parts with compatibility checks
  6. Use datasheet data for missing fields
  7. Constraint resolution & scoring
  8. Generate outputs

- **Implementation**: Sequential agent calls with state management

### 9. Database Utilities (`backend/utils/part_database.py`)

- **Purpose**: Load and query part database
- **Functions**:
  - `load_part_database()` - Load all part files
  - `search_parts(category, constraints)` - Query parts
  - `get_part_by_id(part_id)` - Get specific part
  - `get_application_template(part_id)` - Get recommended circuit

### 10. New Streamlit Page (`backend/pages/DesignGenerator.py`)

- **Purpose**: UI for natural language design generation
- **Features**:
  - Text input for natural language query
  - Step-by-step progress display
  - Results: Architecture diagram, selected parts, BOM table, connection list
  - Export options (JSON, CSV)

## File Structure

```
backend/
├── agents/
│   ├── __init__.py
│   ├── requirements_agent.py
│   ├── architecture_agent.py
│   ├── part_search_agent.py
│   ├── compatibility_agent.py
│   ├── datasheet_agent.py
│   ├── output_generator.py
│   └── design_orchestrator.py
├── data/
│   ├── part_database/
│   │   ├── parts_base.json
│   │   ├── parts_mcu.json
│   │   ├── parts_sensors.json
│   │   ├── parts_power.json
│   │   ├── parts_passives.json
│   │   └── datasheet_cache.json
│   └── component_library.json (existing)
├── utils/
│   └── part_database.py (new)
└── pages/
    └── DesignGenerator.py (new)
```

## Implementation Details

### Part Database Content

- **MCUs**: ESP32-S3, ESP32-C3, ATWINC15x0, nRF52840 (WiFi/BLE capable)
- **Sensors**: TMP102, TMP117, DS18B20, LM35 (temperature sensors with I2C/SPI/analog)
- **Power**: USB-C connectors, LDO regulators (AMS1117, LM1117), buck converters, polyfuses, TVS diodes
- **Passives**: Common capacitors (0.1µF, 10µF), resistors (pull-ups, current limiting), crystals

### Mock Datasheet Data

- Simulated extracted fields: pin descriptions, electrical characteristics, application circuits
- Stored as structured JSON matching what real PDF parsing would produce

### Agent Communication

- Agents use XAI API (Grok) for LLM reasoning
- Structured JSON responses for all agent outputs
- Error handling and fallback logic

### Integration Points

- Reuse existing `ComponentAgent` pattern for consistency
- Use existing `ComponentRegistry` for storing generated designs
- Follow existing Streamlit page patterns

## Testing Strategy

- Unit tests for each agent
- Integration test with example query: "temperature sensor with wifi and 5V-USBC"
- Verify BOM and connection list correctness