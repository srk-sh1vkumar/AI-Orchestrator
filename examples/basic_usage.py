"""Basic usage examples for AI Orchestrator."""

import asyncio
import httpx


async def basic_request():
    """Example: Basic request with automatic routing."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={"message": "Build a REST API for user authentication with JWT tokens"},
        )
        data = response.json()
        print(f"Provider: {data['provider']}")
        print(f"Response: {data['message'][:200]}...")
        print(f"Category: {data['routing_decision']['category']}")


async def explicit_provider():
    """Example: Explicit provider selection."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={
                "message": "@chatgpt: Create a dashboard layout for monitoring system metrics"
            },
        )
        data = response.json()
        print(f"Provider: {data['provider']}")
        print(f"Response: {data['message'][:200]}...")


async def incident_analysis():
    """Example: Incident analysis with fallback chain."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={
                "message": "Analyze this production incident: 500 errors increased by 300% at 2PM",
                "context": {
                    "logs": ["ERROR: Database connection timeout", "ERROR: Pool exhausted"],
                    "metrics": {"error_rate": 0.35, "response_time": 5000},
                },
            },
        )
        data = response.json()
        print(f"Provider: {data['provider']}")
        print(f"Fallback events: {len(data['fallback_events'])}")
        print(f"Response: {data['message'][:200]}...")


async def collaboration_task():
    """Example: Multi-LLM collaboration."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={
                "message": "Build a complete monitoring dashboard with deployment automation",
                "enable_collaboration": True,
            },
        )
        data = response.json()
        print(f"Collaboration steps: {len(data.get('collaboration_steps', []))}")
        if data.get("collaboration_steps"):
            for step in data["collaboration_steps"]:
                print(f"  Step {step['step']}: {step['provider']} - {step['execution_time']:.2f}s")


async def health_check():
    """Example: Check orchestrator health."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/health")
        data = response.json()
        print(f"Status: {data['status']}")
        print("Providers:")
        for provider, status in data["providers"].items():
            print(f"  {provider}: {'✓' if status else '✗'}")


async def list_providers():
    """Example: List available providers."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/providers")
        data = response.json()
        print("Available Providers:")
        for name, info in data["providers"].items():
            status = "✓" if info["configured"] else "✗"
            print(f"  {status} {name}: {info['role']}")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("AI Orchestrator - Usage Examples")
    print("=" * 60)

    print("\n1. Basic Request (Automatic Routing)")
    print("-" * 60)
    await basic_request()

    print("\n2. Explicit Provider Selection")
    print("-" * 60)
    await explicit_provider()

    print("\n3. Incident Analysis with Fallback")
    print("-" * 60)
    await incident_analysis()

    print("\n4. Multi-LLM Collaboration")
    print("-" * 60)
    await collaboration_task()

    print("\n5. Health Check")
    print("-" * 60)
    await health_check()

    print("\n6. List Providers")
    print("-" * 60)
    await list_providers()


if __name__ == "__main__":
    asyncio.run(main())
