# PCB Design Agent System

A multi-agent system that converts natural language PCB design queries into complete circuit designs with BOMs and connection lists.

## Overview

This system implements the architecture described in `questions.txt`:

1. **Requirements Agent** - Extracts structured requirements from natural language
2. **Architecture Agent** - Builds functional hierarchy and selects anchor part
3. **Part Search & Ranking Agent** - Queries database and ranks candidates
4. **Compatibility Agent** - Verifies electrical/mechanical/interface compatibility
5. **Datasheet Agent** - Enriches part data from datasheet cache (mock PDF parsing)
6. **Output Generator** - Produces connection lists and BOMs
7. **Design Orchestrator** - Coordinates all agents through the 7-step process

## Structure

```
development_demo/
├── agents/              # All agent implementations
├── api/                 # FastAPI server for React visualization
├── components/          # React components (visualization)
├── services/            # React API services
├── ui/                  # React UI components
├── data/
│   └── part_database/   # Part database JSON files
├── utils/               # Database utilities
├── pages/               # Streamlit UI
├── JigsawDemo.tsx       # Main React demo component
└── questions.txt        # System specification
```

## Part Database

The database contains:

- **MCUs**: ESP32-S3, ESP32-C3, ATWINC15x0 WiFi modules
- **Sensors**: TMP102, TMP117, DS18B20, LM35 temperature sensors
- **Power**: USB-C connectors, LDO regulators (AMS1117, LM1117), protection components
- **Passives**: Capacitors, resistors (common values)
- **Datasheet Cache**: Mock extracted PDF data

## Usage

### Streamlit UI

Run the Streamlit page:

```bash
cd development_demo
streamlit run pages/DesignGenerator.py
```

Then enter a natural language query like:

- "temperature sensor with wifi and 5V-USBC"
- "ESP32 with temperature sensor and USB-C power"

Click "🎯 Go to Demo" in the top left to access the interactive React visualization.

### React Visualization Demo

The React visualization provides an interactive view of the component selection process with real-time reasoning and component placement.

**Start the API server:**

```bash
cd development_demo
python -m api.server
```

The API server runs on `http://localhost:3001` by default.

**Run the React frontend** (if you have Node.js/npm set up):

```bash
# Install dependencies (if needed)
npm install

# Run development server
npm run dev
```

The React demo connects to the API server and streams component reasoning and selections in real-time.

### Programmatic Usage

```python
from agents.design_orchestrator import DesignOrchestrator

orchestrator = DesignOrchestrator()
design = orchestrator.generate_design("temperature sensor with wifi and 5V-USBC")

print(f"Selected {len(design['selected_parts'])} parts")
print(f"Generated {len(design['bom'])} BOM items")
print(f"Created {len(design['connections'])} nets")
```

## Requirements

Install dependencies:

```bash
pip install streamlit requests pandas fastapi uvicorn python-dotenv
```

Required packages:

- Python 3.8+
- streamlit (for Streamlit UI)
- requests (for API calls)
- pandas (for BOM display)
- fastapi (for API server - React visualization)
- uvicorn (for API server - React visualization)
- python-dotenv (optional, for .env file support)

API key for chosen LLM provider:

- `OPENAI_API_KEY` (for OpenAI)
- `XAI_API_KEY` (for XAI/Grok)

## Configuration

### Choosing LLM Provider

The system supports both **OpenAI** and **XAI (Grok)** APIs. Choose your provider:

**Set the provider:**

```bash
export LLM_PROVIDER='openai'  # or 'xai'
```

You can also select the provider in the Streamlit UI dropdown.

### Setting up API Keys

#### For OpenAI:

**Option 1: Using the setup script (recommended)**

```bash
cd development_demo
source setup_env.sh
export LLM_PROVIDER='openai'
streamlit run pages/DesignGenerator.py
```

**Option 2: Set environment variables directly**

```bash
export LLM_PROVIDER='openai'
export OPENAI_API_KEY='your-openai-api-key'
```

**Option 3: Create a .env file (if python-dotenv is installed)**
Create a `.env` file in the project root:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
```

Then install python-dotenv:

```bash
pip install python-dotenv
```

#### For XAI (Grok):

```bash
export LLM_PROVIDER='xai'
export XAI_API_KEY='your-xai-api-key'
```

Or in `.env` file:

```
LLM_PROVIDER=xai
XAI_API_KEY=your-xai-api-key
```

### Optional Environment Variables

**For OpenAI:**

- `OPENAI_MODEL`: Model to use (default: "gpt-3.5-turbo", can use "gpt-4" or "gpt-4-turbo-preview" if available)
- `OPENAI_TEMPERATURE`: Temperature for LLM (default: 0.3)

**For XAI:**

- `XAI_MODEL`: Model to use (default: "grok-3")
- `XAI_TEMPERATURE`: Temperature for LLM (default: 0.3)

## Example Output

The system generates:

1. **Architecture**: Block diagram with anchor and child blocks
2. **Selected Parts**: Main components with full specifications
3. **External Components**: Recommended passives and support components
4. **Connection List**: Netlist with all pin connections
5. **BOM**: Complete bill of materials with designators, quantities, part numbers

## Database Schema

Each part card includes:

- Base fields: id, name, category, manufacturer, part number
- Electrical: voltage ranges, current limits, IO levels
- Interfaces: I2C, SPI, UART, WiFi, etc.
- Mechanical: package, footprint, temperature range
- Lifecycle: availability, status, cost
- Application: recommended external components, typical circuit

## Extending the Database

To add new parts:

1. Add part JSON to appropriate category file in `data/part_database/`
2. Optionally add datasheet data to `datasheet_cache.json`
3. Parts will be automatically available for search and selection

## Notes

- Datasheet parsing is currently mocked via `datasheet_cache.json`
- Real PDF parsing can be added by extending `DatasheetAgent`
- The system uses OpenAI API for LLM reasoning (GPT-4 by default)
- All agents return structured JSON for easy integration
- API keys are stored securely and never committed to git (see `.gitignore`)
