"""Tests for MongoDB database layer."""

import pytest
import pytest_asyncio
from datetime import datetime
from src.database.mongodb import MongoDBManager, get_mongodb_manager
from src.database.repositories import (
    ConversationRepository,
    MessageRepository,
    ToolExecutionRepository,
    ContextEventRepository,
    ProviderMetricRepository,
)
from src.database.models import ConversationMetrics


@pytest.mark.asyncio
async def test_mongodb_connection():
    """Test MongoDB connection and health check."""
    db_manager = await get_mongodb_manager()

    assert db_manager is not None
    assert db_manager.db is not None

    # Test health check
    is_healthy = await db_manager.health_check()
    assert is_healthy is True


@pytest.mark.asyncio
async def test_conversation_repository():
    """Test conversation repository CRUD operations."""
    db_manager = await get_mongodb_manager()
    conv_repo = ConversationRepository(db_manager)

    # Create conversation
    conversation = await conv_repo.create_conversation(
        provider_used="claude_code",
        routing_decision={
            "provider": "claude_code",
            "category": "code_generation",
            "confidence": 0.95,
        },
        title="Test Conversation",
    )

    assert conversation.id is not None
    assert conversation.provider_used == "claude_code"
    assert conversation.title == "Test Conversation"
    assert conversation.status == "active"

    # Get conversation
    retrieved = await conv_repo.get_conversation(str(conversation.id))
    assert retrieved is not None
    assert str(retrieved.id) == str(conversation.id)

    # Update metrics
    metrics = ConversationMetrics(
        message_count=2,
        total_tokens=100,
        total_cost_usd=0.005,
        execution_time_ms=1500,
    )
    updated = await conv_repo.update_conversation_metrics(str(conversation.id), metrics)
    assert updated is True

    # List conversations
    conversations = await conv_repo.list_conversations(limit=10)
    assert len(conversations) > 0


@pytest.mark.asyncio
async def test_message_repository():
    """Test message repository CRUD operations."""
    db_manager = await get_mongodb_manager()
    conv_repo = ConversationRepository(db_manager)
    msg_repo = MessageRepository(db_manager)

    # Create conversation first
    conversation = await conv_repo.create_conversation(
        provider_used="chatgpt",
        routing_decision={"provider": "chatgpt"},
        title="Message Test",
    )

    # Create user message
    user_msg = await msg_repo.create_message(
        conversation_id=str(conversation.id),
        role="user",
        content="Hello, how are you?",
        token_count=5,
    )

    assert user_msg.id is not None
    assert user_msg.role == "user"
    assert user_msg.content == "Hello, how are you?"

    # Create assistant message
    assistant_msg = await msg_repo.create_message(
        conversation_id=str(conversation.id),
        role="assistant",
        content="I'm doing well, thank you!",
        provider="chatgpt",
        model="gpt-4",
        token_count=8,
        cost_usd=0.001,
        metadata={"temperature": 0.7},
    )

    assert assistant_msg.id is not None
    assert assistant_msg.role == "assistant"
    assert assistant_msg.provider == "chatgpt"

    # Get conversation messages
    messages = await msg_repo.get_conversation_messages(str(conversation.id))
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_tool_execution_repository():
    """Test tool execution repository."""
    db_manager = await get_mongodb_manager()
    conv_repo = ConversationRepository(db_manager)
    tool_repo = ToolExecutionRepository(db_manager)

    # Create conversation first
    conversation = await conv_repo.create_conversation(
        provider_used="claude_code",
        routing_decision={"provider": "claude_code"},
        title="Tool Test",
    )

    # Create tool execution
    tool_exec = await tool_repo.create_tool_execution(
        conversation_id=str(conversation.id),
        tool_type="github",
        operation="create_issue",
        success=True,
        execution_time_ms=250,
        result={"issue_number": 123},
    )

    assert tool_exec.id is not None
    assert tool_exec.tool_type == "github"
    assert tool_exec.success is True
    assert tool_exec.execution_time_ms == 250


@pytest.mark.asyncio
async def test_context_event_repository():
    """Test context event repository."""
    db_manager = await get_mongodb_manager()
    conv_repo = ConversationRepository(db_manager)
    context_repo = ContextEventRepository(db_manager)

    # Create conversation first
    conversation = await conv_repo.create_conversation(
        provider_used="claude_code",
        routing_decision={"provider": "claude_code"},
        title="Context Test",
    )

    # Create context event
    event = await context_repo.create_context_event(
        conversation_id=str(conversation.id),
        event_type="check",
        provider="claude_code",
        token_count=1500,
        limit=200000,
        utilization_percent=0.75,
    )

    assert event.id is not None
    assert event.event_type == "check"
    assert event.token_count == 1500

    # Create truncation event
    truncation = await context_repo.create_context_event(
        conversation_id=str(conversation.id),
        event_type="truncation",
        provider="claude_code",
        token_count=180000,
        limit=200000,
        utilization_percent=90.0,
        truncation_strategy="sliding_window",
        messages_removed=5,
    )

    assert truncation.id is not None
    assert truncation.event_type == "truncation"
    assert truncation.messages_removed == 5


@pytest.mark.asyncio
async def test_provider_metric_repository():
    """Test provider metric repository."""
    db_manager = await get_mongodb_manager()
    metric_repo = ProviderMetricRepository(db_manager)

    # Create request metric
    request_metric = await metric_repo.create_metric(
        provider="claude_code",
        metric_type="request",
        value=1.0,
        unit="count",
        metadata={"category": "code_generation"},
    )

    assert request_metric.id is not None
    assert request_metric.provider == "claude_code"
    assert request_metric.metric_type == "request"

    # Create latency metric
    latency_metric = await metric_repo.create_metric(
        provider="chatgpt",
        metric_type="latency",
        value=1.5,
        unit="seconds",
    )

    assert latency_metric.id is not None
    assert latency_metric.value == 1.5

    # Create cost metric
    cost_metric = await metric_repo.create_metric(
        provider="gemini",
        metric_type="cost",
        value=0.025,
        unit="usd",
    )

    assert cost_metric.id is not None
    assert cost_metric.metric_type == "cost"


@pytest.mark.asyncio
async def test_collections_exist():
    """Test that all required collections are created."""
    db_manager = await get_mongodb_manager()

    collections = await db_manager.db.list_collection_names()

    required_collections = [
        "conversations",
        "messages",
        "enhancements",
        "tool_executions",
        "context_events",
        "provider_metrics",
    ]

    for collection in required_collections:
        assert collection in collections, f"Collection {collection} not found"
