"""Tests for core orchestrator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.core.orchestrator import Orchestrator
from src.models.schemas import (
    ChatRequest,
    LLMProvider,
    LLMResponse,
    Message,
    RoutingDecision,
    TaskCategory,
)


@pytest.fixture
def orchestrator():
    """Create orchestrator instance."""
    return Orchestrator()


@pytest.mark.asyncio
async def test_process_request_basic(orchestrator):
    """Test basic request processing."""
    with patch.object(
        orchestrator.router, "route"
    ) as mock_route, patch.object(
        orchestrator.providers[LLMProvider.CLAUDE_CODE], "complete"
    ) as mock_complete:

        # Mock routing decision
        mock_route.return_value = RoutingDecision(
            provider=LLMProvider.CLAUDE_CODE,
            category=TaskCategory.CODE_GENERATION,
            confidence=0.9,
            reasoning="Test routing",
            fallback_providers=[],
        )

        # Mock LLM response
        mock_complete.return_value = LLMResponse(
            provider=LLMProvider.CLAUDE_CODE,
            content="Here's the code...",
            tool_calls=[],
            execution_time=1.0,
        )

        request = ChatRequest(message="Build a REST API")
        response = await orchestrator.process_request(request)

        assert response.provider == LLMProvider.CLAUDE_CODE
        assert response.routing_decision.category == TaskCategory.CODE_GENERATION
        assert "code" in response.message.lower()


@pytest.mark.asyncio
async def test_fallback_chain(orchestrator):
    """Test fallback chain execution."""
    with patch.object(
        orchestrator.router, "route"
    ) as mock_route:

        # Mock routing with fallback chain
        mock_route.return_value = RoutingDecision(
            provider=LLMProvider.LOCAL,
            category=TaskCategory.INCIDENT_ANALYSIS,
            confidence=0.95,
            reasoning="Incident analysis",
            fallback_providers=[
                LLMProvider.LOCAL,
                LLMProvider.CLAUDE,
                LLMProvider.GEMINI,
            ],
        )

        # Mock Local LLM failure
        with patch.object(
            orchestrator.providers[LLMProvider.LOCAL], "complete"
        ) as mock_local:
            mock_local.side_effect = Exception("Local LLM unavailable")

            # Mock Claude success
            with patch.object(
                orchestrator.providers[LLMProvider.CLAUDE], "complete"
            ) as mock_claude:
                mock_claude.return_value = LLMResponse(
                    provider=LLMProvider.CLAUDE,
                    content="Analysis complete...",
                    tool_calls=[],
                    execution_time=2.0,
                )

                request = ChatRequest(message="Analyze this incident")
                response = await orchestrator.process_request(request)

                # Should have fallen back to Claude
                assert response.provider == LLMProvider.CLAUDE
                assert len(response.fallback_events) > 0


@pytest.mark.asyncio
async def test_collaboration(orchestrator):
    """Test multi-LLM collaboration."""
    with patch.object(
        orchestrator.router, "route"
    ) as mock_route:

        # Mock routing with collaboration
        mock_route.return_value = RoutingDecision(
            provider=LLMProvider.GEMINI,
            category=TaskCategory.UI_GENERATION,
            confidence=0.95,
            reasoning="Requires collaboration",
            fallback_providers=[],
            requires_collaboration=True,
            collaboration_plan=[
                LLMProvider.GEMINI,
                LLMProvider.CHATGPT,
                LLMProvider.CLAUDE_CODE,
            ],
        )

        # Mock each provider
        with patch.object(
            orchestrator.providers[LLMProvider.GEMINI], "complete"
        ) as mock_gemini, patch.object(
            orchestrator.providers[LLMProvider.CHATGPT], "complete"
        ) as mock_chatgpt, patch.object(
            orchestrator.providers[LLMProvider.CLAUDE_CODE], "complete"
        ) as mock_claude_code:

            mock_gemini.return_value = LLMResponse(
                provider=LLMProvider.GEMINI,
                content="Optimized requirements...",
                tool_calls=[],
                execution_time=1.0,
            )

            mock_chatgpt.return_value = LLMResponse(
                provider=LLMProvider.CHATGPT,
                content="Dashboard design...",
                tool_calls=[],
                execution_time=1.5,
            )

            mock_claude_code.return_value = LLMResponse(
                provider=LLMProvider.CLAUDE_CODE,
                content="Implementation complete...",
                tool_calls=[],
                execution_time=2.0,
            )

            request = ChatRequest(
                message="Build a complete dashboard", enable_collaboration=True
            )
            response = await orchestrator.process_request(request)

            # Should have executed all steps
            assert response.collaboration_steps is not None
            assert len(response.collaboration_steps) == 3
            assert response.provider == LLMProvider.CLAUDE_CODE  # Last provider


@pytest.mark.asyncio
async def test_health_check(orchestrator):
    """Test health check."""
    with patch.object(
        orchestrator.providers[LLMProvider.CLAUDE_CODE], "health_check"
    ) as mock_health:
        mock_health.return_value = True

        health = await orchestrator.health_check()

        assert "status" in health
        assert "providers" in health
        assert "tools" in health


@pytest.mark.asyncio
async def test_explicit_provider(orchestrator):
    """Test explicit provider selection."""
    request = ChatRequest(
        message="Write some code", explicit_provider=LLMProvider.CHATGPT
    )

    with patch.object(
        orchestrator.providers[LLMProvider.CHATGPT], "complete"
    ) as mock_complete:
        mock_complete.return_value = LLMResponse(
            provider=LLMProvider.CHATGPT,
            content="Code here...",
            tool_calls=[],
            execution_time=1.0,
        )

        response = await orchestrator.process_request(request)

        # Should use explicitly requested provider
        assert response.provider == LLMProvider.CHATGPT
