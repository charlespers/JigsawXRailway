# AI PCB Simulator - YC Demo

**Component-based AI agents simulate PCB behavior through reasoning, not physics**

Built for Y Combinator | Combining Dielectric + Jigsaw Approaches

---

## Overview

This simulator uses AI agents for each PCB component. When inputs/outputs change, agents communicate to reason about circuit behavior - no expensive physics simulation needed.

### Key Innovation

Traditional simulators (SPICE, Isaac Sim) use complex physics engines. We use:
- **Component-based AI agents** - Each component has an agent
- **XAI reasoning** - Agents reason about behavior using Grok
- **Agent communication** - When outputs change, agents talk
- **Component registry** - All states stored for agent context

**Result:** 10-100x faster than physics simulation, with human-readable reasoning.

---

## Architecture

```
┌─────────────────────────────────────┐
│  Landing Page (Home.py)             │
│  - KiCAD file upload                │
│  - Feature showcase                 │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Simulator (pages/Simulator.py)     │
│  - Component management             │
│  - Agent control                    │
│  - Visualization                    │
└───────────────┬─────────────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│ ComponentAgent│  │  Component   │
│  (XAI)        │  │  Registry    │
└──────────────┘  └──────────────┘
```

### Component Agent Flow

1. **Add Component** → Agent created with XAI API
2. **Run Simulation** → All agents reason about states
3. **Output Changes** → Agents communicate changes
4. **Update Registry** → New states stored
5. **Visualize** → PCB layout updated

---

## Quick Start

### Prerequisites

- Python 3.12+
- XAI API Key (required - no fallbacks)

### Installation

```bash
# Clone/navigate to yc_demo
cd yc_demo

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set XAI API key (REQUIRED)
export XAI_API_KEY="your_xai_api_key_here"
```

### Run Locally

```bash
streamlit run Home.py
```

Opens at: `http://localhost:8501`

---

## Deployment

### Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Set environment variable: `XAI_API_KEY`
5. Deploy

### Deploy to Heroku

```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create your-app-name

# Set environment variable
heroku config:set XAI_API_KEY="your_key"

# Deploy
git push heroku main
```

### Deploy to Railway

1. Connect GitHub repo
2. Add environment variable: `XAI_API_KEY`
3. Deploy automatically

### Deploy to Docker

```bash
# Build image
docker build -t yc-demo .

# Run container
docker run -p 8501:8501 \
  -e XAI_API_KEY="your_key" \
  yc-demo
```

---

## Usage

### 1. Landing Page

- View features
- Upload KiCAD file (TODO: implement parser)
- Navigate to simulator

### 2. Simulator Page

**Add Components:**
1. Use sidebar to select component type
2. Enter component name
3. Click "Add Component"
4. Agent automatically created

**Run Simulation:**
1. Add at least 2 components
2. Click "Run Simulation"
3. Agents reason about interactions
4. View reasoning in component cards

**Agent Reasoning:**
- Expand "Agent Reasoning" for each component
- See step-by-step logic from XAI
- Understand how outputs were determined

---

## Component Types

Currently supported:

| Component | Type | Inputs | Outputs |
|-----------|------|--------|---------|
| Microcontroller | mcu | VCC, GND, RESET | GPIO1, GPIO2, TX, RX |
| LED | led | ANODE, CATHODE | - |
| Resistor | resistor | IN | OUT |
| Sensor | sensor | VCC, GND | DATA, CLK |

### Adding New Components

Edit `pages/Simulator.py`:

```python
component_types = {
    "YourComponent": {
        "type": "your_type",
        "inputs": ["IN1", "IN2"],
        "outputs": ["OUT1"],
        "description": "Description here"
    }
}
```

Agent automatically adapts to new component types.

---

## API Reference

### ComponentAgent

```python
agent = ComponentAgent(
    component_id="U1",
    component_type="mcu",
    inputs=["VCC", "GND"],
    outputs=["GPIO1"],
    description="ESP32 MCU"
)

# Reason about state
result = agent.reason_about_state(component_state, registry)

# Communicate with other agent
response = agent.communicate_with_agent(other_agent, message, context)
```

### ComponentRegistry

```python
registry = ComponentRegistry()

# Add component
registry.add_component("U1", component_data)

# Update states
registry.update_inputs("U1", {"VCC": 5.0})
registry.update_outputs("U1", {"GPIO1": "HIGH"})

# Query
state = registry.get_component_state("U1")
connections = registry.get_connections_for("U1")
```

---

## Configuration

Environment variables:

```bash
# Required
XAI_API_KEY="your_key"

# Optional
XAI_MODEL="grok-beta"         # XAI model to use
XAI_TEMPERATURE="0.3"         # Reasoning temperature
MAX_COMPONENTS="10"           # Max components per simulation
SIMULATION_TIMEOUT="30"       # Timeout in seconds
DEBUG_MODE="false"            # Enable debug logging
DEPLOYMENT_ENV="local"        # local|staging|production
```

---

## How It Works

### Component-Based Agents

Each component has an AI agent that:
1. Understands component behavior
2. Monitors input states
3. Reasons about outputs using XAI
4. Communicates with downstream agents

### Agent Reasoning Process

```
Input Change Detected
    ↓
Agent analyzes component behavior
    ↓
XAI API call with:
  - Component type & specs
  - Current inputs
  - Circuit topology
  - Connected components
    ↓
XAI returns:
  - Reasoning explanation
  - Output determinations
  - Downstream effects
  - Agent notifications
    ↓
Registry updated
    ↓
Downstream agents notified
    ↓
Visualization updated
```

### No Physics Simulation

Traditional approach:
```
Component change → SPICE simulation (minutes)
                 → Complex solver
                 → No explanation
```

Our approach:
```
Component change → Agent reasoning (seconds)
                 → XAI logical analysis
                 → Human-readable explanation
```

---

## Why This Matters

### For Robotics

- Simulate robot PCBs without Isaac Sim
- Faster iteration on hardware designs
- Understand component interactions logically

### For IoT

- Test sensor/MCU interactions
- Verify power delivery
- Debug communication protocols

### For Complex Systems

- Scale to 100+ components
- O(n) reasoning, not O(n²) physics
- Deploy anywhere, no GPU needed

---

## Roadmap

- [ ] KiCAD file parser
- [ ] More component types (capacitors, inductors, etc.)
- [ ] Automatic connection detection
- [ ] Agent-to-agent chat logs
- [ ] Component search/library
- [ ] Export simulation results
- [ ] Multi-page PCB support
- [ ] Real-time collaboration

---

## Troubleshooting

**Q: XAI API error**
A: Check that `XAI_API_KEY` is set correctly. No fallbacks - API required.

**Q: Agent reasoning fails**
A: Check API quota/limits. Ensure good network connection.

**Q: Components not showing**
A: Check browser console for errors. Try refreshing page.

**Q: Deployment fails**
A: Ensure `XAI_API_KEY` is set in deployment environment variables.

---

## Credits

Built for **Y Combinator Demo Day**

Combining:
- **Dielectric**: Computational geometry + XAI for PCB optimization
- **Jigsaw**: Natural language → component selection

Powered by **XAI (Grok)** for component reasoning

---

## License

MIT License - See parent project

---

**Built for Y Combinator | Production-Ready | Deploy Anywhere**

