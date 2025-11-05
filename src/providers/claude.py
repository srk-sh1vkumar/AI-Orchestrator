"""Claude provider integration (fallback for analysis)."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
import anthropic
from src.providers.base import BaseLLMProvider
from src.models.schemas import LLMResponse, LLMProvider, Message, ToolCall, ToolType, StreamChunk
from src.core.config import settings


class ClaudeProvider(BaseLLMProvider):
    """Claude provider for reasoning and analysis (fallback)."""

    def __init__(self) -> None:
        """Initialize Claude provider."""
        super().__init__(LLMProvider.CLAUDE)
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"

    async def _complete_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> LLMResponse:
        """Generate a completion using Claude.

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
            # Anthropic SDK requires max_tokens to be set (cannot be None)
            if max_tokens is None:
                max_tokens = 4096

            formatted_messages = self.format_messages(messages)

            system_message = """You are Claude, specialized in:
            - Incident analysis and root cause investigation
            - Complex reasoning and problem-solving
            - Event correlation and pattern recognition
            - Technical documentation
            - Deep analytical thinking

            Provide thorough, well-reasoned analysis."""

            request_params: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": formatted_messages,
                "system": system_message,
            }

            if tools:
                request_params["tools"] = tools

            response = self.client.messages.create(**request_params)

            execution_time = time.time() - start_time

            content = ""
            tool_calls: List[ToolCall] = []

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            tool_type=self._map_tool_type(block.name),
                            operation=block.name,
                            parameters=block.input,
                            metadata={"tool_use_id": block.id},
                        )
                    )

            self.logger.info(
                "completion_generated",
                tokens=response.usage.output_tokens,
                tool_calls=len(tool_calls),
                time=execution_time,
            )

            return LLMResponse(
                provider=self.provider,
                content=content,
                tool_calls=tool_calls,
                tokens_used=response.usage.output_tokens,
                execution_time=execution_time,
                metadata={"model": self.model, "stop_reason": response.stop_reason},
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
        """Stream a completion using Claude.

        Args:
            messages: Conversation messages
            tools: Available tools
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            StreamChunk: Incremental response chunks
        """
        try:
            # Anthropic SDK requires max_tokens to be set
            if max_tokens is None:
                max_tokens = 4096

            formatted_messages = self.format_messages(messages)

            system_message = """You are Claude, specialized in:
            - Incident analysis and root cause investigation
            - Complex reasoning and problem-solving
            - Event correlation and pattern recognition
            - Technical documentation
            - Deep analytical thinking

            Provide thorough, well-reasoned analysis."""

            request_params: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": formatted_messages,
                "system": system_message,
            }

            if tools:
                request_params["tools"] = tools

            # Use streaming API (synchronous API in async function)
            # Note: Anthropic Python SDK v0.34+ supports streaming but not async streaming
            # We need to use the sync stream in a way that works with async
            stream = self.client.messages.stream(**request_params)

            # Enter the context manager
            stream.__enter__()

            try:
                # Stream text chunks
                for text in stream.text_stream:
                    if text:  # Only yield non-empty chunks
                        yield StreamChunk(
                            provider=self.provider,
                            content=text,
                            is_final=False
                        )

                # Get final message for token usage
                final_message = stream.get_final_message()

                # Send final chunk with metadata
                yield StreamChunk(
                    provider=self.provider,
                    content="",
                    is_final=True,
                    tokens_used=final_message.usage.output_tokens,
                    metadata={
                        "model": self.model,
                        "stop_reason": final_message.stop_reason
                    }
                )

                self.logger.info(
                    "streaming_completed",
                    tokens=final_message.usage.output_tokens,
                    model=self.model
                )
            finally:
                # Ensure stream is properly closed
                stream.__exit__(None, None, None)

        except Exception as e:
            self.logger.error("streaming_failed", error=str(e))
            raise

    async def health_check(self) -> bool:
        """Check if Claude API is accessible.

        Returns:
            True if healthy
        """
        try:
            response = self.client.messages.create(
                model=self.model, max_tokens=10, messages=[{"role": "user", "content": "Hello"}]
            )
            return response.content[0].text is not None
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    def _map_tool_type(self, tool_name: str) -> ToolType:
        """Map tool name to ToolType enum."""
        mapping = {
            "elasticsearch": ToolType.ELASTICSEARCH,
            "splunk": ToolType.SPLUNK,
            "grafana": ToolType.GRAFANA,
            "prometheus": ToolType.PROMETHEUS,
        }

        for key, value in mapping.items():
            if key in tool_name.lower():
                return value

        return ToolType.TERMINAL
