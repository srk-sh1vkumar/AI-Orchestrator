# AI Orchestrator - Documentation Index

**Version:** 0.1.0
**Last Updated:** 2025-11-02
**Python:** 3.11+ (tested on 3.13.7)

Welcome to the AI Orchestrator documentation! This directory contains comprehensive guides, references, and technical documentation for the project.

---

## 📚 Documentation Structure

```
docs/
├── README.md                          # This file - documentation index
├── QUICK_REFERENCE.md                 # Daily cheat sheet
├── DOCUMENTATION_GOVERNANCE.md        # Documentation standards and rules
│
├── setup/                             # Getting Started & Configuration
│   ├── QUICKSTART.md                  # Quick start guide
│   ├── SETUP_GUIDE.md                 # Complete setup instructions
│   ├── LOCAL_LLM_SETUP.md             # Local LLM (Ollama) configuration
│   ├── DEEPSEEK_M1_SETUP_GUIDE.md     # DeepSeek integration
│   ├── QUICKSTART_DEVAI.md            # DevAI quick start
│   ├── QUICK_START_TOKEN_ANALYTICS.md # Token analytics setup
│   ├── TESTING_LOCAL_LLMS.md          # Local LLM testing guide
│   ├── SETUP_COMPLETE.md              # Setup completion report
│   └── PYTHON_3.13_MIGRATION.md       # Python 3.13 migration guide
│
├── enhancements/                      # Enhancement Completion Reports
│   ├── ENHANCEMENT_001_COMPLETE.md    # Intent-based Routing
│   ├── ENHANCEMENT_002_COMPLETE.md    # Advanced Fallback
│   ├── ENHANCEMENT_003_COMPLETE.md    # Context Window Management
│   ├── ENHANCEMENT_004_COMPLETE.md    # Semantic Caching
│   ├── ENHANCEMENT_006_COMPLETE.md    # Tool Output Validation
│   ├── ENHANCEMENT_012_COMPLETE.md    # Personal Goal Tracker
│   ├── ENHANCEMENT_013_COMPLETE.md    # Growth Tracking
│   ├── DEPLOYMENT_COMPLETE_2025-11-02.md      # Production deployment report
│   ├── PROVIDER_FIXES_STATUS_REPORT.md        # Provider bug fixes
│   ├── TOOL_EXECUTION_COMPLETE.md             # Tool execution implementation
│   ├── SESSION_SUMMARY_2025-11-02.md          # Session summary
│   ├── FINAL_SESSION_STATUS_2025-11-02.md     # Final session status
│   ├── FRONTEND_INTEGRATION_COMPLETE.md       # Frontend integration
│   ├── TOKEN_ANALYTICS_IMPLEMENTATION.md      # Token analytics
│   ├── IMPLEMENTATION_COMPLETE.md             # Implementation reports
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── ISSUE_RESOLUTION_SUMMARY.md
│   ├── ENHANCEMENT_TRACKER_SUMMARY.md
│   ├── FINAL_DELIVERABLES.md
│   └── FINAL_SUMMARY.md
│
├── architecture/                      # System Architecture
│   ├── ARCHITECTURE.md                # System overview
│   ├── DIAGRAMS.md                    # Architecture diagrams
│   ├── DATABASE_SCHEMA.md             # Database schema design
│   ├── DATABASE_INTEGRATION_SUMMARY.md # Database integration plan
│   ├── ADR-001-MONITORING-DASHBOARD.md # Architecture Decision Record
│   ├── ADR-002-RATE-LIMITING.md        # Rate limiting design
│   ├── ARCHITECTURE_ENHANCEMENTS.md    # Architecture improvements
│   ├── DEVAI_INTEGRATION_NOTES.md      # DevAI integration
│   └── PORT_CONFIGURATION.md           # Port allocation strategy
│
└── development/                       # Development Guides
    ├── USAGE_GUIDE.md                 # How to use the orchestrator
    ├── WEB_UI_GUIDE.md                # Web UI development
    ├── README_WEB_UI.md               # Web UI overview
    └── TOKEN_ANALYTICS_README.md      # Token analytics guide
```

---

## 🚀 Quick Start

**New to the project?** Start here:

1. **[QUICKSTART.md](setup/QUICKSTART.md)** - Get up and running in 5 minutes
2. **[SETUP_GUIDE.md](setup/SETUP_GUIDE.md)** - Complete setup instructions
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Daily command cheat sheet

**Quick activation:**
```bash
cd /Users/shiva/Projects/ai-orchestrator
source venv/bin/activate  # Or: poetry shell
pytest  # Verify all tests pass
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Access Points:**
- **Web UI:** http://localhost:8000/
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

---

## 📖 Documentation Categories

### 1. Setup & Configuration

Essential guides for getting the project running on your machine.

| Document | Purpose | Time to Complete |
|----------|---------|------------------|
| **[QUICKSTART.md](setup/QUICKSTART.md)** | Fast-track setup | 5 minutes |
| **[SETUP_GUIDE.md](setup/SETUP_GUIDE.md)** | Complete setup instructions | 10-15 minutes |
| **[LOCAL_LLM_SETUP.md](setup/LOCAL_LLM_SETUP.md)** | Configure Ollama for local LLMs | 10 minutes |
| **[DEEPSEEK_M1_SETUP_GUIDE.md](setup/DEEPSEEK_M1_SETUP_GUIDE.md)** | DeepSeek integration | 5 minutes |
| **[TESTING_LOCAL_LLMS.md](setup/TESTING_LOCAL_LLMS.md)** | Test local LLM providers | 5 minutes |
| **[PYTHON_3.13_MIGRATION.md](setup/PYTHON_3.13_MIGRATION.md)** | Python 3.13 benefits | 5 minutes read |

**What you'll learn:**
- Virtual environment setup (Python 3.11+)
- IDE configuration (VS Code, PyCharm)
- Environment variables (.env)
- Local LLM configuration (Ollama)
- Running tests and the application
- Troubleshooting common issues

---

### 2. Enhancement Reports

Detailed completion reports for each implemented enhancement.

| Enhancement | Title | Status | Report |
|-------------|-------|--------|--------|
| **001** | Intent-based Routing | ✅ Complete | [ENHANCEMENT_001_COMPLETE.md](enhancements/ENHANCEMENT_001_COMPLETE.md) |
| **002** | Advanced Fallback | ✅ Complete | [ENHANCEMENT_002_COMPLETE.md](enhancements/ENHANCEMENT_002_COMPLETE.md) |
| **003** | Context Window Management | ✅ Complete | [ENHANCEMENT_003_COMPLETE.md](enhancements/ENHANCEMENT_003_COMPLETE.md) |
| **004** | Semantic Caching | ✅ Complete | [ENHANCEMENT_004_COMPLETE.md](enhancements/ENHANCEMENT_004_COMPLETE.md) |
| **006** | Tool Output Validation | ✅ Complete | [ENHANCEMENT_006_COMPLETE.md](enhancements/ENHANCEMENT_006_COMPLETE.md) |
| **012** | Personal Goal Tracker | ✅ Complete | [ENHANCEMENT_012_COMPLETE.md](enhancements/ENHANCEMENT_012_COMPLETE.md) |
| **013** | Growth Tracking | ✅ Complete | [ENHANCEMENT_013_COMPLETE.md](enhancements/ENHANCEMENT_013_COMPLETE.md) |

**Recent Completion Reports:**
- [DEPLOYMENT_COMPLETE_2025-11-02.md](enhancements/DEPLOYMENT_COMPLETE_2025-11-02.md) - Production deployment
- [TOOL_EXECUTION_COMPLETE.md](enhancements/TOOL_EXECUTION_COMPLETE.md) - DevOps tool execution
- [PROVIDER_FIXES_STATUS_REPORT.md](enhancements/PROVIDER_FIXES_STATUS_REPORT.md) - Provider bug fixes
- [FRONTEND_INTEGRATION_COMPLETE.md](enhancements/FRONTEND_INTEGRATION_COMPLETE.md) - React UI

---

### 3. Architecture & Design

Technical architecture, database schemas, and system design.

| Document | Purpose | Audience |
|----------|---------|----------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System architecture overview | All developers |
| **[DIAGRAMS.md](DIAGRAMS.md)** | Visual architecture diagrams | Visual learners |
| **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** | MongoDB/PostgreSQL schemas | Developers, DBAs |
| **[DATABASE_INTEGRATION_SUMMARY.md](architecture/DATABASE_INTEGRATION_SUMMARY.md)** | Database integration plan | Architects, PMs |
| **[ADR-001-MONITORING-DASHBOARD.md](architecture/ADR-001-MONITORING-DASHBOARD.md)** | Monitoring design decisions | Architects |
| **[ADR-002-RATE-LIMITING.md](architecture/ADR-002-RATE-LIMITING.md)** | Rate limiting strategy | Architects |
| **[PORT_CONFIGURATION.md](architecture/PORT_CONFIGURATION.md)** | Port allocation strategy | DevOps |

**Key Concepts:**
- Multi-provider LLM routing (ChatGPT, Claude, Gemini, Local LLM)
- ML-based intent classification
- Tool execution framework (Docker, K8s, GitHub, Terminal)
- Fallback strategies
- Context window management
- Semantic caching with Redis
- Monitoring & metrics (Prometheus)

---

### 4. Development Guides

Guides for developing and extending the AI Orchestrator.

| Document | Purpose |
|----------|---------|
| **[USAGE_GUIDE.md](development/USAGE_GUIDE.md)** | How to use the orchestrator API |
| **[WEB_UI_GUIDE.md](development/WEB_UI_GUIDE.md)** | Frontend development guide |
| **[README_WEB_UI.md](development/README_WEB_UI.md)** | Web UI architecture overview |
| **[TOKEN_ANALYTICS_README.md](development/TOKEN_ANALYTICS_README.md)** | Token usage analytics |

**Development Topics:**
- API integration patterns
- Frontend development (React + TypeScript)
- Tool execution and validation
- Cost tracking and budgeting
- Adding new LLM providers
- Custom tool development

---

### 5. API Reference

API endpoints, schemas, and integration guides.

| Document | Purpose |
|----------|---------|
| **[api-reference.md](api-reference.md)** | Complete API documentation |
| **[routing-patterns.md](routing-patterns.md)** | Routing logic and patterns |

**Main Endpoints:**
- `POST /api/chat` - Main chat/orchestration endpoint
- `GET /api/health` - Health check with provider status
- `GET /api/providers` - List configured providers
- `GET /api/conversations` - Conversation history
- `GET /api/analytics/tokens` - Token usage analytics
- `GET /api/enhancements` - Enhancement tracker
- `GET /metrics` - Prometheus metrics

---

## 🎯 Documentation by Use Case

### "I'm setting up the project for the first time"

1. Read: [QUICKSTART.md](setup/QUICKSTART.md)
2. Run: `source venv/bin/activate && pytest`
3. Start: `uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`
4. Access: http://localhost:8000/
5. Bookmark: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### "I want to use local LLMs (Ollama)"

1. Install Ollama: https://ollama.ai
2. Read: [LOCAL_LLM_SETUP.md](setup/LOCAL_LLM_SETUP.md)
3. Test: [TESTING_LOCAL_LLMS.md](setup/TESTING_LOCAL_LLMS.md)
4. Configure: Update `.env` with `LOCAL_LLM_ENABLED=true`

### "I want to understand the provider routing"

1. Read: [ENHANCEMENT_001_COMPLETE.md](enhancements/ENHANCEMENT_001_COMPLETE.md)
2. Review: `src/core/intent_classifier.py`
3. Explore: [routing-patterns.md](routing-patterns.md)
4. Run: `pytest tests/test_intent_routing.py -v`

### "I need to integrate the database"

1. Read: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
2. Review: [DATABASE_INTEGRATION_SUMMARY.md](architecture/DATABASE_INTEGRATION_SUMMARY.md)
3. Check: `PROJECT_ENHANCEMENT_TRACKER_DB.yaml`
4. Setup: MongoDB connection in `.env`

### "I want to understand the tool execution"

1. Read: [TOOL_EXECUTION_COMPLETE.md](enhancements/TOOL_EXECUTION_COMPLETE.md)
2. Explore: `src/tools/` directory
3. Test: `/tmp/test_tools_comprehensive.py`
4. Use: `POST /api/chat` with `enable_tools: true`

### "I want to build/customize the frontend"

1. Read: [WEB_UI_GUIDE.md](development/WEB_UI_GUIDE.md)
2. Review: [README_WEB_UI.md](development/README_WEB_UI.md)
3. Setup: `cd frontend && npm install`
4. Develop: `npm run dev` (port 5173)
5. Build: `npm run build` (outputs to `dist/`)

### "I'm debugging an issue"

1. Check: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Troubleshooting section
2. Review: [SETUP_GUIDE.md](setup/SETUP_GUIDE.md) - Step 7: Troubleshooting
3. Run: `pytest -v --tb=short`
4. Check logs: Server logs in terminal or `orchestrator.log`

---

## 📊 Project Status Overview

| Metric | Value |
|--------|-------|
| **Python Version** | 3.11+ (tested on 3.13.7) |
| **Enhancements Complete** | 7/13 (54%) |
| **LLM Providers** | 5 (ChatGPT, Claude, Claude Code, Gemini, Local) |
| **Operational Providers** | 3/5 (ChatGPT, Gemini, Local LLM) |
| **DevOps Tools** | 9 (Docker, K8s, GitHub, Terminal, File System) |
| **Test Coverage** | 100% for tool execution (16/16 tests) |
| **Tool Execution Success** | 100% |
| **Production Ready** | 90% (missing: Claude API keys, MongoDB schema refinement) |
| **Documentation Files** | 40+ |

---

## 🔍 Finding Specific Information

### Search by Topic

**Setup & Installation:**
- Virtual environment → [SETUP_GUIDE.md](setup/SETUP_GUIDE.md) Step 1
- IDE configuration → [SETUP_GUIDE.md](setup/SETUP_GUIDE.md) Step 2
- Local LLM → [LOCAL_LLM_SETUP.md](setup/LOCAL_LLM_SETUP.md)
- Dependencies → [PYTHON_3.13_MIGRATION.md](setup/PYTHON_3.13_MIGRATION.md)

**Development:**
- Daily commands → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- API usage → [USAGE_GUIDE.md](development/USAGE_GUIDE.md)
- Frontend → [WEB_UI_GUIDE.md](development/WEB_UI_GUIDE.md)
- Testing → [SETUP_GUIDE.md](setup/SETUP_GUIDE.md) Step 5

**Architecture:**
- Routing logic → [routing-patterns.md](routing-patterns.md)
- Intent classification → [ENHANCEMENT_001_COMPLETE.md](enhancements/ENHANCEMENT_001_COMPLETE.md)
- Database design → [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- Monitoring → [ADR-001-MONITORING-DASHBOARD.md](architecture/ADR-001-MONITORING-DASHBOARD.md)
- Rate limiting → [ADR-002-RATE-LIMITING.md](architecture/ADR-002-RATE-LIMITING.md)

**API:**
- Endpoints → [api-reference.md](api-reference.md)
- Request/Response schemas → [api-reference.md](api-reference.md)

---

## 🔗 External Resources

- **Python 3.13 Documentation:** https://docs.python.org/3.13/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **React Documentation:** https://react.dev/
- **Sentence Transformers:** https://www.sbert.net/
- **Prometheus Metrics:** https://prometheus.io/docs/
- **Ollama (Local LLMs):** https://ollama.ai
- **MongoDB Documentation:** https://www.mongodb.com/docs/

---

## 📝 Documentation Standards

All documentation in this project follows the standards defined in [DOCUMENTATION_GOVERNANCE.md](DOCUMENTATION_GOVERNANCE.md):

**Core Principles:**
- **ONE TOPIC = ONE LOCATION = ONE FILE** - Single source of truth
- **Markdown format** - Easy to read, version control friendly
- **Code examples** - Working, tested code snippets
- **Clear structure** - Headers, tables, and lists for easy scanning
- **Up-to-date** - Last updated dates on all documents
- **Cross-referenced** - Links between related documents

**Directory Structure:**
- `docs/setup/` - Setup and configuration guides
- `docs/enhancements/` - Enhancement completion reports
- `docs/architecture/` - System design and architecture
- `docs/development/` - Developer guides and workflows
- `docs/` (root) - API reference, quick reference, indexes

**Forbidden Actions:**
- ❌ Never duplicate documentation across multiple files
- ❌ Never create alternative documentation structures
- ❌ Never create duplicate tracking files

---

## 🤝 Contributing to Documentation

Found a typo? Want to improve a guide? See an outdated section?

1. **Small fixes:** Edit the markdown file directly
2. **New documentation:** Add to appropriate subdirectory (`setup/`, `enhancements/`, `architecture/`, `development/`)
3. **Update this index:** When adding new docs
4. **Follow governance:** Review [DOCUMENTATION_GOVERNANCE.md](DOCUMENTATION_GOVERNANCE.md)

**Documentation checklist:**
- [ ] Clear, descriptive title
- [ ] Table of contents (for long docs)
- [ ] Code examples tested and working
- [ ] Links to related documentation
- [ ] Last updated date
- [ ] Single source of truth - no duplicates

---

## 📅 Documentation Changelog

### 2025-11-02
- ✅ Reorganized all root-level documentation into proper structure
- ✅ Moved 5 files from /tmp/ to docs/enhancements/
- ✅ Moved 13 enhancement completion reports to docs/enhancements/
- ✅ Moved 9 setup guides to docs/setup/
- ✅ Moved 6 architecture docs to docs/architecture/
- ✅ Moved 4 development guides to docs/development/
- ✅ Archived 13 duplicate/superseded files
- ✅ Created comprehensive documentation index (this file)
- ✅ Added DOCUMENTATION_GOVERNANCE.md to docs/
- ✅ Fixed frontend serving issue (src/api/main.py)
- ✅ Completed provider bug fixes and tool execution

### 2025-10-21
- ✅ Created organized docs/ structure
- ✅ Added Python 3.13 migration guide
- ✅ Added complete setup guide
- ✅ Added quick reference card
- ✅ Added Enhancement 001 completion report

### 2025-10-20
- ✅ Added database schema documentation
- ✅ Added database integration summary
- ✅ Updated project enhancement tracker

### 2025-10-19
- ✅ Initial documentation structure
- ✅ Architecture diagrams
- ✅ API reference

---

## 🎓 Learning Path

**Beginner (New to the project):**
1. [QUICKSTART.md](setup/QUICKSTART.md) - Get everything running
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Learn daily commands
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system

**Intermediate (Starting development):**
1. [ENHANCEMENT_001_COMPLETE.md](enhancements/ENHANCEMENT_001_COMPLETE.md) - Learn intent routing
2. [TOOL_EXECUTION_COMPLETE.md](enhancements/TOOL_EXECUTION_COMPLETE.md) - Understand tool execution
3. [routing-patterns.md](routing-patterns.md) - Master routing logic
4. [api-reference.md](api-reference.md) - Master the API

**Advanced (System design):**
1. [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database architecture
2. [ADR-001-MONITORING-DASHBOARD.md](architecture/ADR-001-MONITORING-DASHBOARD.md) - Monitoring design
3. [ADR-002-RATE-LIMITING.md](architecture/ADR-002-RATE-LIMITING.md) - Rate limiting strategy
4. [DIAGRAMS.md](DIAGRAMS.md) - Visual system design
5. Source code - `src/core/` and `src/api/`

---

## 📞 Getting Help

**Questions about:**
- **Setup:** See [SETUP_GUIDE.md](setup/SETUP_GUIDE.md) troubleshooting section
- **Local LLMs:** Check [LOCAL_LLM_SETUP.md](setup/LOCAL_LLM_SETUP.md)
- **Development:** Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Architecture:** Study [ARCHITECTURE.md](ARCHITECTURE.md)
- **API:** Consult [api-reference.md](api-reference.md)
- **Frontend:** Read [WEB_UI_GUIDE.md](development/WEB_UI_GUIDE.md)

**Can't find what you need?**
- Check the main [README.md](../README.md) in project root
- Review test files in `tests/` for usage examples
- Explore source code with IDE (Cmd+Click / F12 to navigate)
- Check recent enhancement reports in `docs/enhancements/`

---

## 🗂️ Archive

Superseded and duplicate documentation has been moved to `archive/legacy-root-docs-2025-11-02/`. These files are kept for historical reference but should not be used for current development.

---

**Happy coding! 🚀**

*Documentation maintained by the AI Orchestrator team*
*Last updated: 2025-11-02*
