"""Claude Code provider integration."""

import time
from typing import List, Optional, Dict, Any
import anthropic
from src.providers.base import BaseLLMProvider
from src.models.schemas import LLMResponse, LLMProvider, Message, ToolCall, ToolType
from src.core.config import settings
import structlog

logger = structlog.get_logger()


class ClaudeCodeProvider(BaseLLMProvider):
    """Claude Code provider for code generation and DevOps tasks."""

    def __init__(self) -> None:
        """Initialize Claude Code provider."""
        super().__init__(LLMProvider.CLAUDE_CODE)
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model

    async def _complete_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> LLMResponse:
        """Generate a completion using Claude Code (implementation).

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

            # Add system message for Claude Code role
            system_message = """You are Claude Code, a specialized AI assistant for:
            - Code generation and implementation
            - Technical analysis and debugging
            - DevOps tasks (Docker, Kubernetes, CI/CD)
            - Deployment automation
            - Infrastructure as code
            - Testing and quality assurance

            You have direct access to tools for executing these tasks. Use them when appropriate."""

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

            # Extract content
            content = ""
            tool_calls: List[ToolCall] = []

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    # Map tool use to our ToolCall format
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
                metadata={
                    "model": self.model,
                    "stop_reason": response.stop_reason,
                },
            )

        except Exception as e:
            self.logger.error("completion_failed", error=str(e))
            raise

    async def health_check(self) -> bool:
        """Check if Claude API is accessible.

        Returns:
            True if healthy
        """
        try:
            # Simple message to test API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}],
            )
            return response.content[0].text is not None
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    def _map_tool_type(self, tool_name: str) -> ToolType:
        """Map tool name to ToolType enum.

        Args:
            tool_name: Name of the tool

        Returns:
            ToolType
        """
        # Map common tool names to types
        mapping = {
            "github": ToolType.GITHUB,
            "docker": ToolType.DOCKER,
            "kubernetes": ToolType.KUBERNETES,
            "k8s": ToolType.KUBERNETES,
            "terminal": ToolType.TERMINAL,
            "bash": ToolType.TERMINAL,
            "file": ToolType.FILE_SYSTEM,
            "jenkins": ToolType.JENKINS,
        }

        for key, value in mapping.items():
            if key in tool_name.lower():
                return value

        return ToolType.TERMINAL  # Default
