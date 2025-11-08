#!/usr/bin/env python3
"""Test streaming endpoint for first token latency and reliability."""

import asyncio
import time
import json
import sys
from typing import List, Dict, Any
import httpx

API_URL = "http://localhost:8000/api/chat/stream"

async def test_streaming_basic(provider: str = None) -> Dict[str, Any]:
    """Test basic streaming functionality and measure first token latency.

    Args:
        provider: Specific provider to test, or None for auto-routing

    Returns:
        Dict with test results
    """
    request_data = {
        "message": "Say hello and count to 3",
    }

    if provider:
        request_data["explicit_provider"] = provider

    results = {
        "provider": provider or "auto",
        "success": False,
        "first_token_latency_ms": None,
        "total_time_ms": None,
        "chunks_received": 0,
        "total_content_length": 0,
        "tokens_used": None,
        "error": None
    }

    start_time = time.time()
    first_chunk_time = None
    content_parts = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                API_URL,
                json=request_data
            ) as response:
                if response.status_code != 200:
                    results["error"] = f"HTTP {response.status_code}"
                    return results

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    # Record first chunk time
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                        results["first_token_latency_ms"] = (first_chunk_time - start_time) * 1000

                    # Parse chunk
                    try:
                        chunk_data = json.loads(line[6:])  # Remove "data: " prefix

                        if "error" in chunk_data:
                            results["error"] = chunk_data["error"]
                            break

                        results["chunks_received"] += 1

                        if chunk_data.get("content"):
                            content_parts.append(chunk_data["content"])
                            results["total_content_length"] += len(chunk_data["content"])

                        if chunk_data.get("is_final"):
                            results["tokens_used"] = chunk_data.get("tokens_used")
                            results["provider"] = chunk_data.get("provider", provider or "auto")
                            results["success"] = True
                            break

                    except json.JSONDecodeError as e:
                        results["error"] = f"JSON decode error: {e}"
                        break

        end_time = time.time()
        results["total_time_ms"] = (end_time - start_time) * 1000
        results["full_content"] = "".join(content_parts)

    except Exception as e:
        results["error"] = str(e)

    return results


async def test_multiple_streams(provider: str, count: int = 10) -> Dict[str, Any]:
    """Test multiple concurrent streams for reliability.

    Args:
        provider: Provider to test
        count: Number of concurrent streams

    Returns:
        Aggregated test results
    """
    print(f"\n🔄 Testing {count} concurrent streams with {provider}...")

    tasks = [test_streaming_basic(provider) for _ in range(count)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
    errors = [r for r in results if isinstance(r, Exception)]

    latencies = [r["first_token_latency_ms"] for r in successful if r.get("first_token_latency_ms")]

    summary = {
        "provider": provider,
        "total_requests": count,
        "successful": len(successful),
        "failed": len(failed),
        "errors": len(errors),
        "success_rate": len(successful) / count * 100,
        "avg_first_token_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "min_latency_ms": min(latencies) if latencies else None,
        "max_latency_ms": max(latencies) if latencies else None,
        "avg_chunks": sum(r["chunks_received"] for r in successful) / len(successful) if successful else None,
    }

    return summary


async def main():
    """Run streaming tests."""
    print("=" * 60)
    print("🚀 AI Orchestrator Streaming Tests")
    print("=" * 60)

    # Test 1: Basic streaming with each provider
    print("\n📊 Test 1: Basic Streaming with Each Provider")
    print("-" * 60)

    providers = ["claude", "chatgpt", "gemini", "local"]

    for provider in providers:
        print(f"\n🧪 Testing {provider}...")
        result = await test_streaming_basic(provider)

        if result["success"]:
            print(f"  ✅ Success!")
            print(f"  ⏱️  First token latency: {result['first_token_latency_ms']:.0f}ms")
            print(f"  ⏱️  Total time: {result['total_time_ms']:.0f}ms")
            print(f"  📦 Chunks received: {result['chunks_received']}")
            print(f"  📝 Content length: {result['total_content_length']} chars")
            if result["tokens_used"]:
                print(f"  🎯 Tokens used: {result['tokens_used']}")

            # Check latency target
            if result['first_token_latency_ms'] < 500:
                print(f"  🎉 Target achieved: <500ms")
            else:
                print(f"  ⚠️  Above target: {result['first_token_latency_ms']:.0f}ms > 500ms")
        else:
            print(f"  ❌ Failed: {result['error']}")

    # Test 2: Concurrent streams for reliability
    print("\n\n📊 Test 2: Concurrent Stream Reliability")
    print("-" * 60)

    # Test with smaller batch first
    for provider in ["local"]:  # Test with local provider (fastest)
        summary = await test_multiple_streams(provider, count=10)

        print(f"\n📈 Results for {provider}:")
        print(f"  Total requests: {summary['total_requests']}")
        print(f"  Successful: {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"  Failed: {summary['failed']}")
        print(f"  Errors: {summary['errors']}")

        if summary['avg_first_token_latency_ms']:
            print(f"  Avg latency: {summary['avg_first_token_latency_ms']:.0f}ms")
            print(f"  Min latency: {summary['min_latency_ms']:.0f}ms")
            print(f"  Max latency: {summary['max_latency_ms']:.0f}ms")
            print(f"  Avg chunks: {summary['avg_chunks']:.1f}")

        if summary['success_rate'] == 100:
            print(f"  🎉 Perfect reliability: 0 dropped streams!")
        elif summary['success_rate'] >= 95:
            print(f"  ✅ Good reliability: {summary['success_rate']:.1f}%")
        else:
            print(f"  ⚠️  Reliability issues: {summary['success_rate']:.1f}%")

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
