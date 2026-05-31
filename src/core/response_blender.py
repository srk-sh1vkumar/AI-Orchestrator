"""Response blending for multi-provider orchestration.

Enhancement 018: Combine responses from multiple LLM providers.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import structlog
from src.models.schemas import LLMProvider, LLMResponse, Message

logger = structlog.get_logger()


@dataclass
class BlendedResponse:
    """Result of blending multiple provider responses."""

    content: str
    providers_used: List[LLMProvider]
    strategy: str
    total_tokens: int = 0
    total_execution_time: float = 0.0
    individual_responses: List[LLMResponse] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseBlender:
    """Combines responses from multiple LLM providers."""

    def __init__(self) -> None:
        """Initialize response blender."""
        self.logger = logger.bind(component="response_blender")

    async def blend(
        self,
        providers: List[LLMProvider],
        messages: List[Message],
        strategy: str = "sequential",
        orchestrator: Any = None,
    ) -> BlendedResponse:
        """Blend responses from multiple providers.

        Args:
            providers: List of providers to use
            messages: Conversation messages
            strategy: Blending strategy (sequential, parallel, consensus, combined)
            orchestrator: Orchestrator instance for making completions

        Returns:
            BlendedResponse with combined content
        """
        if not orchestrator:
            raise ValueError("Orchestrator required for blending")

        if strategy == "sequential":
            return await self._blend_sequential(providers, messages, orchestrator)
        elif strategy == "parallel":
            return await self._blend_parallel(providers, messages, orchestrator)
        elif strategy == "consensus":
            return await self._blend_consensus(providers, messages, orchestrator)
        elif strategy == "combined":
            return await self._blend_combined(providers, messages, orchestrator)
        else:
            self.logger.warning("unknown_blend_strategy", strategy=strategy, using="sequential")
            return await self._blend_sequential(providers, messages, orchestrator)

    async def _blend_sequential(
        self,
        providers: List[LLMProvider],
        messages: List[Message],
        orchestrator: Any,
    ) -> BlendedResponse:
        """Sequential blending - pass output from A as context to B.

        Provider A responds first, then B gets A's response as additional context.
        """
        responses: List[LLMResponse] = []
        current_messages = list(messages)
        total_tokens = 0
        total_time = 0.0

        for i, provider in enumerate(providers):
            self.logger.info("sequential_blend_step", step=i + 1, provider=provider.value)

            # Get completion from current provider
            response = await orchestrator.complete(
                messages=current_messages,
                provider=provider,
            )
            responses.append(response)
            total_tokens += response.tokens_used or 0
            total_time += response.execution_time

            # Add response as context for next provider
            if i < len(providers) - 1:
                # Add assistant response
                current_messages.append(
                    Message(role="assistant", content=response.content)
                )
                # Add continuation prompt
                current_messages.append(
                    Message(
                        role="user",
                        content=f"Based on the above analysis, please provide additional insights or expand on the response."
                    )
                )

        # Final response is the last provider's output
        final_content = responses[-1].content if responses else ""

        return BlendedResponse(
            content=final_content,
            providers_used=providers,
            strategy="sequential",
            total_tokens=total_tokens,
            total_execution_time=total_time,
            individual_responses=responses,
            metadata={
                "steps": len(providers),
                "context_passed": True,
            },
        )

    async def _blend_parallel(
        self,
        providers: List[LLMProvider],
        messages: List[Message],
        orchestrator: Any,
    ) -> BlendedResponse:
        """Parallel blending - all providers respond independently, merge results."""

        # Create tasks for all providers
        async def get_response(provider: LLMProvider) -> LLMResponse:
            return await orchestrator.complete(
                messages=messages,
                provider=provider,
            )

        tasks = [get_response(p) for p in providers]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful responses
        valid_responses: List[LLMResponse] = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                self.logger.error(
                    "parallel_blend_provider_failed",
                    provider=providers[i].value,
                    error=str(resp),
                )
            else:
                valid_responses.append(resp)

        if not valid_responses:
            raise RuntimeError("All providers failed during parallel blending")

        # Merge responses
        merged_content = self._merge_parallel_responses(valid_responses, providers)
        total_tokens = sum(r.tokens_used or 0 for r in valid_responses)
        max_time = max(r.execution_time for r in valid_responses)

        return BlendedResponse(
            content=merged_content,
            providers_used=[providers[i] for i, r in enumerate(responses) if not isinstance(r, Exception)],
            strategy="parallel",
            total_tokens=total_tokens,
            total_execution_time=max_time,
            individual_responses=valid_responses,
            metadata={
                "providers_attempted": len(providers),
                "providers_succeeded": len(valid_responses),
            },
        )

    def _merge_parallel_responses(
        self, responses: List[LLMResponse], providers: List[LLMProvider]
    ) -> str:
        """Merge multiple parallel responses into one."""
        if len(responses) == 1:
            return responses[0].content

        # Create structured merged response
        sections = []
        for i, response in enumerate(responses):
            provider_name = providers[i].value if i < len(providers) else f"Provider {i+1}"
            sections.append(f"## Analysis from {provider_name}\n\n{response.content}")

        merged = "\n\n---\n\n".join(sections)

        # Add summary section
        merged += "\n\n---\n\n## Combined Analysis\n\n"
        merged += "The above responses provide complementary perspectives on the query. "
        merged += "Key points have been gathered from multiple sources for comprehensive coverage."

        return merged

    async def _blend_consensus(
        self,
        providers: List[LLMProvider],
        messages: List[Message],
        orchestrator: Any,
    ) -> BlendedResponse:
        """Consensus blending - multiple providers vote on best answer."""

        # Get responses in parallel
        async def get_response(provider: LLMProvider) -> LLMResponse:
            return await orchestrator.complete(
                messages=messages,
                provider=provider,
            )

        tasks = [get_response(p) for p in providers]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        valid_responses: List[LLMResponse] = [
            r for r in responses if not isinstance(r, Exception)
        ]

        if not valid_responses:
            raise RuntimeError("All providers failed during consensus blending")

        # For consensus, we use the response with highest confidence/quality indicators
        # Simple heuristic: longest substantive response often has more detail
        best_response = max(valid_responses, key=lambda r: len(r.content))

        total_tokens = sum(r.tokens_used or 0 for r in valid_responses)
        max_time = max(r.execution_time for r in valid_responses)

        return BlendedResponse(
            content=best_response.content,
            providers_used=[providers[i] for i, r in enumerate(responses) if not isinstance(r, Exception)],
            strategy="consensus",
            total_tokens=total_tokens,
            total_execution_time=max_time,
            individual_responses=valid_responses,
            metadata={
                "consensus_method": "length_heuristic",
                "responses_considered": len(valid_responses),
            },
        )

    async def _blend_combined(
        self,
        providers: List[LLMProvider],
        messages: List[Message],
        orchestrator: Any,
    ) -> BlendedResponse:
        """Combined blending - intelligent merge of complementary responses."""

        # Get parallel responses first
        async def get_response(provider: LLMProvider) -> LLMResponse:
            return await orchestrator.complete(
                messages=messages,
                provider=provider,
            )

        tasks = [get_response(p) for p in providers]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        valid_responses: List[LLMResponse] = [
            r for r in responses if not isinstance(r, Exception)
        ]

        if not valid_responses:
            raise RuntimeError("All providers failed during combined blending")

        # Intelligently combine responses
        combined_content = self._combine_responses_intelligently(valid_responses)

        total_tokens = sum(r.tokens_used or 0 for r in valid_responses)
        max_time = max(r.execution_time for r in valid_responses)

        return BlendedResponse(
            content=combined_content,
            providers_used=[providers[i] for i, r in enumerate(responses) if not isinstance(r, Exception)],
            strategy="combined",
            total_tokens=total_tokens,
            total_execution_time=max_time,
            individual_responses=valid_responses,
            metadata={
                "merge_method": "intelligent_combination",
            },
        )

    def _combine_responses_intelligently(self, responses: List[LLMResponse]) -> str:
        """Intelligently combine multiple responses."""
        if len(responses) == 1:
            return responses[0].content

        # Extract unique insights from each response
        all_content = [r.content for r in responses]

        # Use first response as base
        base = all_content[0]

        # Add unique content from other responses
        additional_insights = []
        for i, content in enumerate(all_content[1:], 1):
            # Simple deduplication: add sections that seem unique
            # In production, use NLP/embeddings for better deduplication
            lines = content.split("\n")
            for line in lines:
                if line.strip() and line not in base and len(line) > 50:
                    additional_insights.append(line)

        if additional_insights:
            combined = base + "\n\n### Additional Insights\n\n"
            combined += "\n".join(additional_insights[:10])  # Limit additions
        else:
            combined = base

        return combined


# Singleton instance
_response_blender: Optional[ResponseBlender] = None


def get_response_blender() -> ResponseBlender:
    """Get singleton ResponseBlender instance."""
    global _response_blender
    if _response_blender is None:
        _response_blender = ResponseBlender()
    return _response_blender
