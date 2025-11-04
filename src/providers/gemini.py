"""Gemini provider integration."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
import google.generativeai as genai
from src.providers.base import BaseLLMProvider
from src.models.schemas import LLMResponse, LLMProvider, Message, ToolCall, ToolType, StreamChunk
from src.core.config import settings


class GeminiProvider(BaseLLMProvider):
    """Gemini provider for prompt optimization and analysis."""

    def __init__(self) -> None:
        """Initialize Gemini provider."""
        super().__init__(LLMProvider.GEMINI)
        genai.configure(api_key=settings.google_api_key)
        # Use gemini-2.5-flash: Current stable model (replaces retired 1.5 Flash)
        # Gemini 1.5 models were retired April 29, 2025
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def _complete_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> LLMResponse:
        """Generate a completion using Gemini.

        Args:
            messages: Conversation messages
            tools: Available tools
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            LLMResponse
        """
        start_time = time.time()

        try:
            # Format messages for Gemini
            prompt_parts = []
            for msg in messages:
                prefix = f"{msg.role.upper()}: "
                prompt_parts.append(prefix + msg.content)

            # Add system context
            system_context = """You are Gemini specialized in:
            - Prompt engineering and optimization
            - Meta-prompting and instruction refinement
            - Creating effective prompt templates
            - Analyzing prompt effectiveness
            - Incident and event analysis (as fallback)

            Help users create better prompts and analyze complex situations."""

            prompt = system_context + "\n\n" + "\n\n".join(prompt_parts)

            generation_config = genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            )

            response = self.model.generate_content(prompt, generation_config=generation_config)

            execution_time = time.time() - start_time

            content = response.text if response.text else ""

            self.logger.info("completion_generated", time=execution_time)

            return LLMResponse(
                provider=self.provider,
                content=content,
                tool_calls=[],  # Gemini doesn't support function calling in this version
                tokens_used=None,  # Token usage not available
                execution_time=execution_time,
                metadata={"model": "gemini-2.5-flash"},
            )

        except Exception as e:
            self.logger.error("completion_failed", error=str(e))
            raise

    async def _stream_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion using Gemini.

        Args:
            messages: Conversation messages
            tools: Available tools
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            StreamChunk: Incremental response chunks
        """
        try:
            # Format messages for Gemini
            prompt_parts = []
            for msg in messages:
                prefix = f"{msg.role.upper()}: "
                prompt_parts.append(prefix + msg.content)

            # Add system context
            system_context = """You are Gemini specialized in:
            - Prompt engineering and optimization
            - Meta-prompting and instruction refinement
            - Creating effective prompt templates
            - Analyzing prompt effectiveness
            - Incident and event analysis (as fallback)

            Help users create better prompts and analyze complex situations."""

            prompt = system_context + "\n\n" + "\n\n".join(prompt_parts)

            generation_config = genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            )

            # Stream response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )

            # Stream chunks
            for chunk in response:
                if chunk.text:
                    yield StreamChunk(
                        provider=self.provider,
                        content=chunk.text,
                        is_final=False
                    )

            # Send final chunk
            yield StreamChunk(
                provider=self.provider,
                content="",
                is_final=True,
                tokens_used=None,  # Token usage not available in Gemini
                metadata={"model": "gemini-2.5-flash"}
            )

            self.logger.info("streaming_completed", model="gemini-2.5-flash")

        except Exception as e:
            self.logger.error("streaming_failed", error=str(e))
            raise

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible.

        Returns:
            True if healthy
        """
        try:
            response = self.model.generate_content("Hello")
            return bool(response.text)
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False
