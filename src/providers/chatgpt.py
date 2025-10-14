"""ChatGPT provider integration."""

import time
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from src.providers.base import BaseLLMProvider
from src.models.schemas import LLMResponse, LLMProvider, Message, ToolCall, ToolType
from src.core.config import settings


class ChatGPTProvider(BaseLLMProvider):
    """ChatGPT provider for UI and workflow automation."""

    def __init__(self) -> None:
        """Initialize ChatGPT provider."""
        super().__init__(LLMProvider.CHATGPT)
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4-turbo-preview"

    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> LLMResponse:
        """Generate a completion using ChatGPT.

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
            formatted_messages = self.format_messages(messages)

            # Add system message for ChatGPT role
            formatted_messages.insert(
                0,
                {
                    "role": "system",
                    "content": """You are ChatGPT specialized in:
                    - User interface and UX design
                    - Frontend development
                    - Dashboard creation
                    - Workflow automation
                    - Interactive component generation
                    - Report formatting and presentation

                    Create beautiful, functional interfaces and automate complex workflows.""",
                },
            )

            request_params: Dict[str, Any] = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**request_params)

            execution_time = time.time() - start_time

            message = response.choices[0].message
            content = message.content or ""
            tool_calls: List[ToolCall] = []

            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            tool_type=self._map_tool_type(tc.function.name),
                            operation=tc.function.name,
                            parameters=tc.function.arguments,
                            metadata={"tool_call_id": tc.id},
                        )
                    )

            self.logger.info(
                "completion_generated",
                tokens=response.usage.completion_tokens if response.usage else 0,
                tool_calls=len(tool_calls),
                time=execution_time,
            )

            return LLMResponse(
                provider=self.provider,
                content=content,
                tool_calls=tool_calls,
                tokens_used=response.usage.completion_tokens if response.usage else None,
                execution_time=execution_time,
                metadata={"model": self.model, "finish_reason": response.choices[0].finish_reason},
            )

        except Exception as e:
            self.logger.error("completion_failed", error=str(e))
            raise

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible.

        Returns:
            True if healthy
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": "Hello"}], max_tokens=10
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    def _map_tool_type(self, tool_name: str) -> ToolType:
        """Map tool name to ToolType enum."""
        mapping = {
            "github": ToolType.GITHUB,
            "file": ToolType.FILE_SYSTEM,
            "terminal": ToolType.TERMINAL,
        }

        for key, value in mapping.items():
            if key in tool_name.lower():
                return value

        return ToolType.FILE_SYSTEM
