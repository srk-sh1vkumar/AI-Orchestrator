# AI Orchestrator - Architecture

## Overview

The AI Orchestrator is a sophisticated system that intelligently routes tasks to specialized LLM providers based on their strengths, with built-in fallback mechanisms, tool execution, and multi-LLM collaboration.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Request                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Server                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  POST /api/chat                                           │  │
│  │  GET  /api/health                                         │  │
│  │  GET  /api/providers                                      │  │
│  │  GET  /metrics (Prometheus)                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Orchestrator                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Task Router                                            │  │
│  │    - Pattern matching                                     │  │
│  │    - Intent classification                                │  │
│  │    - Provider selection                                   │  │
│  │                                                            │  │
│  │ 2. Quality Checker                                        │  │
│  │    - Response validation                                  │  │
│  │    - Confidence scoring                                   │  │
│  │    - Fallback triggering                                  │  │
│  │                                                            │  │
│  │ 3. Tool Manager                                           │  │
│  │    - Tool registration                                    │  │
│  │    - Function calling                                     │  │
│  │    - Result aggregation                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Providers                                 │
│  ┌──────────────┬──────────────┬──────────────┬─────────────┐  │
│  │ Claude Code  │   ChatGPT    │    Gemini    │   Claude    │  │
│  │              │              │              │             │  │
│  │ • Code Gen   │ • UI/UX      │ • Prompts    │ • Analysis  │  │
│  │ • DevOps     │ • Dashboards │ • Meta       │ • Reasoning │  │
│  │ • Deploy     │ • Workflows  │ • Optimize   │ • Docs      │  │
│  └──────────────┴──────────────┴──────────────┴─────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Local LLM (Ollama)                           │  │
│  │  • Incident Analysis (Primary)                            │  │
│  │  • Log Analysis                                           │  │
│  │  • Privacy-focused                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Tool Execution Layer                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐    │
│  │   GitHub    │   Docker    │ Kubernetes  │  Terminal   │    │
│  ├─────────────┼─────────────┼─────────────┼─────────────┤    │
│  │  Grafana    │ Prometheus  │     ELK     │   Splunk    │    │
│  ├─────────────┼─────────────┼─────────────┼─────────────┤    │
│  │  Jenkins    │ GH Actions  │ File System │ CloudWatch  │    │
│  └─────────────┴─────────────┴─────────────┴─────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Basic Request Flow

```
User: "Build a REST API for authentication"
  │
  ├─▶ Router analyzes intent
  │   └─▶ Matches "build", "api" → Claude Code
  │
  ├─▶ Claude Code generates response
  │   └─▶ May include tool calls (GitHub, Terminal)
  │
  ├─▶ Tool Manager executes tools
  │   └─▶ Creates repo, runs tests, etc.
  │
  └─▶ Quality check and response
      └─▶ Returns to user with execution details
```

### 2. Incident Analysis with Fallback

```
User: "Analyze this production incident"
  │
  ├─▶ Router classifies as INCIDENT_ANALYSIS
  │   └─▶ Primary: Local LLM, Fallback: Claude → Gemini
  │
  ├─▶ Try Local LLM
  │   ├─▶ Success? → Quality check
  │   │   └─▶ Pass? → Return response
  │   └─▶ Fail? → Fallback to Claude
  │
  ├─▶ Try Claude (fallback #1)
  │   ├─▶ Success? → Quality check
  │   │   └─▶ Pass? → Return response
  │   └─▶ Fail? → Fallback to Gemini
  │
  └─▶ Try Gemini (fallback #2)
      └─▶ Return response (final attempt)
```

### 3. Multi-LLM Collaboration

```
User: "Build a complete monitoring dashboard with deployment"
  │
  ├─▶ Router detects collaboration pattern
  │   └─▶ Plan: Gemini → ChatGPT → Claude Code
  │
  ├─▶ Step 1: Gemini
  │   └─▶ Optimizes requirements and creates detailed specs
  │
  ├─▶ Step 2: ChatGPT
  │   └─▶ Uses Gemini's output to design UI/UX
  │
  ├─▶ Step 3: Claude Code
  │   └─▶ Uses ChatGPT's output to implement and deploy
  │   └─▶ Executes tools: Docker, Kubernetes, GitHub
  │
  └─▶ Aggregated response with all steps
```

## Component Details

### Task Router

**Responsibility:** Intelligent routing based on intent analysis

**Key Features:**
- Pattern-based matching with confidence scores
- Task category classification (12 categories)
- Collaboration detection
- Explicit provider override support
- Fallback chain determination

**Routing Patterns:**
```python
{
    "build|code|implement" → Claude Code (0.9 confidence)
    "ui|dashboard|interface" → ChatGPT (0.9 confidence)
    "optimize prompt" → Gemini (0.95 confidence)
    "analyze incident" → Local LLM (0.95 confidence)
}
```

### Provider Manager

**Responsibility:** Manage LLM provider connections and health

**Providers:**
1. **Claude Code** (Anthropic)
   - Model: claude-3-5-sonnet-20241022
   - Role: Code, DevOps, Deployment
   - Tools: All

2. **ChatGPT** (OpenAI)
   - Model: gpt-4-turbo-preview
   - Role: UI/UX, Workflows
   - Tools: GitHub, File System

3. **Gemini** (Google)
   - Model: gemini-pro
   - Role: Prompt optimization
   - Tools: Limited

4. **Claude** (Anthropic)
   - Model: claude-3-5-sonnet-20241022
   - Role: Analysis fallback
   - Tools: Monitoring, Logs

5. **Local LLM** (Ollama)
   - Model: Configurable (llama2:13b default)
   - Role: Primary incident analysis
   - Tools: None (privacy-focused)

### Tool Manager

**Responsibility:** Execute operations across integrated systems

**Tool Categories:**
- **Version Control:** GitHub API
- **Container Orchestration:** Docker, Kubernetes
- **CI/CD:** Jenkins, GitHub Actions
- **Monitoring:** Grafana, Prometheus
- **Logging:** Elasticsearch, Splunk, CloudWatch
- **System:** Terminal, File System

**Tool Execution Flow:**
```
LLM Response with tool_calls
  ↓
Tool Manager receives calls
  ↓
Execute tools in sequence/parallel
  ↓
Aggregate results
  ↓
Return to LLM for final response
```

### Quality Checker

**Responsibility:** Validate response quality and trigger fallbacks

**Checks:**
- Minimum content length
- Failure pattern detection
- Confidence scoring
- Empty/placeholder detection

**Scoring:**
```python
score = 1.0
- 0.3 if too_short
- 0.2 if contains("error")
- 0.2 if contains("cannot")
- 0.1 if contains("apologize")

pass = score >= 0.7 and no_issues
```

## Fallback Logic

### Fallback Chain by Category

| Category | Primary | Fallback #1 | Fallback #2 |
|----------|---------|-------------|-------------|
| Incident Analysis | Local LLM | Claude | Gemini |
| Log Analysis | Local LLM | Claude | Gemini |
| Code Generation | Claude Code | Claude | - |
| UI Generation | ChatGPT | Claude | - |
| Deployment | Claude Code | Claude | - |

### Fallback Triggers

1. **Provider Unavailable:** Connection error, timeout
2. **Quality Check Failed:** Low confidence score
3. **Empty Response:** No meaningful content
4. **API Error:** Rate limit, authentication failure

### Fallback Logging

All fallback events are logged with:
- Timestamp
- From/To providers
- Reason for fallback
- Task category
- Success of fallback attempt

## Collaboration Patterns

### Pattern 1: Full Application Build

```
User: "Build a complete dashboard application"

Flow:
1. Gemini: Create optimal prompt for requirements
2. ChatGPT: Design UI components and layout
3. Claude Code: Implement backend and frontend
4. Claude Code: Deploy using Docker/K8s tools
```

### Pattern 2: Incident Analysis + Fix

```
User: "Analyze incident and create fixes"

Flow:
1. Local LLM: Analyze logs and metrics
2. Local LLM: Identify root cause
3. Claude Code: Generate fix code
4. Claude Code: Deploy fix
```

### Pattern 3: Analysis + Report

```
User: "Analyze outage and create report"

Flow:
1. Local LLM: Analyze incident data
2. ChatGPT: Format as dashboard/report
```

## Monitoring & Observability

### Metrics Collected

**Request Metrics:**
- `orchestrator_requests_total` - Counter by provider/category/status
- `orchestrator_request_duration_seconds` - Histogram by provider

**Fallback Metrics:**
- `orchestrator_fallbacks_total` - Counter by from/to provider

**Tool Metrics:**
- Tool execution count
- Tool execution duration
- Tool success/failure rates

### Logging

Structured JSON logging with:
- Timestamp
- Log level
- Component
- Event type
- Contextual data

### Health Checks

- Provider connectivity
- Tool availability
- System resources
- API rate limits

## Security Considerations

### API Keys
- Stored in environment variables
- Never logged or exposed
- Validated on startup

### Local LLM Benefits
- Sensitive data stays local
- No external API calls
- GDPR/compliance friendly
- Cost-free analysis

### Tool Execution
- Sandboxed when possible
- Permission checks
- Audit logging
- Rate limiting

## Performance

### Optimization Strategies

1. **Async Operations:** All I/O is async
2. **Parallel Tool Execution:** Independent tools run concurrently
3. **Caching:** Redis for session/response caching
4. **Connection Pooling:** Reuse HTTP connections
5. **Quality Gating:** Fast failure detection

### Expected Latencies

| Operation | Typical Latency |
|-----------|----------------|
| Simple request | 2-5s |
| With tool execution | 5-15s |
| Collaboration (3 LLMs) | 15-30s |
| With fallback | +3-5s per fallback |

## Extensibility

### Adding New Providers

1. Create provider class extending `BaseLLMProvider`
2. Implement `complete()` and `health_check()`
3. Add to `Orchestrator.__init_providers()`
4. Update routing patterns

### Adding New Tools

1. Create tool class extending `BaseTool`
2. Implement `execute()` and `get_definitions()`
3. Add to `ToolManager.__init_tools()`
4. Update provider tool access

### Custom Routing Rules

Edit `src/core/routing.py`:
- Add patterns to `ROUTING_PATTERNS`
- Add categories to `CATEGORY_PATTERNS`
- Add collaboration patterns to `COLLABORATION_PATTERNS`

## Future Enhancements

1. **Streaming Responses:** SSE for real-time updates
2. **Response Caching:** Cache similar requests
3. **Cost Tracking:** Per-provider cost monitoring
4. **A/B Testing:** Compare provider performance
5. **Custom Models:** Support for fine-tuned models
6. **Multi-tenancy:** Support multiple users/teams
7. **Workflow Templates:** Predefined collaboration patterns
8. **Auto-scaling:** Dynamic provider selection based on load
