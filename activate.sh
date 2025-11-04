#!/bin/bash
# Activation helper for AI Orchestrator Python 3.13 virtual environment
# Usage: source activate.sh

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Python 3.13 virtual environment activated"
    echo "Python version: $(python --version)"
    echo ""
    echo "Quick commands:"
    echo "  deactivate          - Exit virtual environment"
    echo "  pytest tests/       - Run all tests"
    echo "  uvicorn src.api.main:app --reload  - Start API server"
    echo "  python src/cli.py   - Start CLI interface"
else
    echo "❌ Virtual environment not found!"
    echo "Run: python3.13 -m venv venv && pip install -r requirements.txt"
fi
