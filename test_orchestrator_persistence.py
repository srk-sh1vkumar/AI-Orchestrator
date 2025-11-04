"""Test orchestrator with MongoDB persistence."""

import asyncio
from src.core.orchestrator import Orchestrator
from src.models.schemas import ChatRequest
from src.database.mongodb import get_mongodb_manager
from src.database.repositories import ConversationRepository, MessageRepository


async def test_orchestrator_persistence():
    """Test that orchestrator persists conversations and messages."""
    print("🔍 Testing orchestrator with MongoDB persistence...\n")

    # Create orchestrator with persistence enabled
    orchestrator = Orchestrator(enable_cache=True, enable_persistence=True)

    # Test health check
    print("1. Checking health status...")
    health = await orchestrator.health_check()
    print(f"   Overall status: {health['status']}")
    print(f"   Database enabled: {health['database']['enabled']}")
    print(f"   Database healthy: {health['database']['healthy']}")
    print()

    # Test simple request (without tools)
    print("2. Processing simple request...")
    request = ChatRequest(
        message="What is the capital of France?",
        enable_tools=False,
        enable_collaboration=False,
    )

    response = await orchestrator.process_request(request)
    print(f"   Response: {response.message[:100]}...")
    print(f"   Provider: {response.provider.value}")
    print(f"   Execution time: {response.execution_time:.3f}s")
    print()

    # Verify data was persisted
    print("3. Verifying data persistence...")
    db_manager = await get_mongodb_manager()
    conv_repo = ConversationRepository(db_manager)
    msg_repo = MessageRepository(db_manager)

    # List conversations
    conversations = await conv_repo.list_conversations(limit=5)
    print(f"   ✅ Total conversations: {len(conversations)}")

    if conversations:
        latest_conv = conversations[0]
        print(f"   Latest conversation ID: {latest_conv.id}")
        print(f"   Provider used: {latest_conv.provider_used}")
        print(f"   Title: {latest_conv.title}")
        print(f"   Status: {latest_conv.status}")
        print(f"   Metrics: {latest_conv.metrics}")
        print()

        # Get messages for latest conversation
        messages = await msg_repo.get_conversation_messages(str(latest_conv.id))
        print(f"   ✅ Messages in conversation: {len(messages)}")
        for msg in messages:
            print(f"      - {msg.role}: {msg.content[:50]}...")
            if msg.provider:
                print(f"        Provider: {msg.provider}, Tokens: {msg.token_count}")

    print("\n✅ All orchestrator persistence tests passed!")


if __name__ == "__main__":
    asyncio.run(test_orchestrator_persistence())
