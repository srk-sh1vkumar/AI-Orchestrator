"""Test MongoDB connection and basic operations."""

import asyncio
from src.database.mongodb import get_mongodb_manager
from src.database.repositories import (
    ConversationRepository,
    MessageRepository,
)


async def test_mongodb():
    """Test MongoDB connection and operations."""
    print("🔍 Testing MongoDB connection...")

    # Get MongoDB manager
    db_manager = await get_mongodb_manager()

    # Test connection
    is_healthy = await db_manager.health_check()
    print(f"✅ MongoDB health check: {'PASSED' if is_healthy else 'FAILED'}")

    if not is_healthy:
        print("❌ MongoDB is not healthy!")
        return

    # List collections
    collections = await db_manager.db.list_collection_names()
    print(f"📋 Collections: {', '.join(collections)}")

    # Test conversation repository
    print("\n🧪 Testing Conversation Repository...")
    conv_repo = ConversationRepository(db_manager)

    conversation = await conv_repo.create_conversation(
        provider_used="claude_code",
        routing_decision={
            "provider": "claude_code",
            "category": "code_generation",
            "confidence": 0.95,
            "reasoning": "High confidence code generation task",
        },
        title="Test Conversation",
    )
    print(f"✅ Created conversation: {conversation.id}")

    # Test message repository
    print("\n🧪 Testing Message Repository...")
    msg_repo = MessageRepository(db_manager)

    message = await msg_repo.create_message(
        conversation_id=str(conversation.id),
        role="user",
        content="Build a REST API for user authentication",
        token_count=10,
    )
    print(f"✅ Created message: {message.id}")

    response_message = await msg_repo.create_message(
        conversation_id=str(conversation.id),
        role="assistant",
        content="I'll help you build a REST API for user authentication...",
        provider="claude_code",
        model="claude-3.5-sonnet",
        token_count=450,
        cost_usd=0.009,
        metadata={"cached": False},
    )
    print(f"✅ Created response message: {response_message.id}")

    # Retrieve messages
    messages = await msg_repo.get_conversation_messages(str(conversation.id))
    print(f"📨 Retrieved {len(messages)} messages")

    # List conversations
    conversations = await conv_repo.list_conversations(limit=10)
    print(f"📋 Total conversations: {len(conversations)}")

    print("\n✅ All MongoDB tests passed!")


if __name__ == "__main__":
    asyncio.run(test_mongodb())
