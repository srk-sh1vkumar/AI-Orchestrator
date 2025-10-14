# AI Orchestrator

An intelligent LLM orchestration system that routes tasks to specialized language models based on their strengths, with direct tool execution capabilities.

## 🎉 **NEW: Web UI Available!**

A beautiful, modern web interface is now available! [See Web UI Guide →](README_WEB_UI.md)

```bash
cd frontend && npm install && npm run dev
# Open http://localhost:3000
```

## Features

- **🖥️ Modern Web UI**: Beautiful interface for easy interaction (NEW!)
- **Intelligent Task Routing**: Automatically routes tasks to the most appropriate LLM based on intent
- **Multi-LLM Collaboration**: Orchestrates complex tasks across multiple LLMs
- **Direct Tool Execution**: LLMs can directly interact with GitHub, CI/CD, Docker, Kubernetes, monitoring systems, and more
- **Fallback Chain**: Robust fallback system for high-availability incident analysis
- **Function Calling**: Full function calling/tool use support for all providers
- **Privacy-First**: Local LLM option for sensitive data analysis
- **Three Interfaces**: Web UI, CLI, and REST API

## Architecture

### Supported LLMs and Their Roles

1. **Claude Code** (Primary Executor & DevOps)
   - Code generation and implementation
   - Technical analysis and debugging
   - Docker/Kubernetes deployment
   - CI/CD pipeline management

2. **ChatGPT** (Interface & Workflow Layer)
   - UI/UX design and implementation
   - Dashboard creation
   - Workflow automation
   - Report generation

3. **Gemini** (Meta-Prompting Layer)
   - Prompt optimization
   - Instruction refinement
   - Template creation
   - Incident analysis (fallback #2)

4. **Claude** (Reasoning & Analysis Fallback)
   - Incident analysis (fallback #1)
   - Complex reasoning
   - Documentation

5. **Local LLM** (Privacy & Analysis Layer)
   - Primary incident analysis
   - Log analysis
   - Security investigations
   - Offline operations

### Tool Integrations

- **Version Control**: GitHub API (repos, PRs, issues)
- **CI/CD**: Jenkins, GitHub Actions
- **Containers**: Docker, Kubernetes
- **Monitoring**: Grafana, Prometheus
- **Logging**: ELK Stack, Splunk, CloudWatch
- **File System**: Direct file operations
- **Terminal**: Command execution
- **Claude Code CLI**: Direct integration

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd ai-orchestrator

# Install dependencies using Poetry
poetry install

# Copy environment configuration
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env
```

### Running the Orchestrator

```bash
# Start the server
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the CLI
poetry run python src/cli.py
```

### Usage Examples

#### Basic Task Routing

```bash
# Automatically routed to Claude Code
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Build a REST API for user management"}'

# Explicitly route to specific LLM
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "@chatgpt: Create a dashboard for monitoring metrics"}'
```

#### Incident Analysis with Fallback

```bash
# Primary: Local LLM → Fallback: Claude → Final: Gemini
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze this production incident", "context": {...}}'
```

#### Multi-LLM Collaboration

```bash
# Orchestrates across Gemini → ChatGPT → Claude Code
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Build a complete monitoring dashboard with deployment"}'
```

## Configuration

See `.env.example` for all configuration options.

### Key Settings

- **LLM Provider Keys**: Configure API keys for each provider
- **Local LLM**: Set up Ollama or other local model server
- **Tool Integrations**: Configure access to external systems
- **Fallback Behavior**: Customize fallback chains and timeouts
- **Quality Checks**: Set thresholds for response quality

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_routing.py
```

## Development

```bash
# Format code
poetry run black src tests

# Lint
poetry run ruff src tests

# Type checking
poetry run mypy src
```

## Monitoring

The orchestrator exposes Prometheus metrics at `/metrics`:
- Request counts and latencies
- LLM routing decisions
- Fallback occurrences
- Tool execution metrics

## License

MIT License
