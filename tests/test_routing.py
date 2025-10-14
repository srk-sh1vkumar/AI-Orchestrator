"""Tests for task routing."""

import pytest
from src.core.routing import TaskRouter
from src.models.schemas import LLMProvider, TaskCategory


@pytest.fixture
def router():
    """Create a router instance."""
    return TaskRouter()


def test_code_generation_routing(router):
    """Test routing for code generation tasks."""
    decision = router.route("Build a REST API for user management")
    assert decision.provider == LLMProvider.CLAUDE_CODE
    assert decision.category == TaskCategory.CODE_GENERATION


def test_ui_generation_routing(router):
    """Test routing for UI generation tasks."""
    decision = router.route("Create a dashboard for monitoring metrics")
    assert decision.provider == LLMProvider.CHATGPT
    assert decision.category == TaskCategory.UI_GENERATION


def test_incident_analysis_routing(router):
    """Test routing for incident analysis tasks."""
    decision = router.route("Analyze this production incident and find root cause")
    assert decision.provider == LLMProvider.LOCAL
    assert decision.category == TaskCategory.INCIDENT_ANALYSIS


def test_prompt_optimization_routing(router):
    """Test routing for prompt optimization tasks."""
    decision = router.route("Optimize this prompt for better results")
    assert decision.provider == LLMProvider.GEMINI
    assert decision.category == TaskCategory.PROMPT_OPTIMIZATION


def test_explicit_provider(router):
    """Test explicit provider selection."""
    decision = router.route("@chatgpt: Write some code")
    assert decision.provider == LLMProvider.CHATGPT
    assert decision.confidence == 1.0


def test_fallback_chain_incident(router):
    """Test fallback chain for incident analysis."""
    decision = router.route("Analyze logs for errors")
    assert decision.fallback_providers == [
        LLMProvider.LOCAL,
        LLMProvider.CLAUDE,
        LLMProvider.GEMINI,
    ]


def test_collaboration_detection(router):
    """Test collaboration detection."""
    decision = router.route("Build a complete dashboard with deployment")
    assert decision.requires_collaboration
    assert decision.collaboration_plan is not None
    assert len(decision.collaboration_plan) > 1


def test_category_classification(router):
    """Test task category classification."""
    assert router.classify_task("debug the api") == TaskCategory.DEBUGGING
    assert router.classify_task("deploy to kubernetes") == TaskCategory.DEPLOYMENT
    assert router.classify_task("write documentation") == TaskCategory.DOCUMENTATION
