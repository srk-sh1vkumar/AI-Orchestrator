# AI Orchestrator - Documentation Map

Visual guide to all project documentation.

Last Updated: 2025-10-21

---

## 📁 Complete Documentation Structure

```
ai-orchestrator/
│
├── 📄 README.md                                 # Project overview (start here!)
├── 📄 QUICK_START.md                            # 3-minute quick start
├── 🔧 activate.sh                               # Virtual environment helper
├── 📝 PROJECT_ENHANCEMENT_TRACKER_DB.yaml       # Enhancement roadmap
│
├── 📁 docs/                                     # Main documentation directory
│   ├── 📄 README.md                             # Documentation index (you are here!)
│   ├── 📄 QUICK_REFERENCE.md                    # Daily cheat sheet ⭐
│   ├── 📄 DOCUMENTATION_MAP.md                  # This file - visual guide
│   │
│   ├── 📁 setup/                                # Getting Started
│   │   ├── 📄 SETUP_GUIDE.md                    # Complete setup (8 steps) ⭐
│   │   └── 📄 PYTHON_3.13_MIGRATION.md          # Python upgrade guide
│   │
│   ├── 📁 enhancements/                         # Enhancement Reports
│   │   ├── 📄 ENHANCEMENT_001_COMPLETE.md       # Intent-based Routing ✅
│   │   ├── 📄 ENHANCEMENT_002_COMPLETE.md       # (Future)
│   │   └── 📄 ENHANCEMENT_00X_COMPLETE.md       # (Future)
│   │
│   ├── 📁 architecture/                         # System Design
│   │   ├── 📄 DATABASE_SCHEMA.md                # PostgreSQL schema
│   │   ├── 📄 DATABASE_INTEGRATION_SUMMARY.md   # DB integration plan
│   │   ├── 📄 ARCHITECTURE.md                   # System overview
│   │   └── 📄 DIAGRAMS.md                       # Visual diagrams
│   │
│   ├── 📁 development/                          # Developer Guides
│   │   └── (coming soon)
│   │
│   ├── 📄 api-reference.md                      # API documentation
│   ├── 📄 routing-patterns.md                   # Routing logic
│   ├── 📄 project_enhancement_tracker.md        # Enhancement tracker (old)
│   └── 📄 INDEX.md                              # Legacy index
│
├── 📁 .vscode/                                  # IDE Configuration
│   ├── settings.json                            # VS Code Python settings
│   ├── launch.json                              # Debug configurations
│   └── extensions.json                          # Recommended extensions
│
├── 📁 .github/workflows/                        # CI/CD
│   └── python-ci.yml                            # GitHub Actions pipeline
│
├── 📁 src/                                      # Source Code
│   ├── api/                                     # FastAPI application
│   ├── core/                                    # Core logic
│   │   ├── intent_classifier.py                 # ML routing ⭐
│   │   ├── routing.py                           # Task router
│   │   └── orchestrator.py                      # Main orchestrator
│   ├── models/                                  # Pydantic schemas
│   ├── providers/                               # LLM integrations
│   └── tools/                                   # Tool execution
│
├── 📁 tests/                                    # Test Suite
│   └── test_intent_routing.py                   # Enhancement 001 tests ⭐
│
└── 📁 frontend/                                 # React UI
    ├── src/
    └── package.json
```

---

## 🎯 Documentation by User Journey

### 🆕 First Time Setup

```
1. README.md (project overview)
   ↓
2. docs/setup/SETUP_GUIDE.md (step-by-step)
   ↓
3. source activate.sh (activate environment)
   ↓
4. pytest (verify installation)
   ↓
5. docs/QUICK_REFERENCE.md (bookmark this!)
```

### 👨‍💻 Daily Development

```
docs/QUICK_REFERENCE.md → Your daily companion
   ├── Common commands
   ├── Troubleshooting
   └── Quick links
```

### 🏗️ Understanding Architecture

```
1. docs/ARCHITECTURE.md (overview)
   ↓
2. docs/DIAGRAMS.md (visual diagrams)
   ↓
3. docs/routing-patterns.md (routing logic)
   ↓
4. docs/enhancements/ENHANCEMENT_001_COMPLETE.md (ML routing)
```

### 🔍 Working on Enhancements

```
1. PROJECT_ENHANCEMENT_TRACKER_DB.yaml (roadmap)
   ↓
2. docs/enhancements/ENHANCEMENT_00X_COMPLETE.md (reference)
   ↓
3. docs/architecture/DATABASE_SCHEMA.md (if needed)
   ↓
4. src/core/ (implementation)
```

---

## 📊 Documentation Categories

### 🚀 Getting Started (New Users)
- ⭐ `docs/setup/SETUP_GUIDE.md` - **START HERE**
- `docs/QUICK_REFERENCE.md` - Daily cheat sheet
- `docs/setup/PYTHON_3.13_MIGRATION.md` - Python details
- `.vscode/` - IDE auto-configuration

### 🏗️ Architecture & Design
- `docs/ARCHITECTURE.md` - System overview
- `docs/DIAGRAMS.md` - Visual diagrams
- `docs/architecture/DATABASE_SCHEMA.md` - Database design
- `docs/routing-patterns.md` - Routing logic

### 🎯 Enhancements & Features
- `PROJECT_ENHANCEMENT_TRACKER_DB.yaml` - Master tracker
- `docs/enhancements/ENHANCEMENT_001_COMPLETE.md` - ML routing
- `docs/project_enhancement_tracker.md` - Legacy tracker

### 🔧 Development
- `docs/QUICK_REFERENCE.md` - Command reference
- `docs/api-reference.md` - API docs
- `.github/workflows/python-ci.yml` - CI/CD
- `tests/` - Test examples

---

## 🔍 Find Documentation By...

### By File Type
**Markdown (`.md`)** - All human-readable documentation
**YAML (`.yml`, `.yaml`)** - Configuration and tracking
**JSON** - IDE and tool configuration

### By Purpose
**Learning:** `docs/setup/`, `docs/ARCHITECTURE.md`
**Reference:** `docs/QUICK_REFERENCE.md`, `docs/api-reference.md`
**Reports:** `docs/enhancements/`
**Configuration:** `.vscode/`, `.github/workflows/`

### By Audience
**New Developers:** `docs/setup/SETUP_GUIDE.md`
**Experienced Developers:** `docs/QUICK_REFERENCE.md`
**Architects:** `docs/ARCHITECTURE.md`, `docs/DATABASE_SCHEMA.md`
**Product Managers:** `PROJECT_ENHANCEMENT_TRACKER_DB.yaml`

---

## 📝 Quick Links by Task

| Task | Documentation |
|------|---------------|
| **Set up project** | [SETUP_GUIDE.md](setup/SETUP_GUIDE.md) |
| **Daily commands** | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| **Understand ML routing** | [ENHANCEMENT_001_COMPLETE.md](enhancements/ENHANCEMENT_001_COMPLETE.md) |
| **API integration** | [api-reference.md](api-reference.md) |
| **Database design** | [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) |
| **VS Code setup** | `.vscode/settings.json` |
| **CI/CD pipeline** | `.github/workflows/python-ci.yml` |
| **Troubleshooting** | [SETUP_GUIDE.md](setup/SETUP_GUIDE.md) Step 7 |

---

## 🎓 Recommended Reading Order

### Beginner
1. `README.md`
2. `docs/setup/SETUP_GUIDE.md`
3. `docs/QUICK_REFERENCE.md`

### Intermediate
1. `docs/ARCHITECTURE.md`
2. `docs/enhancements/ENHANCEMENT_001_COMPLETE.md`
3. `docs/routing-patterns.md`

### Advanced
1. `docs/DATABASE_SCHEMA.md`
2. `docs/DIAGRAMS.md`
3. Source code in `src/core/`

---

## 📅 Documentation Updates

**Latest additions (2025-10-21):**
- ✅ Organized docs/ structure
- ✅ Python 3.13 migration guide
- ✅ Complete setup guide
- ✅ Quick reference card
- ✅ Enhancement 001 report
- ✅ Documentation index

**Coming soon:**
- Developer contribution guide
- Code style guide
- Release process documentation
- Video tutorials

---

## 🔗 External Documentation

- **Python 3.13:** https://docs.python.org/3.13/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Pydantic:** https://docs.pydantic.dev/
- **Sentence Transformers:** https://www.sbert.net/
- **Prometheus:** https://prometheus.io/docs/

---

**Legend:**
- ⭐ = Essential/Most used
- ✅ = Complete
- 📋 = Planned
- 🔧 = Configuration
- 📁 = Directory
- 📄 = Document

**Last Updated:** 2025-10-21
