# AI Orchestrator - Architecture Diagrams

This document contains all architecture diagrams for the AI Orchestrator system.

## 📋 Available Diagrams

1. **System Architecture** - Overall system structure
2. **Request Flow** - Complete request processing flow
3. **Fallback Chain** - Fallback mechanism for high availability
4. **Collaboration Flow** - Multi-LLM collaboration
5. **Routing Decision Tree** - Task routing logic
6. **Deployment Architecture** - Docker/Kubernetes deployment

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER LAYER                                 │
│  ┌──────────────────┐         ┌─────────────────────────────────┐  │
│  │  👤 User         │         │  🖥️  CLI Interface              │  │
│  │  - Developers    │────────▶│  - Interactive mode              │  │
│  │  - SREs          │         │  - One-shot commands             │  │
│  │  - DevOps        │         │  - Rich terminal UI              │  │
│  └──────────────────┘         └─────────────────────────────────┘  │
│           │                              │                           │
│           └──────────────┬───────────────┘                           │
└──────────────────────────┼─────────────────────────────────────────┘
                           │
┌──────────────────────────┼─────────────────────────────────────────┐
│                    API GATEWAY LAYER                                 │
│                           │                                          │
│  ┌────────────────────────▼───────────────────────────────────┐    │
│  │              ⚡ FastAPI Server (Port 8000)                  │    │
│  │  ┌─────────────┬──────────────┬────────────┬────────────┐  │    │
│  │  │ POST        │ GET          │ GET        │ GET        │  │    │
│  │  │ /api/chat   │ /api/health  │ /api/      │ /metrics   │  │    │
│  │  │             │              │ providers  │ (Prom)     │  │    │
│  │  └─────────────┴──────────────┴────────────┴────────────┘  │    │
│  └──────────────────────────────────────────────────────────┘      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────────┐
│              CORE ORCHESTRATION LAYER                                │
│                           │                                          │
│  ┌────────────────────────▼───────────────────────────────────┐    │
│  │                  🎯 ORCHESTRATOR                            │    │
│  │                  (Main Engine)                              │    │
│  └─┬───────────────────┬──────────────────┬──────────────────┘    │
│    │                   │                  │                        │
│  ┌─▼─────────────┐  ┌─▼────────────┐  ┌─▼──────────────────┐    │
│  │ 🧭 Router     │  │ ✅ Quality    │  │ 🛠️  Tool Manager   │    │
│  │ - Pattern     │  │ - Validation  │  │ - Tool registry    │    │
│  │   matching    │  │ - Scoring     │  │ - Execution        │    │
│  │ - Task        │  │ - Fallback    │  │ - Result           │    │
│  │   classification│  │   trigger    │  │   aggregation     │    │
│  └───────┬───────┘  └──────────────┘  └─────────┬──────────┘    │
└──────────┼──────────────────────────────────────┼────────────────┘
           │                                       │
┌──────────┼───────────────────────────────────────┼────────────────┐
│        LLM PROVIDER LAYER                        │                 │
│           │                                       │                 │
│  ┌────────▼──────────┬────────────┬─────────────┬────────────┐   │
│  │                   │            │             │            │   │
│  │ 🤖 Claude Code    │ 💬 ChatGPT │ ✨ Gemini   │ 🧠 Claude  │   │
│  │ Sonnet 3.5        │ GPT-4      │ Gemini Pro  │ Sonnet 3.5 │   │
│  │ ─────────────     │ ──────────  │ ──────────  │ ────────── │   │
│  │ • Code gen        │ • UI/UX    │ • Prompts   │ • Analysis │   │
│  │ • DevOps          │ • Dashboard│ • Optimize  │ • Reasoning│   │
│  │ • Deploy          │ • Workflow │ • Meta      │ • Fallback │   │
│  │ • CI/CD           │ • Reports  │             │            │   │
│  └───────────────────┴────────────┴─────────────┴────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │          🏠 Local LLM (Ollama) - Primary for Analysis     │    │
│  │          • Incident analysis    • Privacy-focused         │    │
│  │          • Log analysis         • Cost-free               │    │
│  │          • Security incidents   • Offline capable         │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│  Fallback Chain (Analysis): Local LLM → Claude → Gemini          │
└──────────────────────────┬────────────────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────────────────┐
│              TOOL EXECUTION LAYER                                  │
│                           │                                        │
│  ┌────────────────────────▼─────────────────────────────────┐    │
│  │                   🛠️  Tool Manager                        │    │
│  └─┬──────────┬──────────┬──────────┬──────────┬──────────┬─┘    │
│    │          │          │          │          │          │       │
│  ┌─▼────┐  ┌─▼─────┐  ┌─▼─────┐  ┌─▼─────┐  ┌─▼─────┐  ┌─▼────┐ │
│  │📦 Git│  │🐳 Doc │  │☸️  K8s │  │💻 Term│  │📁 File│  │📊 Mon│ │
│  │Hub   │  │ker   │  │       │  │inal  │  │System│  │itor  │ │
│  │      │  │      │  │       │  │      │  │      │  │      │ │
│  │Repos │  │Build │  │Deploy │  │Shell │  │Read  │  │Metrics│ │
│  │PRs   │  │Run   │  │Scale  │  │Exec  │  │Write │  │Logs  │ │
│  │Issues│  │Manage│  │Pods   │  │      │  │      │  │Alerts│ │
│  └──────┘  └──────┘  └───────┘  └──────┘  └──────┘  └──────┘ │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                              │
│  ┌────────────┬───────────────┬────────────────┬──────────────┐   │
│  │ 🗄️  Redis  │ 🦙 Ollama     │ 📊 Prometheus  │ 📈 Grafana   │   │
│  │ Cache      │ Local Models  │ Metrics Store  │ Dashboards   │   │
│  │ Sessions   │ llama2:13b    │ Time Series    │ Alerts       │   │
│  └────────────┴───────────────┴────────────────┴──────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. Request Flow

### Basic Code Generation Request

```
┌─────────┐
│  User   │ "Build a REST API for user authentication"
└────┬────┘
     │
     ▼
┌─────────────────┐
│  FastAPI Server │ POST /api/chat
└────┬────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Orchestrator: process_request()                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 1. Task Router                                    │ │
│  │    - Analyze: "build", "REST API"                │ │
│  │    - Category: CODE_GENERATION                   │ │
│  │    - Provider: Claude Code (0.9 confidence)      │ │
│  │    - Fallback: [Claude]                          │ │
│  └──────────────────────────────────────────────────┘ │
└────┬───────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Claude Code Provider                                  │
│  ┌──────────────────────────────────────────────────┐ │
│  │ - Generate authentication API code                │ │
│  │ - Include tool calls:                             │ │
│  │   • create_github_repo()                          │ │
│  │   • build_docker_image()                          │ │
│  │   • run_tests()                                   │ │
│  └──────────────────────────────────────────────────┘ │
└────┬───────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Tool Manager: execute_tools()                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Parallel Execution:                               │ │
│  │                                                    │ │
│  │ [GitHub]    create_repository()                   │ │
│  │   └─> ✅ Repo created: user-auth-api              │ │
│  │                                                    │ │
│  │ [Docker]    build_image()                         │ │
│  │   └─> ✅ Image built: user-auth-api:latest        │ │
│  │                                                    │ │
│  │ [Terminal]  run_tests()                           │ │
│  │   └─> ✅ All tests passed                         │ │
│  └──────────────────────────────────────────────────┘ │
└────┬───────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Quality Checker: check()                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │ - Length: ✅ 1247 chars                           │ │
│  │ - Patterns: ✅ No failure indicators              │ │
│  │ - Score: 0.95 (threshold: 0.7)                   │ │
│  │ - Result: ✅ PASSED                               │ │
│  └──────────────────────────────────────────────────┘ │
└────┬───────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Response to User                                      │
│  {                                                     │
│    "provider": "claude_code",                         │
│    "message": "I've created a REST API...",           │
│    "tool_results": [                                  │
│      {"tool": "github", "success": true},             │
│      {"tool": "docker", "success": true}              │
│    ],                                                  │
│    "execution_time": 8.5,                             │
│    "quality_check": {"passed": true, "score": 0.95}  │
│  }                                                     │
└────────────────────────────────────────────────────────┘
```

---

## 3. Fallback Chain (Incident Analysis)

```
                    USER REQUEST
                         │
                         ▼
          "Analyze this production incident"
                         │
                         ▼
                  ┌──────────────┐
                  │ Task Router  │
                  │ Category:    │
                  │ INCIDENT_    │
                  │ ANALYSIS     │
                  └──────┬───────┘
                         │
         ┌───────────────┴───────────────┐
         │  Fallback Chain Determined:   │
         │  Local LLM → Claude → Gemini  │
         └───────────────┬───────────────┘
                         │
         ╔═══════════════▼════════════════╗
         ║  TRY PRIMARY: Local LLM        ║
         ╚═══════════════╤════════════════╝
                         │
                 ┌───────▼────────┐
                 │ Local LLM      │
                 │ (Ollama)       │
                 │ - Privacy ✅   │
                 │ - Cost: $0 ✅  │
                 └───────┬────────┘
                         │
                    ┌────▼─────┐
                    │ Quality  │
                    │ Check?   │
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    ✅ PASSED      ❌ FAILED      ⚠️  ERROR
  Score ≥ 0.7   Score < 0.7    Connection
          │              │           Failed
          │              │              │
          │              └──────┬───────┘
          │                     │
          │         📝 Log: Local→Claude
          │                     │
          │      ╔══════════════▼═════════════╗
          │      ║  TRY FALLBACK #1: Claude  ║
          │      ╚══════════════╤═════════════╝
          │                     │
          │             ┌───────▼────────┐
          │             │ Claude         │
          │             │ (Anthropic)    │
          │             │ - Reasoning ✅ │
          │             │ - Cost: $0.10  │
          │             └───────┬────────┘
          │                     │
          │                ┌────▼─────┐
          │                │ Quality  │
          │                │ Check?   │
          │                └────┬─────┘
          │                     │
          │      ┌──────────────┼──────────────┐
          │      │              │              │
          │      ▼              ▼              ▼
          │  ✅ PASSED      ❌ FAILED      ⚠️  ERROR
          │                     │              │
          │                     └──────┬───────┘
          │                            │
          │              📝 Log: Claude→Gemini
          │                            │
          │         ╔══════════════════▼═════════════╗
          │         ║  TRY FALLBACK #2: Gemini      ║
          │         ║  (Final Attempt)               ║
          │         ╚══════════════════╤═════════════╝
          │                            │
          │                    ┌───────▼────────┐
          │                    │ Gemini         │
          │                    │ (Google)       │
          │                    │ - Last resort  │
          │                    │ - Cost: $0.05  │
          │                    └───────┬────────┘
          │                            │
          └────────────────────────────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │ Return to User │
                              │ + Fallback Log │
                              └────────────────┘
```

**Fallback Metrics Logged:**
- From Provider → To Provider
- Reason (error/quality/timeout)
- Timestamp
- Task category
- Success/Failure

---

## 4. Multi-LLM Collaboration

```
USER: "Build a complete monitoring dashboard with deployment"
│
▼
┌────────────────────────────────────────────────────┐
│  Orchestrator detects collaboration pattern         │
│  Plan: [Gemini → ChatGPT → Claude Code]           │
└──────────────────┬─────────────────────────────────┘
                   │
    ╔══════════════▼═══════════════╗
    ║  STEP 1: GEMINI              ║
    ║  Role: Optimize Requirements ║
    ╚══════════════╤═══════════════╝
                   │
         ┌─────────▼──────────┐
         │ Gemini analyzes:   │
         │ - Best practices   │
         │ - Optimal structure│
         │ - Requirements     │
         └─────────┬──────────┘
                   │
         OUTPUT: "Dashboard should have:
                  - Real-time metrics display
                  - Alert system integration
                  - Auto-refresh every 5s
                  - Responsive layout
                  - Dark/light themes"
                   │
    ╔══════════════▼═══════════════╗
    ║  STEP 2: CHATGPT             ║
    ║  Role: Design UI/UX          ║
    ╚══════════════╤═══════════════╝
                   │
         ┌─────────▼──────────┐
         │ ChatGPT creates:   │
         │ - Layout design    │
         │ - Components       │
         │ - Interactions     │
         │ Uses Gemini output │
         └─────────┬──────────┘
                   │
         OUTPUT: "Dashboard design:
                  - Grid: 3x2 layout
                  - Charts: Line, Bar, Gauge
                  - Components: React
                  - Styling: Tailwind CSS
                  - Navigation: Sidebar"
                   │
    ╔══════════════▼═══════════════╗
    ║  STEP 3: CLAUDE CODE         ║
    ║  Role: Implement & Deploy    ║
    ╚══════════════╤═══════════════╝
                   │
         ┌─────────▼──────────────┐
         │ Claude Code:           │
         │ - Generates code       │
         │ - Creates Dockerfile   │
         │ - K8s manifests        │
         │ Uses ChatGPT design    │
         └─────────┬──────────────┘
                   │
         Tool Calls:
         │ ├─ build_docker_image()
         │ ├─ create_k8s_deployment()
         │ └─ create_github_repo()
                   │
         ┌─────────▼──────────────┐
         │ Tool Execution:        │
         │ ✅ Docker built         │
         │ ✅ K8s deployed         │
         │ ✅ Repo created         │
         └─────────┬──────────────┘
                   │
         OUTPUT: "Deployed to:
                  https://dashboard.prod.example.com
                  GitHub: github.com/user/dashboard
                  Container: dashboard:v1.0.0"
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│  Aggregated Response to User                         │
│  ┌────────────────────────────────────────────────┐ │
│  │ Step 1 (Gemini): Requirements optimized        │ │
│  │ Step 2 (ChatGPT): UI designed                  │ │
│  │ Step 3 (Claude): Deployed successfully         │ │
│  │                                                 │ │
│  │ Result: Production-ready dashboard             │ │
│  │ URL: https://dashboard.prod.example.com        │ │
│  │ Execution time: 25.3 seconds                   │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## 5. Routing Decision Tree

```
                    ┌──────────────────┐
                    │  User Message    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Check Explicit   │
                    │ Provider?        │
                    │ (@provider:)     │
                    └────┬────────┬────┘
                         │        │
                    YES  │        │  NO
                         │        │
                    ┌────▼────┐   │
                    │ Use     │   │
                    │ Specified│   │
                    │ Provider│   │
                    └─────────┘   │
                                  │
                         ┌────────▼────────┐
                         │ Pattern Matching│
                         │ Analysis        │
                         └────────┬────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
    ┌────▼─────┐          ┌──────▼──────┐          ┌────▼─────┐
    │"build"   │          │"ui"         │          │"analyze" │
    │"code"    │          │"dashboard"  │          │"incident"│
    │"implement"│          │"interface" │          │"logs"    │
    └────┬─────┘          └──────┬──────┘          └────┬─────┘
         │                        │                        │
         │                        │                        │
    ┌────▼─────────┐      ┌──────▼────────┐       ┌──────▼─────┐
    │ Claude Code  │      │   ChatGPT     │       │ Local LLM  │
    │ (0.9 conf)   │      │  (0.9 conf)   │       │ (0.95 conf)│
    └────┬─────────┘      └──────┬────────┘       └──────┬─────┘
         │                        │                        │
    Fallback:              Fallback:                 Fallback:
    Claude                 Claude                    Claude→Gemini
         │                        │                        │
         └────────────────────────┴────────────────────────┘
                                  │
                         ┌────────▼────────┐
                         │ Check           │
                         │ Collaboration?  │
                         └────┬───────┬────┘
                              │       │
                         YES  │       │  NO
                              │       │
                    ┌─────────▼──┐    │
                    │ Create     │    │
                    │ Multi-LLM  │    │
                    │ Plan       │    │
                    └────────────┘    │
                                      │
                             ┌────────▼────────┐
                             │ Execute with    │
                             │ Selected        │
                             │ Provider        │
                             └─────────────────┘
```

**Pattern Weights:**
- "build", "code", "implement" → Claude Code (0.9)
- "ui", "dashboard", "interface" → ChatGPT (0.9)
- "optimize prompt" → Gemini (0.95)
- "analyze incident" → Local LLM (0.95)

---

## 6. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCKER COMPOSE STACK                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  orchestrator:8000                                         │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Python 3.11 + Poetry                                │ │ │
│  │  │  FastAPI + Uvicorn                                   │ │ │
│  │  │  Volumes: src/, .kube/, docker.sock                  │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│  ┌───────────▼──────┐  ┌────▼──────┐  ┌────▼────────────────┐ │
│  │  redis:6379      │  │ ollama    │  │ prometheus:9090     │ │
│  │  ┌──────────────┐│  │ :11434    │  │ ┌──────────────────┐│ │
│  │  │ Cache        ││  │ ┌────────┐│  │ │ Scrapes /metrics ││ │
│  │  │ Sessions     ││  │ │ Local  ││  │ │ Time series DB   ││ │
│  │  └──────────────┘│  │ │ Models ││  │ └──────────────────┘│ │
│  │  Volume:         │  │ └────────┘│  │ Volume:             │ │
│  │  redis-data      │  │ Volume:   │  │ prometheus-data     │ │
│  └──────────────────┘  │ ollama-   │  └─────────────────────┘ │
│                        │ data      │              │            │
│                        └───────────┘              │            │
│                                                    │            │
│                                          ┌─────────▼────────┐  │
│                                          │ grafana:3000     │  │
│                                          │ ┌───────────────┐│  │
│                                          │ │ Dashboards    ││  │
│                                          │ │ Visualizations││  │
│                                          │ │ Alerts        ││  │
│                                          │ └───────────────┘│  │
│                                          │ Volume:          │  │
│                                          │ grafana-data     │  │
│                                          └──────────────────┘  │
│                                                                 │
│  Network: orchestrator-network (bridge)                        │
└─────────────────────────────────────────────────────────────────┘

External Integrations:
├─ GitHub API (via token)
├─ Anthropic API (Claude, Claude Code)
├─ OpenAI API (ChatGPT)
├─ Google API (Gemini)
├─ Kubernetes Cluster (via kubeconfig)
└─ Docker Daemon (via socket)
```

---

## Viewing These Diagrams

### Mermaid Diagrams (Interactive)

The `.mmd` files can be viewed using:

1. **Online**: Visit [mermaid.live](https://mermaid.live) and paste the content
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **GitHub**: GitHub renders Mermaid diagrams automatically in markdown

### Text Diagrams

The ASCII diagrams in this file render in any text editor or markdown viewer.

---

## Diagram Files

| File | Description |
|------|-------------|
| `architecture-diagram.mmd` | Complete system architecture (Mermaid) |
| `request-flow-diagram.mmd` | Request processing flow (Sequence) |
| `fallback-flow-diagram.mmd` | Fallback chain logic (Flowchart) |
| `collaboration-flow-diagram.mmd` | Multi-LLM collaboration (Sequence) |
| `DIAGRAMS.md` | This file with all ASCII diagrams |

---

## Color Legend (for Mermaid diagrams)

- 🔵 **Blue** - LLM Providers
- 🟠 **Orange** - Tools
- 🟣 **Purple** - Core Components
- 🟢 **Green** - Infrastructure

---

**Last Updated**: 2025-10-12
**Version**: 1.0.0
