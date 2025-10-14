# AI Orchestrator - API Reference

Complete API reference for the AI Orchestrator REST API.

---

## Base URL

```
http://localhost:8000
```

Or when deployed:
```
https://your-domain.com
```

---

## Authentication

Currently, the API does not require authentication. For production deployment, consider adding:
- API keys
- OAuth2
- JWT tokens

---

## Endpoints

### 1. Chat Completion

Send a message to the orchestrator for intelligent routing and execution.

**Endpoint**: `POST /api/chat`

**Request Body**:
```json
{
  "message": "string (required)",
  "context": "object (optional)",
  "explicit_provider": "string (optional)",
  "session_id": "string (optional)",
  "enable_tools": "boolean (optional, default: true)",
  "enable_collaboration": "boolean (optional, default: true)"
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | The user's request or question |
| `context` | object | No | Additional context (e.g., logs, metrics) |
| `explicit_provider` | string | No | Force specific provider: `claude_code`, `chatgpt`, `gemini`, `claude`, `local` |
| `session_id` | string | No | Session identifier for conversation context |
| `enable_tools` | boolean | No | Allow tool execution (default: true) |
| `enable_collaboration` | boolean | No | Allow multi-LLM collaboration (default: true) |

**Response**: `200 OK`
```json
{
  "message": "string",
  "provider": "string",
  "routing_decision": {
    "provider": "string",
    "category": "string",
    "confidence": "number",
    "reasoning": "string",
    "fallback_providers": ["string"],
    "requires_collaboration": "boolean",
    "collaboration_plan": ["string"] | null
  },
  "tool_results": [
    {
      "tool_type": "string",
      "operation": "string",
      "success": "boolean",
      "result": "any",
      "error": "string | null",
      "execution_time": "number",
      "timestamp": "string"
    }
  ],
  "fallback_events": [
    {
      "from_provider": "string",
      "to_provider": "string",
      "reason": "string",
      "category": "string",
      "timestamp": "string"
    }
  ],
  "quality_check": {
    "passed": "boolean",
    "score": "number",
    "issues": ["string"],
    "metadata": "object"
  } | null,
  "collaboration_steps": [
    {
      "step": "number",
      "provider": "string",
      "response": "string",
      "tool_calls": "number",
      "tool_results": "number",
      "execution_time": "number"
    }
  ] | null,
  "execution_time": "number",
  "timestamp": "string"
}
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Build a REST API for user authentication",
    "enable_tools": true
  }'
```

**Example Response**:
```json
{
  "message": "I've created a REST API for user authentication with JWT tokens...",
  "provider": "claude_code",
  "routing_decision": {
    "provider": "claude_code",
    "category": "code_generation",
    "confidence": 0.9,
    "reasoning": "Pattern-based routing with 90% confidence",
    "fallback_providers": ["claude"],
    "requires_collaboration": false,
    "collaboration_plan": null
  },
  "tool_results": [
    {
      "tool_type": "github",
      "operation": "create_repository",
      "success": true,
      "result": {"url": "https://github.com/user/auth-api"},
      "error": null,
      "execution_time": 1.2,
      "timestamp": "2025-10-12T10:30:00Z"
    }
  ],
  "fallback_events": [],
  "quality_check": {
    "passed": true,
    "score": 0.95,
    "issues": [],
    "metadata": {"provider": "claude_code", "content_length": 1247}
  },
  "collaboration_steps": null,
  "execution_time": 8.5,
  "timestamp": "2025-10-12T10:30:00Z"
}
```

**Error Responses**:

`400 Bad Request`:
```json
{
  "detail": "Invalid request format"
}
```

`500 Internal Server Error`:
```json
{
  "detail": "All providers failed. Last error: ..."
}
```

---

### 2. Health Check

Check the health status of the orchestrator and all providers.

**Endpoint**: `GET /api/health`

**Response**: `200 OK`
```json
{
  "status": "string",
  "providers": {
    "claude_code": "boolean",
    "chatgpt": "boolean",
    "gemini": "boolean",
    "claude": "boolean",
    "local": "boolean"
  },
  "tools": {
    "github": "boolean",
    "docker": "boolean",
    "kubernetes": "boolean",
    "terminal": "boolean",
    "file_system": "boolean"
  },
  "timestamp": "string"
}
```

**Status Values**:
- `"healthy"` - All providers available
- `"degraded"` - Some providers unavailable
- `"unhealthy"` - No providers available

**Example Request**:
```bash
curl http://localhost:8000/api/health
```

**Example Response**:
```json
{
  "status": "healthy",
  "providers": {
    "claude_code": true,
    "chatgpt": true,
    "gemini": true,
    "claude": true,
    "local": true
  },
  "tools": {
    "github": true,
    "docker": true,
    "kubernetes": false,
    "terminal": true,
    "file_system": true
  },
  "timestamp": "2025-10-12T10:30:00Z"
}
```

---

### 3. List Providers

Get information about available LLM providers and their configuration status.

**Endpoint**: `GET /api/providers`

**Response**: `200 OK`
```json
{
  "providers": {
    "provider_name": {
      "configured": "boolean",
      "role": "string",
      "model": "string | null"
    }
  }
}
```

**Example Request**:
```bash
curl http://localhost:8000/api/providers
```

**Example Response**:
```json
{
  "providers": {
    "claude_code": {
      "configured": true,
      "role": "Code generation, DevOps, deployment"
    },
    "chatgpt": {
      "configured": true,
      "role": "UI/UX, workflow automation"
    },
    "gemini": {
      "configured": true,
      "role": "Prompt optimization, meta-prompting"
    },
    "claude": {
      "configured": true,
      "role": "Incident analysis (fallback), reasoning"
    },
    "local": {
      "configured": true,
      "role": "Incident analysis (primary), privacy-focused",
      "model": "llama2:13b"
    }
  }
}
```

---

### 4. Prometheus Metrics

Get metrics for monitoring and observability.

**Endpoint**: `GET /metrics`

**Response**: `200 OK` (Prometheus format)

**Available Metrics**:

```prometheus
# Total requests by provider, category, and status
orchestrator_requests_total{provider="claude_code", category="code_generation", status="success"} 42

# Request duration histogram
orchestrator_request_duration_seconds_bucket{provider="claude_code", le="5.0"} 35
orchestrator_request_duration_seconds_sum{provider="claude_code"} 142.5
orchestrator_request_duration_seconds_count{provider="claude_code"} 42

# Fallback occurrences
orchestrator_fallbacks_total{from_provider="local", to_provider="claude"} 3
```

**Example Request**:
```bash
curl http://localhost:8000/metrics
```

---

### 5. API Documentation

Interactive API documentation is available at:

**Swagger UI**: `GET /docs`
```
http://localhost:8000/docs
```

**ReDoc**: `GET /redoc`
```
http://localhost:8000/redoc
```

**OpenAPI Schema**: `GET /openapi.json`
```
http://localhost:8000/openapi.json
```

---

## Request Examples

### Basic Code Generation

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a Python function to validate email addresses"
  }'
```

### Incident Analysis with Context

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this production incident",
    "context": {
      "logs": [
        "ERROR: Database connection timeout",
        "ERROR: Connection pool exhausted"
      ],
      "metrics": {
        "error_rate": 0.35,
        "response_time_ms": 5000,
        "cpu_usage": 0.95
      },
      "timestamp": "2025-10-12T14:30:00Z"
    }
  }'
```

### Explicit Provider Selection

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@chatgpt: Create a dashboard layout",
    "enable_tools": true
  }'
```

### Multi-LLM Collaboration

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Build a complete monitoring dashboard with deployment",
    "enable_collaboration": true,
    "enable_tools": true
  }'
```

### Without Tool Execution

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain how to deploy to Kubernetes",
    "enable_tools": false
  }'
```

---

## Python Client Example

```python
import httpx
import asyncio

async def chat_with_orchestrator():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={
                "message": "Build a REST API for authentication",
                "enable_tools": True,
                "enable_collaboration": False
            },
            timeout=120.0
        )

        if response.status_code == 200:
            data = response.json()
            print(f"Provider: {data['provider']}")
            print(f"Response: {data['message']}")
            print(f"Tools executed: {len(data['tool_results'])}")
            print(f"Execution time: {data['execution_time']:.2f}s")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

asyncio.run(chat_with_orchestrator())
```

---

## JavaScript Client Example

```javascript
async function chatWithOrchestrator() {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: 'Create a user dashboard',
      enable_tools: true,
      enable_collaboration: false
    })
  });

  const data = await response.json();

  console.log(`Provider: ${data.provider}`);
  console.log(`Response: ${data.message}`);
  console.log(`Tools executed: ${data.tool_results.length}`);
  console.log(`Execution time: ${data.execution_time}s`);
}

chatWithOrchestrator();
```

---

## Rate Limits

Currently no rate limiting is implemented. For production:
- Consider adding rate limiting middleware
- Use Redis for distributed rate limiting
- Set limits per API key or IP

**Recommended Limits**:
- 100 requests per minute per IP
- 1000 requests per hour per user

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 404 | Endpoint not found |
| 500 | Internal Server Error (provider failure, etc.) |
| 503 | Service Unavailable (all providers down) |

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

---

## Webhooks (Future)

Webhooks for long-running operations are planned for future releases:

```json
{
  "message": "Long running task...",
  "webhook_url": "https://your-app.com/webhook",
  "webhook_secret": "your_secret_key"
}
```

---

## WebSocket Support (Future)

Real-time streaming responses planned for future releases:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');
ws.send(JSON.stringify({message: "Build an API"}));
ws.onmessage = (event) => {
  console.log(event.data);
};
```

---

## CORS Configuration

CORS is enabled for all origins in development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, restrict to specific origins:

```python
allow_origins=["https://your-frontend.com"]
```

---

## Timeouts

- **Request timeout**: 120 seconds (default)
- **Provider timeout**: Varies by provider
- **Tool execution timeout**: 30 seconds per tool

Configure in `.env`:
```bash
REQUEST_TIMEOUT=120
PROVIDER_TIMEOUT=60
TOOL_TIMEOUT=30
```

---

## Best Practices

1. **Use explicit providers sparingly**: Let the router choose for best results
2. **Provide context**: Include relevant logs, metrics for incident analysis
3. **Handle timeouts**: Set appropriate timeouts for long operations
4. **Check health**: Monitor `/api/health` for provider availability
5. **Enable tools selectively**: Disable when not needed for faster responses
6. **Use session_id**: For multi-turn conversations (future feature)

---

**Last Updated**: 2025-10-12
**Version**: 1.0.0
