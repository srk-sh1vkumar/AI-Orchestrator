# Enhancement 008: Streaming Response Support - Analysis

## Current State Analysis

### Existing Architecture

**Base Provider Pattern:**
- `BaseLLMProvider` - Abstract base class
- `_complete_impl()` - Abstract method for providers to implement
- Returns `LLMResponse` - Complete response object
- **Current limitation:** Blocking - waits for full response

**Provider Implementations:**
1. **Claude** (`claude.py`) - Uses `anthropic.Anthropic().messages.create()` synchronously
2. **ChatGPT** (`chatgpt.py`) - Uses OpenAI client
3. **Gemini** (`gemini.py`) - Uses Google GenerativeAI client
4. **Claude Code** (`claude_code.py`) - Direct CLI integration
5. **Local LLM** (`local_llm.py`) - Ollama integration

**Current Flow:**
```
User Request → API → Orchestrator → Provider._complete_impl()
→ Wait for full response → Return complete LLMResponse → Stream to user
```

**Problem:** User waits for entire generation before seeing first token.

---

## Streaming Architecture Design

### New Pattern: AsyncIterator for Streaming

**Updated Base Class:**
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def _complete_impl(...) -> LLMResponse:
        """Non-streaming completion (existing)"""
        pass

    @abstractmethod
    async def _stream_impl(...) -> AsyncIterator[StreamChunk]:
        """NEW: Streaming completion"""
        pass
```

**New Model: StreamChunk**
```python
@dataclass
class StreamChunk:
    """Individual chunk from streaming response."""
    provider: LLMProvider
    content: str  # Delta content
    is_final: bool = False
    tokens_used: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Implementation Strategy

#### Phase 1: Provider-Level Streaming

**1. Claude Provider Streaming:**
```python
async def _stream_impl(self, messages, tools=None, temperature=0.7, max_tokens=4096):
    """Stream Claude responses using async iterator."""
    with self.client.messages.stream(
        model=self.model,
        max_tokens=max_tokens,
        messages=formatted_messages,
        system=system_message
    ) as stream:
        for text in stream.text_stream:
            yield StreamChunk(
                provider=self.provider,
                content=text,
                is_final=False
            )

        # Final chunk with metadata
        final_message = await stream.get_final_message()
        yield StreamChunk(
            provider=self.provider,
            content="",
            is_final=True,
            tokens_used=final_message.usage.output_tokens,
            metadata={"stop_reason": final_message.stop_reason}
        )
```

**2. ChatGPT Provider Streaming:**
```python
async def _stream_impl(self, messages, tools=None, temperature=0.7, max_tokens=None):
    """Stream GPT responses using async iterator."""
    stream = await self.client.chat.completions.create(
        model=self.model,
        messages=formatted_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True  # Enable streaming
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield StreamChunk(
                provider=self.provider,
                content=chunk.choices[0].delta.content,
                is_final=False
            )

    # Final chunk
    yield StreamChunk(
        provider=self.provider,
        content="",
        is_final=True
    )
```

**3. Gemini Provider Streaming:**
```python
async def _stream_impl(self, messages, tools=None, temperature=0.7, max_tokens=None):
    """Stream Gemini responses."""
    response = await self.model.generate_content_async(
        formatted_messages[-1].content,
        stream=True
    )

    async for chunk in response:
        if chunk.text:
            yield StreamChunk(
                provider=self.provider,
                content=chunk.text,
                is_final=False
            )

    yield StreamChunk(
        provider=self.provider,
        content="",
        is_final=True
    )
```

#### Phase 2: API-Level Streaming

**FastAPI Server-Sent Events (SSE):**
```python
from fastapi.responses import StreamingResponse

@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses using SSE."""

    async def event_generator():
        try:
            # Get provider from orchestrator
            provider = await orchestrator.select_provider(request.message)

            # Stream from provider
            async for chunk in provider._stream_impl(
                messages=request.messages,
                temperature=request.temperature
            ):
                # Format as SSE
                yield f"data: {json.dumps(chunk.dict())}\n\n"

        except Exception as e:
            error_data = {"error": str(e), "is_final": True}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

#### Phase 3: Frontend Integration

**JavaScript EventSource API:**
```javascript
const eventSource = new EventSource('/api/chat/stream', {
    method: 'POST',
    body: JSON.stringify({message: userInput, messages: history})
});

let fullResponse = "";

eventSource.onmessage = (event) => {
    const chunk = JSON.parse(event.data);

    if (chunk.error) {
        console.error('Stream error:', chunk.error);
        eventSource.close();
        return;
    }

    if (!chunk.is_final) {
        fullResponse += chunk.content;
        updateUI(fullResponse);  // Update incrementally
    } else {
        // Stream complete
        console.log('Final tokens:', chunk.tokens_used);
        eventSource.close();
    }
};

eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    eventSource.close();
};
```

---

## Success Criteria Implementation

### 1. Streaming works for all providers ✓

**Implementation checklist:**
- [ ] Claude - `anthropic.messages.stream()`
- [ ] ChatGPT - `openai.chat.completions.create(stream=True)`
- [ ] Gemini - `generate_content_async(stream=True)`
- [ ] Fallback handling for non-streaming providers

### 2. First token latency <500ms ✓

**Measurement strategy:**
```python
import time

async def measure_first_token_latency(provider, messages):
    start_time = time.time()
    first_token_received = False

    async for chunk in provider._stream_impl(messages):
        if not first_token_received and chunk.content:
            first_token_time = time.time() - start_time
            print(f"First token latency: {first_token_time*1000:.2f}ms")
            first_token_received = True
```

**Optimization strategies:**
- Use async/await throughout
- Minimize pre-processing
- Stream immediately, don't buffer
- Use connection pooling

### 3. Zero dropped chunks in 1000 requests ✓

**Testing strategy:**
```python
async def test_chunk_delivery():
    """Test that no chunks are dropped."""
    expected_content = "Hello World"  # Known response
    received_content = ""

    async for chunk in provider._stream_impl(test_messages):
        if not chunk.is_final:
            received_content += chunk.content

    assert received_content == expected_content

# Run 1000 times
for i in range(1000):
    await test_chunk_delivery()
```

**Reliability measures:**
- Proper error handling
- Retry logic for transient failures
- Connection keep-alive
- Backpressure handling

---

## Implementation Plan

### Phase 1: Core Streaming (Week 1)
1. Add `StreamChunk` model to schemas
2. Add `_stream_impl()` to base provider
3. Implement Claude streaming
4. Implement ChatGPT streaming
5. Implement Gemini streaming
6. Unit tests for each provider

### Phase 2: API Integration (Week 2)
7. Add `/api/chat/stream` endpoint
8. Implement SSE formatting
9. Add error handling and fallback
10. Integration tests
11. Load testing (1000 concurrent)

### Phase 3: Frontend (Week 3)
12. Add EventSource client
13. Incremental UI updates
14. Error handling UI
15. Reconnection logic
16. End-to-end tests

### Phase 4: Optimization & Monitoring (Week 4)
17. Measure first token latency
18. Add streaming metrics to monitoring
19. Performance optimization
20. Documentation

---

## Technical Considerations

### 1. Async Context Management

**Challenge:** Maintaining async context through streaming
**Solution:** Use `contextlib.asynccontextmanager`

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def streaming_context(provider):
    try:
        yield provider
    finally:
        await provider.cleanup()  # Close streams, connections
```

### 2. Error Handling in Streams

**Challenge:** How to handle errors mid-stream
**Solution:** Send error chunk, close gracefully

```python
try:
    async for chunk in provider._stream_impl(messages):
        yield chunk
except Exception as e:
    yield StreamChunk(
        provider=provider.provider,
        content="",
        is_final=True,
        metadata={"error": str(e)}
    )
```

### 3. Rate Limiting with Streaming

**Challenge:** Rate limiter check before full response
**Solution:** Check before stream starts

```python
async def stream(self, messages, ...):
    if not self.rate_limiter.check_limit(self.provider.value):
        raise RateLimitException()

    async for chunk in self._stream_impl(messages, ...):
        yield chunk
```

### 4. Circuit Breaker with Streaming

**Challenge:** Circuit breaker with partial responses
**Solution:** Wrap stream initiation, not individual chunks

```python
@circuit(failure_threshold=5, expected_exception=ConnectionError)
async def _stream_impl_protected(self, messages, ...):
    async for chunk in self._stream_impl(messages, ...):
        yield chunk
```

### 5. Cost Tracking with Streaming

**Challenge:** Track costs for incomplete streams
**Solution:** Track in final chunk with `tokens_used`

```python
if chunk.is_final and chunk.tokens_used:
    await cost_tracker.record(
        provider=chunk.provider,
        tokens=chunk.tokens_used,
        operation="streaming_completion"
    )
```

---

## API Examples

### Non-Streaming (Existing)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "stream": false}'

# Response (after 2-3 seconds):
{
  "provider": "claude",
  "content": "Hello! How can I help you today?",
  "tokens_used": 15
}
```

### Streaming (New)
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "stream": true}'

# Response (immediate, SSE format):
data: {"provider": "claude", "content": "Hello", "is_final": false}

data: {"provider": "claude", "content": "!", "is_final": false}

data: {"provider": "claude", "content": " How", "is_final": false}

...

data: {"provider": "claude", "content": "", "is_final": true, "tokens_used": 15}
```

---

## Benefits

1. **Better UX** - Users see responses immediately
2. **Lower perceived latency** - First token in <500ms
3. **Progressive rendering** - Long responses feel faster
4. **Modern experience** - Matches ChatGPT, Claude UI
5. **Scalability** - Better resource utilization

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Stream interruption | Medium | High | Retry logic, reconnection |
| Increased server load | Low | Medium | Rate limiting, backpressure |
| Browser compatibility | Low | Low | Fallback to non-streaming |
| Debugging difficulty | Medium | Low | Comprehensive logging |

---

## Metrics to Track

1. **First Token Latency** - p50, p95, p99
2. **Stream Duration** - Average time to completion
3. **Chunk Count** - Average chunks per response
4. **Error Rate** - Streams that fail mid-way
5. **Reconnection Rate** - Client reconnections needed

---

**Status:** Analysis Complete - Ready for Implementation
**Created:** 2025-11-03
**Next Step:** Implement Phase 1 - Core Streaming
