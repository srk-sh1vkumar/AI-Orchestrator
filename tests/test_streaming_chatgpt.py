#!/usr/bin/env python3
"""Test streaming with ChatGPT provider (avoiding Claude auth issues)."""

import asyncio
import httpx
import time
import json


async def test_streaming(provider: str, question: str):
    """Test streaming for a specific provider."""
    print("=" * 80)
    print(f"Testing {provider.upper()} Streaming")
    print("=" * 80)

    url = "http://localhost:8000/api/chat/stream"
    request = {
        "message": f"@{provider}: {question}",
        "enable_tools": False,
        "enable_collaboration": False
    }

    print(f"\n📤 Request: {request['message']}")
    print(f"🔗 Endpoint: {url}\n")

    start_time = time.time()
    first_token_time = None
    content_chunks = []
    chunk_count = 0
    tokens_used = 0

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=request) as response:
                if response.status_code != 200:
                    print(f"❌ Error: HTTP {response.status_code}")
                    text = await response.aread()
                    print(f"Response: {text.decode()}")
                    return False

                buffer = ""
                async for chunk in response.aiter_bytes():
                    if first_token_time is None:
                        first_token_time = time.time()
                        latency_ms = int((first_token_time - start_time) * 1000)
                        print(f"⚡ First token latency: {latency_ms}ms\n")

                    # Decode and add to buffer
                    buffer += chunk.decode('utf-8')

                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)

                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])

                                if 'error' in data:
                                    print(f"\n❌ Stream Error: {data['error']}")
                                    return False

                                if data.get('content'):
                                    content_chunks.append(data['content'])
                                    print(data['content'], end='', flush=True)

                                chunk_count += 1

                                if data.get('is_final'):
                                    tokens_used = data.get('tokens_used', 0)
                                    print(f"\n\n✅ Final chunk received")
                                    break

                            except json.JSONDecodeError as e:
                                print(f"\n⚠️  JSON parse error: {e}")
                                continue

        total_time = time.time() - start_time
        full_content = "".join(content_chunks)

        print("\n" + "=" * 80)
        print("📊 Results:")
        print("=" * 80)
        print(f"✅ Status: SUCCESS")
        print(f"⏱️  First Token Latency: {int((first_token_time - start_time) * 1000)}ms")
        print(f"⏱️  Total Time: {int(total_time * 1000)}ms")
        print(f"📦 Chunks Received: {chunk_count}")
        print(f"📝 Content Length: {len(full_content)} chars")
        print(f"🎯 Tokens Used: {tokens_used}")
        print(f"🏆 Target Achievement: {'🎉 <500ms ACHIEVED' if first_token_time - start_time < 0.5 else '⚠️ Above target'}")

        # Verify we got actual content
        if len(full_content) == 0:
            print(f"\n❌ ISSUE: No content streamed (0 chars)")
            return False
        elif len(full_content) < 10:
            print(f"\n⚠️  WARNING: Very short content ({len(full_content)} chars)")
            print(f"Content: '{full_content}'")
            return False
        else:
            print(f"\n✅ SUCCESS: Content properly streamed ({len(full_content)} chars)")
            return True

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run streaming tests."""
    print("Waiting for server to be ready...")
    await asyncio.sleep(2)

    # Check health
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                print("✅ Server is ready\n")
                health = response.json()
                print("Provider Status:")
                for provider, status in health.get('providers', {}).items():
                    symbol = "✅" if status.get('healthy') else "❌"
                    print(f"  {symbol} {provider}: {'healthy' if status.get('healthy') else 'unhealthy'}")
                print()
            else:
                print(f"⚠️  Server health check returned {response.status_code}\n")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}\n")
        return

    # Test available providers
    tests = [
        ("chatgpt", "What is 2+2? Give a very brief answer."),
        ("local", "What is the capital of France? One word answer only."),
    ]

    results = {}
    for provider, question in tests:
        success = await test_streaming(provider, question)
        results[provider] = success
        print("\n")
        await asyncio.sleep(2)  # Brief pause between tests

    # Summary
    print("=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    for provider, success in results.items():
        symbol = "✅" if success else "❌"
        status = "PASSED" if success else "FAILED"
        print(f"{symbol} {provider.upper()}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Streaming is working!")
    else:
        print("❌ SOME TESTS FAILED - Check results above")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
