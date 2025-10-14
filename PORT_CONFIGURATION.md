# Port Configuration

To avoid conflicts with the existing AI Orchestrator project, the DevAI extensions use different ports:

## Port Assignments

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Original Orchestrator API** | 8000 | http://localhost:8000 | Existing FastAPI service |
| **Original Frontend** | 3000 | http://localhost:3000 | Existing React UI |
| **DevAI Simulation API** | 8002 | http://localhost:8002 | New simulation & metrics API |
| **Streamlit Dashboard** | 8501 | http://localhost:8501 | New self-dev dashboard |

## Why Different Ports?

The original AI Orchestrator already uses:
- **Port 8000**: Main FastAPI application (`src/api/main.py`)
- **Port 3000**: React frontend (`frontend/`)

The new DevAI simulation modules use:
- **Port 8002**: Separate API for simulation metrics (`api/server.py`)
- **Port 8501**: Streamlit dashboard (default Streamlit port)

## Starting Services

### Original AI Orchestrator (Existing)
```bash
# Backend
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm run dev
# Opens at http://localhost:3000
```

### DevAI Simulation Extensions (New)
```bash
# Simulation API
cd api && python server.py
# Opens at http://localhost:8002

# Dashboard
cd dashboard && streamlit run dashboard.py
# Opens at http://localhost:8501
```

## Running Both Systems

You can run both the original orchestrator and the DevAI extensions simultaneously:

```bash
# Terminal 1: Original API
poetry run uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Original Frontend
cd frontend && npm run dev

# Terminal 3: DevAI Simulation API
cd api && python server.py

# Terminal 4: DevAI Dashboard
cd dashboard && streamlit run dashboard.py
```

## Quick Access URLs

### Original System
- API: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Metrics: http://localhost:8000/metrics

### DevAI Extensions
- Simulation API: http://localhost:8002/docs
- Growth Metrics: http://localhost:8002/growth
- Self-Dev Dashboard: http://localhost:8501

## Environment Variables

The ports are configured in `.env`:

```bash
# Original orchestrator
ORCHESTRATOR_PORT=8000

# DevAI simulation API
DEVAI_API_PORT=8002
```

## Integration

Both systems share the same underlying modules (`src/core/`, `src/providers/`, etc.) but expose different interfaces:

- **Original**: Production multi-LLM orchestration with tool execution
- **DevAI**: Simulation, self-development tracking, and metrics visualization

They can be used independently or together depending on your needs.
