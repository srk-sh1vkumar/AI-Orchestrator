#!/usr/bin/env python3
"""Test Claude streaming fix - verify content is properly streamed."""

import asyncio
import httpx
import time
import json


async def test_claude_streaming():
    """Test Claude provider streaming with actual content."""
    print("=" * 80)
    print("Testing Claude Streaming Fix")
    print("=" * 80)

    url = "http://localhost:8000/api/chat/stream"
    request = {
        "message": "@claude: What is the capital of France? Give a brief answer.",
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
                        print(f"⚡ First token latency: {latency_ms}ms")

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
    """Run the test."""
    # Wait for server to be ready
    print("Waiting for server to start...")
    await asyncio.sleep(2)

    # Check health
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                print("✅ Server is ready\n")
            else:
                print(f"⚠️  Server health check returned {response.status_code}\n")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}\n")
        return

    # Run test
    success = await test_claude_streaming()

    print("\n" + "=" * 80)
    if success:
        print("🎉 TEST PASSED - Claude streaming is working!")
    else:
        print("❌ TEST FAILED - Claude streaming issue persists")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
