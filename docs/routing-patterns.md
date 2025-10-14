# AI Orchestrator - Routing Patterns Reference

## Overview

This document provides a comprehensive reference for how the AI Orchestrator routes tasks to different LLM providers based on patterns in the user's request.

---

## Provider Routing Rules

### 1. Claude Code (Primary Executor & DevOps)

**Confidence Score**: 0.85 - 0.9

**Triggers**:
```regex
\b(build|code|implement|debug|refactor|deploy|docker|kubernetes|k8s)\b
\b(fix|bug|error|issue|problem)\b
\b(create|write|generate).*\b(function|class|api|service|script)\b
\b(ci/cd|pipeline|devops|automation)\b
\b(test|unit test|integration test)\b
```

**Example Requests**:
- "Build a REST API for user authentication"
- "Deploy this application to Kubernetes"
- "Fix the bug in the payment service"
- "Create a CI/CD pipeline for the project"
- "Implement unit tests for the auth module"
- "Refactor the database connection code"
- "Debug the performance issue in production"

**Use Cases**:
- Code generation and implementation
- Bug fixing and debugging
- Deployment and DevOps tasks
- CI/CD pipeline creation
- Testing and quality assurance
- Infrastructure as code
- Docker and Kubernetes operations

**Tools Available**:
- ✅ GitHub (repos, PRs, issues)
- ✅ Docker (build, run, manage)
- ✅ Kubernetes (deploy, scale)
- ✅ Terminal (shell commands)
- ✅ File System (read/write)

**Fallback Chain**: Claude

---

### 2. ChatGPT (Interface & Workflow Layer)

**Confidence Score**: 0.75 - 0.9

**Triggers**:
```regex
\b(ui|interface|dashboard|frontend|user experience|ux)\b
\b(automate workflow|workflow automation)\b
\b(design|layout|component|widget)\b
\b(report|document|presentation).*\b(format|create|generate)\b
```

**Example Requests**:
- "Create a dashboard for monitoring system metrics"
- "Design a user interface for the admin panel"
- "Build a workflow automation for customer onboarding"
- "Generate a report showing quarterly performance"
- "Create interactive components for the web app"
- "Design the layout for a mobile application"
- "Format the incident report as a presentation"

**Use Cases**:
- UI/UX design and implementation
- Dashboard creation
- Workflow automation
- Report and document generation
- Frontend development
- Interactive component creation
- User experience optimization

**Tools Available**:
- ✅ GitHub (for UI code)
- ✅ File System
- ✅ Terminal

**Fallback Chain**: Claude

---

### 3. Gemini (Meta-Prompting Layer)

**Confidence Score**: 0.85 - 0.95

**Triggers**:
```regex
\b(optimize prompt|improve instruction|better prompt)\b
\b(meta-prompt|prompt template|prompt engineering)\b
\b(refine|enhance).*\b(prompt|instruction)\b
```

**Example Requests**:
- "Optimize this prompt for better results"
- "Create a prompt template for code reviews"
- "Improve the instruction for the AI assistant"
- "Refine this prompt to be more specific"
- "How can I make this prompt more effective?"
- "Design a meta-prompt for generating documentation"
- "Enhance the prompt engineering for this task"

**Use Cases**:
- Prompt optimization
- Meta-prompting and prompt templates
- Instruction refinement
- Prompt engineering best practices
- Creating effective AI instructions
- Analyzing prompt effectiveness

**Tools Available**:
- Limited (focus on prompt work)

**Fallback Chain**: Claude, ChatGPT

---

### 4. Local LLM (Privacy & Analysis Layer - PRIMARY for Incidents)

**Confidence Score**: 0.85 - 0.95

**Triggers**:
```regex
\b(analyze|investigate|triage).*\b(incident|event|outage|failure)\b
\b(analyze|parse|examine).*\b(log|logs|logging)\b
\b(root cause|postmortem|what happened|why did)\b
\b(security.*incident|breach|vulnerability.*analysis)\b
\b(performance.*degradation|slow|latency.*issue)\b
```

**Example Requests**:
- "Analyze this production incident"
- "Investigate why the service went down"
- "Parse these logs and find the root cause"
- "What happened during the outage last night?"
- "Analyze this security incident"
- "Investigate the performance degradation"
- "Create a postmortem for the database failure"
- "Triage this event and identify contributing factors"

**Use Cases**:
- **Incident analysis (PRIMARY)**
- Log analysis and parsing
- Root cause investigation
- Security incident analysis
- Performance issue diagnosis
- Postmortem creation
- Event triage
- Privacy-sensitive analysis

**Tools Available**:
- None (privacy-focused, stays local)
- Can access logs via orchestrator

**Fallback Chain**: Claude → Gemini

**Special Features**:
- ✅ **Privacy-first**: Data stays local
- ✅ **Cost-free**: No API charges
- ✅ **GDPR-compliant**: Sensitive data doesn't leave
- ✅ **Offline capable**: Works without internet

---

### 5. Claude (Reasoning & Analysis Fallback)

**Confidence Score**: 0.6 - 0.8 (as fallback)

**Triggers**:
- Fallback from Local LLM (incident analysis)
- Fallback from other providers
- Complex reasoning tasks
- Documentation requests

**Example Requests**:
- "Explain how this architecture works"
- "Document the API endpoints"
- "Analyze the trade-offs between these approaches"
- Used automatically when Local LLM fails

**Use Cases**:
- Incident analysis (as fallback #1 from Local LLM)
- Complex reasoning and analysis
- Technical documentation
- Deep analytical thinking
- Event correlation

**Tools Available**:
- ✅ Monitoring tools
- ✅ Log systems
- ✅ Terminal

**Fallback Chain**: Gemini (as final fallback for analysis)

---

## Explicit Provider Override

Users can explicitly select a provider using the `@provider:` syntax:

```bash
@claude-code: <your request>
@chatgpt: <your request>
@gemini: <your request>
@claude: <your request>
@local: <your request>
```

**Examples**:
```bash
# Force ChatGPT even for code task
@chatgpt: Build a REST API

# Use local LLM for general questions
@local: Explain how authentication works

# Use Gemini for non-prompt tasks
@gemini: Create a user interface
```

**Behavior**:
- Sets confidence to 1.0 (100%)
- Bypasses pattern matching
- Still uses fallback chain if provider fails
- Useful for testing or specific preferences

---

## Collaboration Patterns

The orchestrator automatically detects requests that benefit from multiple LLMs working together.

### Pattern 1: Full Application Build

**Trigger**:
```regex
\b(build|create).*\b(complete|full|entire).*\b(dashboard|application|system)\b
```

**Example**: "Build a complete monitoring dashboard"

**Collaboration Plan**:
1. **Gemini**: Optimize requirements and specifications
2. **ChatGPT**: Design UI/UX and layout
3. **Claude Code**: Implement code and deploy

**Why Collaboration?**:
- Complex multi-phase task
- Each LLM excels at different parts
- Better overall quality

---

### Pattern 2: Incident Analysis + Fix

**Trigger**:
```regex
\b(analyze.*incident|outage).*\b(and|then).*\b(fix|create|write)\b
```

**Example**: "Analyze this incident and create fixes"

**Collaboration Plan**:
1. **Local LLM**: Analyze logs and identify root cause
2. **Claude Code**: Generate and deploy fixes

**Why Collaboration?**:
- Combines analysis with implementation
- Leverages local LLM for privacy
- Claude Code for deployment

---

### Pattern 3: Analysis + Report

**Trigger**:
```regex
\b(analyze.*incident|outage).*\b(report|document)\b
```

**Example**: "Analyze outage and create incident report"

**Collaboration Plan**:
1. **Local LLM**: Perform deep analysis
2. **ChatGPT**: Format as professional report/dashboard

**Why Collaboration?**:
- Technical analysis + presentation
- Better formatting and visualization

---

## Routing Priority

When multiple patterns match, the orchestrator uses this priority:

1. **Explicit Provider** (`@provider:`) - Confidence: 1.0
2. **Collaboration Pattern** - Confidence: 0.95
3. **Incident Analysis** (Local LLM) - Confidence: 0.95
4. **Prompt Optimization** (Gemini) - Confidence: 0.95
5. **Code/DevOps** (Claude Code) - Confidence: 0.9
6. **UI/UX** (ChatGPT) - Confidence: 0.9
7. **Default** (Claude Code) - Confidence: 0.6

---

## Fallback Chains by Category

| Category | Primary | Fallback #1 | Fallback #2 |
|----------|---------|-------------|-------------|
| **Incident Analysis** | Local LLM | Claude | Gemini |
| **Log Analysis** | Local LLM | Claude | Gemini |
| **Technical Analysis** | Local LLM | Claude | Gemini |
| **Code Generation** | Claude Code | Claude | - |
| **Code Implementation** | Claude Code | Claude | - |
| **Debugging** | Claude Code | Claude | - |
| **Deployment** | Claude Code | Claude | - |
| **UI Generation** | ChatGPT | Claude | - |
| **Workflow Automation** | ChatGPT | Claude | - |
| **Prompt Optimization** | Gemini | Claude | ChatGPT |
| **Documentation** | Claude | Gemini | - |
| **General** | Claude Code | Claude | - |

---

## Routing Examples

### Example 1: Simple Code Request

**Input**: "Build a REST API"

**Routing Process**:
1. Extract patterns: "build", "api"
2. Match: Claude Code (0.9 confidence)
3. Category: CODE_GENERATION
4. Fallback: [Claude]
5. Collaboration: No

**Result**: Route to Claude Code

---

### Example 2: Incident Analysis

**Input**: "Analyze this production outage"

**Routing Process**:
1. Extract patterns: "analyze", "outage"
2. Match: Local LLM (0.95 confidence)
3. Category: INCIDENT_ANALYSIS
4. Fallback: [Local LLM, Claude, Gemini]
5. Collaboration: No

**Result**: Route to Local LLM (with fallback chain)

---

### Example 3: Collaboration Detected

**Input**: "Build a complete dashboard with deployment"

**Routing Process**:
1. Extract patterns: "build", "complete", "dashboard", "deployment"
2. Match: Collaboration pattern
3. Plan: [Gemini, ChatGPT, Claude Code]
4. Category: UI_GENERATION + DEPLOYMENT
5. Confidence: 0.95

**Result**: Multi-LLM collaboration

---

### Example 4: Explicit Override

**Input**: "@chatgpt: Write some backend code"

**Routing Process**:
1. Detect explicit: ChatGPT
2. Remove prefix: "Write some backend code"
3. Confidence: 1.0 (forced)
4. Category: CODE_GENERATION
5. Fallback: [Claude]

**Result**: Route to ChatGPT (even though Claude Code would normally handle)

---

## Quality Check Impact on Routing

After a provider responds, the quality checker validates:

1. **Minimum length** (default: 50 chars)
2. **Failure patterns** (errors, apologies, refusals)
3. **Confidence score** (default threshold: 0.7)

If quality check **fails**:
- Trigger fallback to next provider in chain
- Log fallback event
- Retry with fallback provider

If **all providers fail**:
- Return last attempt's response
- Include all fallback events in response
- Log error for monitoring

---

## Customizing Routing

To customize routing patterns, edit `src/core/routing.py`:

### Add New Pattern

```python
ROUTING_PATTERNS = {
    LLMProvider.YOUR_PROVIDER: [
        (r"\b(your|custom|pattern)\b", 0.9),
        (r"\b(another|pattern)\b", 0.85),
    ],
}
```

### Add New Category

```python
class TaskCategory(str, Enum):
    YOUR_CATEGORY = "your_category"

CATEGORY_PATTERNS = {
    TaskCategory.YOUR_CATEGORY: [
        r"\b(matching|pattern)\b"
    ],
}
```

### Add Collaboration Pattern

```python
COLLABORATION_PATTERNS = {
    r"\b(your|collaboration|trigger)\b": [
        LLMProvider.FIRST,
        LLMProvider.SECOND,
        LLMProvider.THIRD,
    ],
}
```

---

## Performance Considerations

### Routing Performance
- **Pattern matching**: < 10ms
- **Category classification**: < 5ms
- **Collaboration detection**: < 15ms
- **Total routing overhead**: ~30ms

### Provider Latencies
- **Local LLM**: 2-10s (model dependent)
- **Claude Code**: 3-8s
- **ChatGPT**: 2-6s
- **Gemini**: 2-5s
- **Claude**: 3-8s

### Fallback Overhead
- **Per fallback**: +3-5s
- **Quality check**: ~5ms

---

## Best Practices

### For Users

1. **Be specific**: "Build a REST API" is better than "Make something"
2. **Use keywords**: Include action words (build, analyze, create, deploy)
3. **Override when needed**: Use `@provider:` if you have a preference
4. **Trust the router**: It's optimized for best results

### For Developers

1. **Test patterns**: Use `test_routing.py` to verify patterns
2. **Monitor metrics**: Check Prometheus for routing decisions
3. **Adjust weights**: Fine-tune confidence scores based on results
4. **Add patterns**: Extend routing for your use cases

---

## Monitoring Routing Decisions

### Prometheus Metrics

```prometheus
# Total requests by provider and category
orchestrator_requests_total{provider="claude_code", category="code_generation"}

# Fallback occurrences
orchestrator_fallbacks_total{from_provider="local", to_provider="claude"}
```

### Logs

All routing decisions are logged:
```json
{
  "event": "routing_decision",
  "provider": "claude_code",
  "category": "code_generation",
  "confidence": 0.9,
  "fallback_chain": ["claude"],
  "timestamp": "2025-10-12T10:30:00Z"
}
```

---

## Troubleshooting

### Problem: Wrong provider selected

**Solution**:
- Check if request matches unexpected patterns
- Use explicit override: `@provider:`
- Adjust pattern weights in routing.py

### Problem: No collaboration when expected

**Solution**:
- Verify request matches collaboration patterns
- Ensure `enable_collaboration=true` in request
- Check logs for collaboration detection

### Problem: Too many fallbacks

**Solution**:
- Check provider health: `GET /api/health`
- Verify API keys are configured
- Review quality check thresholds

---

**Last Updated**: 2025-10-12
**Version**: 1.0.0
