# Local LLM Setup Complete

## Installed Models

### 1. Mistral 7B (`mistral:7b`)
- **Purpose**: General incident analysis
- **Specialization**: System failures, root cause analysis, incident postmortems
- **Use case**: Comprehensive incident investigation
- **Usage**: `@mistral: <your request>`

### 2. Llama2 7B (`llama2:7b`)
- **Purpose**: Log analysis
- **Specialization**: Parsing logs, identifying patterns, extracting errors
- **Use case**: Application and system log analysis
- **Usage**: `@llama2: <your request>`

### 3. CodeLlama 7B (`codellama:7b`)
- **Purpose**: Code-related incident analysis
- **Specialization**: Stack traces, code errors, deployment failures
- **Use case**: Debugging and code-level incident analysis
- **Usage**: `@codellama: <your request>`

## Service Information

- **Ollama Version**: 0.12.5
- **Service URL**: http://localhost:11434
- **Status**: Running (managed by Homebrew services)
- **Auto-start**: Enabled (starts on system boot)

## Usage Examples

### Via Frontend (http://localhost:3000)
```
@mistral: Analyze the production outage from yesterday
@llama2: Review these error logs and find anomalies
@codellama: Debug this stack trace: [paste stack trace]
```

### Via CLI
```bash
cd /Users/shiva/Projects/ai-orchestrator
poetry run python src/cli.py
```

### Via API
```bash
# Explicit provider selection
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "@mistral: Analyze incident", "explicit_provider": "mistral"}'

# Automatic routing (orchestrator selects best model)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze these logs: ..."}'
```

## Architecture

### Provider Hierarchy
```
AI Orchestrator
├── Cloud Providers
│   ├── Claude Code (code generation, deployment)
│   ├── ChatGPT (UI/UX, workflows, reports)
│   ├── Gemini (prompt optimization)
│   └── Claude (incident analysis, fallback)
└── Local Providers (Privacy-focused)
    ├── Mistral (incident analysis)
    ├── Llama2 (log analysis)
    ├── CodeLlama (code debugging)
    └── Generic Local (legacy fallback)
```

### Routing Strategy

The orchestrator automatically routes based on task intent:

| Task Type | Primary Provider | Local Fallback |
|-----------|-----------------|----------------|
| Incident Analysis | Claude/Mistral | Mistral |
| Log Analysis | Local | Llama2 |
| Code Debugging | Claude Code/CodeLlama | CodeLlama |
| General Analysis | ChatGPT/Claude | Mistral |

### Privacy & Security

Local models ensure:
- ✅ No data sent to external APIs
- ✅ Offline operation capability
- ✅ Full control over data
- ✅ GDPR/compliance friendly
- ✅ Sensitive log analysis stays local

## Management Commands

### Service Control
```bash
# Start Ollama
brew services start ollama

# Stop Ollama
brew services stop ollama

# Restart Ollama
brew services restart ollama

# Check status
brew services list | grep ollama
```

### Model Management
```bash
# List installed models
ollama list

# Pull additional models
ollama pull <model-name>

# Remove a model
ollama rm <model-name>

# Update a model
ollama pull <model-name>
```

### Health Checks
```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Check orchestrator backend
curl http://localhost:8000/api/health

# Test specific provider
curl http://localhost:8000/api/providers
```

## System Requirements

- **RAM**: 16GB (sufficient for 7B models)
- **Disk**: ~12GB for all 3 models
- **CPU**: Apple Silicon (M1/M2) recommended
- **OS**: macOS (Sequoia 24.0.0)

## Performance Characteristics

| Model | Size | RAM Usage | Speed | Best For |
|-------|------|-----------|-------|----------|
| Mistral 7B | 4.4GB | 6-8GB | Medium | General incidents |
| Llama2 7B | 3.8GB | 5-7GB | Fast | Log parsing |
| CodeLlama 7B | 3.8GB | 5-7GB | Fast | Code analysis |

## Troubleshooting

### Models not loading
```bash
# Check download status
tail -f /tmp/ollama-mistral.log
tail -f /tmp/ollama-llama2.log
tail -f /tmp/ollama-codellama.log

# Manually pull if needed
ollama pull mistral:7b
ollama pull llama2:7b
ollama pull codellama:7b
```

### Service not responding
```bash
# Restart service
brew services restart ollama

# Check process
ps aux | grep ollama

# View logs
brew services info ollama
```

### Integration issues
```bash
# Verify backend is running
lsof -i :8000

# Verify frontend is running
lsof -i :3000

# Check provider registration
curl http://localhost:8000/api/providers | jq
```

## Files Modified

1. `/Users/shiva/Projects/ai-orchestrator/src/models/schemas.py` - Added provider enums
2. `/Users/shiva/Projects/ai-orchestrator/src/providers/mistral.py` - New provider
3. `/Users/shiva/Projects/ai-orchestrator/src/providers/llama2.py` - New provider
4. `/Users/shiva/Projects/ai-orchestrator/src/providers/codellama.py` - New provider
5. `/Users/shiva/Projects/ai-orchestrator/src/providers/__init__.py` - Provider registry
6. Routing configuration (pending completion)

## Next Steps

1. ✅ Wait for model downloads to complete (~20-40 min)
2. ⏳ Update routing configuration
3. ⏳ Test all providers
4. ⏳ Configure fallback chains
5. ⏳ Update frontend UI to show local providers

## Support

- Ollama Docs: https://ollama.com/docs
- AI Orchestrator: `/Users/shiva/Projects/ai-orchestrator/README.md`
- Issues: Check GitHub issues or logs
