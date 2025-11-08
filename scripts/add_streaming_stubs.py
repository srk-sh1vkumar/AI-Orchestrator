#!/usr/bin/env python3
"""Add streaming stub implementations to providers that don't have them."""

import re

PROVIDERS_TO_UPDATE = [
    "src/providers/local_llm.py",
    "src/providers/claude_code.py",
    "src/providers/mistral.py",
    "src/providers/llama2.py",
    "src/providers/codellama.py",
]

STREAMING_STUB = '''
    async def _stream_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion using fallback implementation.

        This provider uses the fallback streaming which calls the blocking API
        and simulates streaming by chunking the response.

        Args:
            messages: Conversation messages
            tools: Available tools
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            StreamChunk: Simulated incremental response chunks
        """
        async for chunk in self._stream_impl_fallback(messages, tools, temperature, max_tokens):
            yield chunk
'''

def add_streaming_to_provider(filepath: str):
    """Add streaming implementation to a provider file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Check if already has _stream_impl
    if '_stream_impl' in content:
        print(f"  ✓ {filepath} already has streaming")
        return False

    # Update imports to include AsyncIterator and StreamChunk
    if 'AsyncIterator' not in content:
        content = re.sub(
            r'from typing import ([^\n]+)',
            r'from typing import \1, AsyncIterator',
            content
        )

    if 'StreamChunk' not in content:
        content = re.sub(
            r'from src\.models\.schemas import ([^\n]+)',
            r'from src.models.schemas import \1, StreamChunk',
            content
        )

    # Find the last method before the end of the class
    # Insert streaming stub before health_check if it exists
    if 'async def health_check' in content:
        content = content.replace(
            '    async def health_check',
            STREAMING_STUB + '\n    async def health_check'
        )
    else:
        # Find the last method and insert before the end of the class
        # Look for the last occurrence of a method
        pattern = r'(\n    def [^(]+\([^)]*\)[^:]*:\n(?:        [^\n]*\n)+)'
        matches = list(re.finditer(pattern, content))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            content = content[:insert_pos] + '\n' + STREAMING_STUB + '\n' + content[insert_pos:]

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"  ✓ Added streaming to {filepath}")
    return True

def main():
    """Main function."""
    print("Adding streaming stub implementations...")
    print()

    updated_count = 0
    for provider_file in PROVIDERS_TO_UPDATE:
        try:
            if add_streaming_to_provider(provider_file):
                updated_count += 1
        except Exception as e:
            print(f"  ✗ Error updating {provider_file}: {e}")

    print()
    print(f"Updated {updated_count} provider(s)")

if __name__ == "__main__":
    main()
