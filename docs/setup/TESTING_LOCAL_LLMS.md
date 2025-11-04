# Testing Local LLM Providers

## Current Status

Three local LLM models are being downloaded via Ollama:

- **Mistral 7B**: 84% complete (~10 min remaining)
- **Llama2 7B**: 46% complete (~28 min remaining)
- **CodeLlama 7B**: 46% complete (~27 min remaining)

## Verification Steps

### 1. Check Model Download Completion

```bash
# List all downloaded models
ollama list

# Expected output when complete:
# NAME              ID              SIZE      MODIFIED
# mistral:7b        f5074b1221da    4.4 GB    X minutes ago
# llama2:7b         8934d96d3f08    3.8 GB    X minutes ago
# codellama:7b      3a43f93b78ec    3.8 GB    X minutes ago
```

### 2. Test Each Model Directly (Optional)

```bash
# Test Mistral
ollama run mistral:7b "Analyze this production incident: API Gateway timeout at 2024-10-16 22:45 UTC. 500 errors on /api/orders endpoint."

# Test Llama2
ollama run llama2:7b "Parse these logs and identify errors: [ERROR] 2024-10-16 22:45:12 - Connection timeout to product-service"

# Test CodeLlama
ollama run codellama:7b "Debug this stack trace: NullPointerException at OrderService.processCheckout(OrderService.java:124)"
```

### 3. Start AI Orchestrator Backend

```bash
cd /Users/shiva/Projects/ai-orchestrator
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test via API

#### Test Mistral Provider (Incident Analysis)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@mistral: Analyze this production incident: High latency on order-service. 95th percentile response time increased from 200ms to 2500ms. Correlates with MongoDB connection pool exhaustion.",
    "enable_tools": false
  }'
```

**Expected Response**: Detailed incident analysis with root cause hypothesis, impact assessment, and remediation steps.

#### Test Llama2 Provider (Log Analysis)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@llama2: Parse and analyze these application logs:\n[ERROR] 2024-10-16 22:45:12 - OrderService - Connection timeout\n[WARN] 2024-10-16 22:45:13 - MongoDB - Pool size exceeded\n[ERROR] 2024-10-16 22:45:14 - OrderService - Failed to process order ORD-12345\n[INFO] 2024-10-16 22:46:00 - System recovered",
    "enable_tools": false
  }'
```

**Expected Response**: Structured log analysis identifying error patterns, timeline, and correlations.

#### Test CodeLlama Provider (Code Debugging)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@codellama: Debug this stack trace and suggest a fix:\njava.lang.NullPointerException: Cannot invoke method getProductId() on null object\n  at com.ecommerce.order.OrderService.processCheckout(OrderService.java:124)\n  at com.ecommerce.order.OrderController.checkout(OrderController.java:56)\n  at org.springframework.web.method.support.InvocableHandlerMethod.invoke(InvocableHandlerMethod.java:205)",
    "enable_tools": false
  }'
```

**Expected Response**: Root cause analysis of the NPE, location in code, and suggested fix with code example.

### 5. Test via Frontend

1. Start frontend:
```bash
cd /Users/shiva/Projects/ai-orchestrator/frontend
npm run dev
```

2. Open http://localhost:3000

3. In the sidebar, select one of the local providers:
   - Mistral 7B (Incident analysis)
   - Llama2 7B (Log analysis)
   - CodeLlama 7B (Code debugging)

4. Test with appropriate queries:
   - **Mistral**: "Analyze production incident with high latency"
   - **Llama2**: "Parse these error logs: [ERROR] Connection timeout"
   - **CodeLlama**: "Debug NullPointerException in OrderService"

### 6. Test Automatic Routing

The orchestrator should automatically route to the appropriate local LLM based on intent:

```bash
# Should route to Llama2 (log keyword)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze these logs for errors",
    "enable_tools": false
  }'

# Should route to CodeLlama (code/debug keyword)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Debug this NullPointerException",
    "enable_tools": false
  }'

# Should route to Mistral (incident keyword)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Incident analysis for production outage",
    "enable_tools": false
  }'
```

## Provider Specializations

### Mistral 7B
- **Purpose**: General incident analysis
- **System Prompt**: "You are Mistral, a specialized AI for incident analysis and response..."
- **Best For**:
  - Root cause analysis
  - Impact assessment
  - Remediation planning
  - Post-mortem reports

### Llama2 7B
- **Purpose**: Log parsing and analysis
- **System Prompt**: "You are Llama2, a specialized AI for log analysis..."
- **Best For**:
  - Error pattern detection
  - Log aggregation and correlation
  - Timeline reconstruction
  - Anomaly detection in logs

### CodeLlama 7B
- **Purpose**: Code debugging and analysis
- **System Prompt**: "You are CodeLlama, a specialized AI for code-related incident analysis..."
- **Best For**:
  - Stack trace analysis
  - Code error debugging
  - Exception analysis
  - Code fix suggestions

## Troubleshooting

### Models Not Showing in `ollama list`

```bash
# Check download processes
ps aux | grep "ollama pull"

# View download logs
tail -f /tmp/ollama-mistral.log
tail -f /tmp/ollama-llama2.log
tail -f /tmp/ollama-codellama.log
```

### Provider Connection Errors

```bash
# Verify Ollama service is running
brew services list | grep ollama

# Restart Ollama if needed
brew services restart ollama

# Test Ollama API
curl http://localhost:11434/api/tags
```

### Backend Not Routing to Local LLMs

Check `.env` configuration:
```bash
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=mistral:7b
LOCAL_LLM_TIMEOUT=300
```

### Memory Issues

Each 7B model requires ~4-6GB RAM when loaded. With 3 models:
- **Total disk space**: ~12 GB
- **Runtime memory**: Up to 18GB if all loaded simultaneously

If you encounter memory issues:
1. Use one model at a time
2. Restart Ollama between model switches
3. Consider using quantized models (e.g., `mistral:7b-q4`)

## Performance Benchmarks

Typical response times on MacBook Pro (16GB RAM):

- **First request** (cold start): 5-10 seconds
- **Subsequent requests** (model loaded): 2-5 seconds
- **Simple queries**: < 3 seconds
- **Complex analysis**: 5-15 seconds

## Next Steps After Testing

1. **Integration with E-commerce**: Test incident analysis with real production logs from the e-commerce microservices
2. **SRE Analytics Integration**: Feed SRE analytics reports to local LLMs for privacy-focused analysis
3. **Self Development**: Use CodeLlama for orchestrator codebase analysis
4. **Personal Tracker**: Generate AI reflections using local LLMs

## Documentation References

- Main README: `/Users/shiva/Projects/ai-orchestrator/README.md`
- Ollama Setup: `/Users/shiva/Projects/ai-orchestrator/LOCAL_LLM_SETUP.md`
- Self Development: `/Users/shiva/Projects/ai-orchestrator/FRONTEND_INTEGRATION_COMPLETE.md`
- Personal Tracker: `/Users/shiva/Projects/ai-orchestrator/PERSONAL_TRACKER_INTEGRATION.md`
