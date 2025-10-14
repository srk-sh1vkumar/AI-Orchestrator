"""Python client for AI Orchestrator."""

import httpx
from typing import Optional, Dict, Any, List


class AIOrchestrator:
    """Python client for AI Orchestrator API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client.

        Args:
            base_url: Base URL of orchestrator API
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def chat(
        self,
        message: str,
        provider: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        enable_tools: bool = True,
        enable_collaboration: bool = True,
    ) -> Dict[str, Any]:
        """Send a chat message.

        Args:
            message: User message
            provider: Explicit provider (claude_code, chatgpt, gemini, claude, local)
            context: Additional context (logs, metrics, etc.)
            enable_tools: Enable tool execution
            enable_collaboration: Enable multi-LLM collaboration

        Returns:
            Response dict with message, provider, tools executed, etc.
        """
        # Add provider prefix if specified
        if provider:
            message = f"@{provider}: {message}"

        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "message": message,
                "context": context,
                "enable_tools": enable_tools,
                "enable_collaboration": enable_collaboration,
            },
        )
        response.raise_for_status()
        return response.json()

    async def health(self) -> Dict[str, Any]:
        """Check health of orchestrator and providers.

        Returns:
            Health status dict
        """
        response = await self.client.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()

    async def list_providers(self) -> Dict[str, Any]:
        """List available providers.

        Returns:
            Provider information dict
        """
        response = await self.client.get(f"{self.base_url}/api/providers")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Example usage
async def main():
    """Example usage of AI Orchestrator client."""

    async with AIOrchestrator() as orchestrator:
        # Example 1: Simple code generation
        print("=" * 60)
        print("Example 1: Code Generation")
        print("=" * 60)

        result = await orchestrator.chat(
            message="Build a REST API for user authentication"
        )

        print(f"Provider: {result['provider']}")
        print(f"Category: {result['routing_decision']['category']}")
        print(f"Response: {result['message'][:200]}...")
        print(f"Tools executed: {len(result['tool_results'])}")

        # Example 2: Incident analysis with context
        print("\n" + "=" * 60)
        print("Example 2: Incident Analysis")
        print("=" * 60)

        result = await orchestrator.chat(
            message="Analyze this production incident",
            context={
                "logs": [
                    "ERROR: Database connection timeout",
                    "ERROR: Connection pool exhausted",
                    "WARN: High memory usage detected"
                ],
                "metrics": {
                    "error_rate": 0.35,
                    "response_time_ms": 5000,
                    "cpu_usage": 0.95
                }
            }
        )

        print(f"Provider: {result['provider']}")
        print(f"Fallbacks: {len(result['fallback_events'])}")
        print(f"Response: {result['message'][:200]}...")

        # Example 3: Explicit provider
        print("\n" + "=" * 60)
        print("Example 3: Explicit Provider (ChatGPT)")
        print("=" * 60)

        result = await orchestrator.chat(
            message="Create a dashboard for monitoring",
            provider="chatgpt"
        )

        print(f"Provider: {result['provider']}")
        print(f"Response: {result['message'][:200]}...")

        # Example 4: Multi-LLM collaboration
        print("\n" + "=" * 60)
        print("Example 4: Multi-LLM Collaboration")
        print("=" * 60)

        result = await orchestrator.chat(
            message="Build a complete monitoring dashboard with deployment",
            enable_collaboration=True
        )

        if result.get('collaboration_steps'):
            print(f"Collaboration steps: {len(result['collaboration_steps'])}")
            for step in result['collaboration_steps']:
                print(f"  Step {step['step']}: {step['provider']} ({step['execution_time']:.2f}s)")

        # Example 5: Check health
        print("\n" + "=" * 60)
        print("Example 5: Health Check")
        print("=" * 60)

        health = await orchestrator.health()
        print(f"Status: {health['status']}")
        print("Providers:")
        for provider, status in health['providers'].items():
            print(f"  {provider}: {'✓' if status else '✗'}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
