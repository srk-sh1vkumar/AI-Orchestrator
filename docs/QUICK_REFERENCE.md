# AI Orchestrator - Quick Reference Card

**Python:** 3.13.7 | **Status:** Production Ready ✅

---

## 🚀 Instant Start (3 Commands)

```bash
source activate.sh                           # Activate Python 3.13 venv
pytest tests/test_intent_routing.py -v      # Verify all tests pass (27/27)
uvicorn src.api.main:app --reload           # Start API server → localhost:8000
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `activate.sh` | Quick venv activation script |
| `SETUP_GUIDE.md` | Complete setup instructions |
| `PYTHON_3.13_MIGRATION.md` | Python upgrade details |
| `ENHANCEMENT_001_COMPLETE.md` | Intent routing implementation |
| `PROJECT_ENHANCEMENT_TRACKER_DB.yaml` | Enhancement roadmap |
| `.vscode/settings.json` | IDE configuration |
| `.github/workflows/python-ci.yml` | CI/CD pipeline |

---

## 🔧 Essential Commands

### Environment
```bash
source activate.sh          # Activate venv (recommended)
deactivate                  # Exit venv
python --version            # Check Python version (should be 3.13.7)
```

### Running
```bash
uvicorn src.api.main:app --reload               # API server
python src/cli.py                               # CLI interface
cd frontend && npm run dev                      # Frontend (port 3000)
```

### Testing
```bash
pytest                                          # Run all tests
pytest tests/test_intent_routing.py -v         # Specific tests
pytest --cov=src --cov-report=html              # With coverage
```

### Code Quality
```bash
black src/ tests/                               # Format code
ruff check --fix src/ tests/                    # Lint and fix
mypy src/                                       # Type check
```

---

## 🎯 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| ImportError | `source activate.sh && pip install -r requirements.txt` |
| Port 8000 in use | `lsof -ti:8000 | xargs kill -9` |
| Tests failing | `find . -name "__pycache__" -exec rm -rf {} + && pytest` |

---

**Last Updated:** 2025-10-21 | **Python:** 3.13.7 | **Status:** 🚀 Active Development
