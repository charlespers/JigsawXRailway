# PCB Design BOM Generator

Enterprise-ready PCB design system with agent-based component reasoning.

## Architecture

Clean, modular architecture following enterprise best practices:

```
app/
├── main.py              # FastAPI application entry point
├── core/                # Core configuration and utilities
│   ├── config.py       # Application settings
│   ├── logging.py      # Logging configuration
│   └── exceptions.py   # Custom exceptions
├── domain/              # Domain models and business logic
│   ├── models.py       # Pydantic models (IPC-2581 compliant)
│   └── part_database.py # Part database interface
├── agents/              # Agent-based reasoning
│   ├── base.py         # Base agent with LLM integration
│   ├── requirements.py # Requirements extraction
│   ├── architecture.py # Architecture design
│   ├── part_selection.py # Part selection
│   ├── compatibility.py # Compatibility checking
│   └── bom_generator.py # BOM generation (IPC-2581)
├── services/            # Business logic services
│   └── orchestrator.py # Design orchestration
└── api/                 # API layer
    ├── schemas.py      # Request/response schemas
    └── routes.py        # API endpoints
```

## Features

- **Agent-based Reasoning**: LLM-powered requirements extraction and architecture design
- **IPC Standards**: IPC-2581 compliant BOM generation, IPC-7351 footprint standards
- **Compatibility Checking**: Electrical and mechanical compatibility validation
- **Clean Architecture**: Modular, testable, maintainable codebase
- **Enterprise Ready**: Proper error handling, logging, configuration management

## API Endpoints

- `POST /api/v1/design/generate` - Generate complete PCB design from query
- `POST /api/v1/bom/generate` - Generate BOM from selected parts
- `GET /health` - Health check

## Environment Variables

- `XAI_API_KEY` - xAI API key for LLM
- `LLM_PROVIDER` - LLM provider (default: xai)
- `CORS_ORIGINS` - CORS allowed origins (comma-separated)
- `LOG_LEVEL` - Logging level (default: INFO)
- `PORT` - Server port (default: 8000)

## Deployment

Deploy to Railway using Nixpacks:

```bash
railway up
```

The application will automatically:
1. Install dependencies
2. Start the FastAPI server
3. Serve on the PORT environment variable

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m app.main
```

## Engineering Standards

- **IPC-2581**: BOM format compliance
- **IPC-7351**: Footprint naming standards
- **Electrical Compatibility**: Voltage, current, IO level checking
- **Mechanical Compatibility**: Package, footprint validation

