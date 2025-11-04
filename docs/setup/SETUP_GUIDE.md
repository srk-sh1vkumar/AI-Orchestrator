# AI Orchestrator - Complete Setup Guide

**Python Version:** 3.13.7
**Last Updated:** 2025-10-21

---

## Quick Start (5 Minutes)

```bash
# 1. Clone the repository (if not already done)
cd /Users/shiva/Projects/ai-orchestrator

# 2. Activate Python 3.13 virtual environment
source activate.sh

# 3. Verify installation
python --version  # Should show Python 3.13.7
pytest tests/ -v  # All tests should pass

# 4. Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Access API at: http://localhost:8000/docs

---

## Detailed Setup Instructions

### Prerequisites

1. **Python 3.13** (via Homebrew):
   ```bash
   brew install python@3.13
   ```

2. **Node.js 18+** (for frontend):
   ```bash
   brew install node
   ```

3. **Git** (should already be installed):
   ```bash
   git --version
   ```

---

## Step 1: Virtual Environment Setup

The virtual environment is **already created** at `venv/` with Python 3.13.7.

### Activate Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Or use the helper script:**
```bash
source activate.sh
```

**Windows:**
```cmd
venv\Scripts\activate
```

### Verify Activation

You should see `(venv)` in your terminal prompt:
```bash
(venv) user@machine ai-orchestrator %
```

Verify Python version:
```bash
python --version
# Output: Python 3.13.7
```

---

## Step 2: IDE Configuration

### VS Code (Recommended)

**Automatic Configuration:**
The `.vscode/` directory is already configured with:
- Python interpreter set to `venv/bin/python`
- Auto-activate on terminal open
- Pytest integration
- Black formatter on save
- Ruff linting
- Debug configurations

**Manual Verification:**
1. Open VS Code in this directory: `code .`
2. Open Command Palette: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
3. Select: `Python: Select Interpreter`
4. Choose: `./venv/bin/python` (Python 3.13.7)

**Install Recommended Extensions:**
VS Code will prompt you to install recommended extensions. Click "Install All".

Or install manually:
```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
```

### PyCharm

1. **File** → **Settings** (or **Preferences** on Mac)
2. **Project: ai-orchestrator** → **Python Interpreter**
3. Click **⚙️** → **Add** → **Existing Environment**
4. Browse to: `/Users/shiva/Projects/ai-orchestrator/venv/bin/python`
5. Click **OK**

### Cursor (AI-powered editor)

Same as VS Code - the `.vscode/` configuration works automatically.

---

## Step 3: Environment Variables

### Create .env File

```bash
cp .env.example .env
nano .env  # Edit with your API keys
```

### Required Variables

```bash
# LLM Provider API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Local LLM (Ollama) - Optional
LOCAL_LLM_ENABLED=false
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2

# Redis Cache - Optional
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379/0

# Server Configuration
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8000
LOG_LEVEL=INFO
```

### Security Note

**Never commit `.env` to Git!** It's already in `.gitignore`.

---

## Step 4: Running the Application

### Backend API Server

**Option 1: Using uvicorn directly**
```bash
source venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 2: Using VS Code debugger**
1. Open `src/api/main.py`
2. Press `F5` or click "Run and Debug"
3. Select "Python: FastAPI Server"

**Option 3: Using the venv directly (no activation needed)**
```bash
./venv/bin/uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Access:**
- API Documentation: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/health
- Metrics: http://localhost:8000/metrics

### Frontend Development Server

```bash
cd frontend
npm install  # First time only
npm run dev
```

**Access:** http://localhost:3000

### CLI Interface

```bash
source venv/bin/activate
python src/cli.py
```

---

## Step 5: Running Tests

### All Tests

```bash
pytest
```

### Specific Test File

```bash
pytest tests/test_intent_routing.py -v
```

### With Coverage

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Performance Tests

```bash
pytest tests/test_intent_routing.py::TestRoutingPerformance -v
```

### In VS Code

1. Open Testing sidebar (beaker icon)
2. Tests will auto-discover
3. Click ▶️ to run individual tests
4. Right-click for debug option

---

## Step 6: Code Quality Tools

### Format Code with Black

```bash
black src/ tests/
```

**Check without formatting:**
```bash
black --check --diff src/ tests/
```

### Lint with Ruff

```bash
ruff check src/ tests/
```

**Auto-fix issues:**
```bash
ruff check --fix src/ tests/
```

### Type Check with MyPy

```bash
mypy src/
```

### Pre-commit Hooks (Recommended)

Install pre-commit hooks to run checks automatically:
```bash
pre-commit install
```

Now Black, Ruff, and MyPy will run on every commit.

**Run manually:**
```bash
pre-commit run --all-files
```

---

## Step 7: Development Workflow

### Daily Workflow

```bash
# 1. Activate environment
source activate.sh

# 2. Pull latest changes
git pull origin main

# 3. Install any new dependencies
pip install -r requirements.txt

# 4. Run tests to ensure everything works
pytest

# 5. Start development server
uvicorn src.api.main:app --reload
```

### Adding New Dependencies

```bash
# 1. Install the package
pip install package-name

# 2. Update requirements.txt
pip freeze > requirements.txt

# 3. Commit both changes
git add requirements.txt pyproject.toml
git commit -m "feat(deps): add package-name for X functionality"
```

### Creating a New Enhancement

```bash
# 1. Check the enhancement tracker
cat PROJECT_ENHANCEMENT_TRACKER_DB.yaml

# 2. Create feature branch
git checkout -b feature/enhancement-002-xyz

# 3. Implement the enhancement
# ... code ...

# 4. Run tests
pytest

# 5. Format and lint
black src/ tests/
ruff check --fix src/ tests/

# 6. Commit changes
git add .
git commit -m "feat(routing): implement enhancement 002 - XYZ"

# 7. Push and create PR
git push -u origin feature/enhancement-002-xyz
```

---

## Step 8: CI/CD Configuration

### GitHub Actions

The project includes a GitHub Actions workflow at `.github/workflows/python-ci.yml`.

**Features:**
- ✅ Runs tests on Python 3.13
- ✅ Tests on Ubuntu and macOS
- ✅ Code quality checks (Black, Ruff, MyPy)
- ✅ Security scanning (Safety, Bandit)
- ✅ Coverage reporting (Codecov)
- ✅ Artifact uploads for test results

**Required Secrets:**

Add these to your GitHub repository settings:

1. Go to: **Settings** → **Secrets and variables** → **Actions**
2. Add:
   - `CODECOV_TOKEN` (from https://codecov.io)
   - `ANTHROPIC_API_KEY` (for integration tests)
   - `OPENAI_API_KEY` (for integration tests)

### Local CI Simulation

Run the same checks that CI runs:

```bash
# Format check
black --check src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/

# Security checks
pip install safety bandit
safety check
bandit -r src/

# Tests with coverage
pytest --cov=src --cov-report=xml
```

---

## Troubleshooting

### "ImportError: No module named 'X'"

**Solution:** Ensure virtual environment is activated:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Tests Failing Locally But Pass in CI

**Check Python version:**
```bash
python --version  # Should be 3.13.7
```

**Clear cache:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### Virtual Environment Corrupted

**Recreate from scratch:**
```bash
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Cannot find Python 3.13"

**Install via Homebrew:**
```bash
brew install python@3.13
which python3.13  # Verify installation
```

### Port 8000 Already in Use

**Find and kill the process:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Or use a different port:**
```bash
uvicorn src.api.main:app --reload --port 8001
```

---

## Project Structure

```
ai-orchestrator/
├── .github/
│   └── workflows/
│       └── python-ci.yml          # GitHub Actions CI/CD
├── .vscode/
│   ├── settings.json              # VS Code configuration
│   ├── launch.json                # Debug configurations
│   └── extensions.json            # Recommended extensions
├── src/
│   ├── api/                       # FastAPI application
│   ├── core/                      # Core routing logic
│   ├── models/                    # Pydantic models
│   ├── providers/                 # LLM provider integrations
│   └── tools/                     # Tool execution
├── tests/
│   └── test_intent_routing.py    # Tests for Enhancement 001
├── frontend/                      # React/TypeScript UI
├── venv/                          # Python 3.13 virtual environment
├── .env                           # Environment variables (NOT in Git)
├── .env.example                   # Template for .env
├── .envrc                         # direnv configuration
├── .gitignore                     # Git ignore rules
├── activate.sh                    # Quick activation script
├── pyproject.toml                 # Project configuration
├── requirements.txt               # Python dependencies
├── PYTHON_3.13_MIGRATION.md       # Migration guide
└── SETUP_GUIDE.md                 # This file
```

---

## Useful Commands Cheat Sheet

```bash
# Environment
source activate.sh                 # Activate venv
deactivate                         # Deactivate venv
python --version                   # Check Python version

# Dependencies
pip install -r requirements.txt    # Install all dependencies
pip install <package>              # Install specific package
pip freeze > requirements.txt      # Update requirements
pip list                           # List installed packages

# Running
uvicorn src.api.main:app --reload  # Start API server
python src/cli.py                  # Start CLI
cd frontend && npm run dev         # Start frontend

# Testing
pytest                             # Run all tests
pytest -v                          # Verbose output
pytest -k "test_name"              # Run specific test
pytest --cov=src                   # With coverage
pytest -x                          # Stop on first failure

# Code Quality
black src/ tests/                  # Format code
ruff check src/ tests/             # Lint code
mypy src/                          # Type check
pre-commit run --all-files         # Run all checks

# Git
git status                         # Check status
git add .                          # Stage all changes
git commit -m "message"            # Commit
git push                           # Push to remote
```

---

## Next Steps

1. ✅ **Environment activated** (`source activate.sh`)
2. ✅ **IDE configured** (`.vscode/` settings applied)
3. ✅ **Tests passing** (`pytest`)
4. ⏭️ **Configure .env** with your API keys
5. ⏭️ **Start development server** and test the API
6. ⏭️ **Add GitHub secrets** for CI/CD
7. ⏭️ **Begin working on next enhancement!**

---

## Support and Resources

- **Project Tracker:** `PROJECT_ENHANCEMENT_TRACKER_DB.yaml`
- **Database Schema:** `docs/DATABASE_SCHEMA.md`
- **Enhancement 001 Report:** `ENHANCEMENT_001_COMPLETE.md`
- **Python 3.13 Migration:** `PYTHON_3.13_MIGRATION.md`

---

**Happy Coding! 🚀**
