"""API router for conversation management endpoints.

Enhancement 019: API Router Refactoring.
"""

from fastapi import APIRouter, HTTPException
import structlog

from src.models.schemas import ChatRequest
from src.api.dependencies import get_orchestrator

logger = structlog.get_logger()
router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    user_id: str | None = None,
    status: str | None = None,
    search: str | None = None,  # Enhancement 022: Full-text search
    tags: str | None = None,  # Enhancement 022: Filter by tags (comma-separated)
    provider: str | None = None,  # Enhancement 022: Filter by provider
    sort_by: str = "created_at",  # Enhancement 022: Sort field
    sort_order: str = "desc",  # Enhancement 022: Sort order (asc/desc)
    limit: int = 50,
    skip: int = 0,
):
    """List conversations with optional filters and search.

    Enhancement 022: Added full-text search, tag filtering, provider filtering, and sorting.

    Args:
        user_id: Filter by user ID
        status: Filter by status (active/archived/deleted)
        search: Full-text search in title and messages
        tags: Filter by tags (comma-separated, e.g., "work,debug")
        provider: Filter by provider
        sort_by: Sort field (created_at, updated_at, total_cost_usd)
        sort_order: Sort order (asc/desc)
        limit: Maximum results (default: 50)
        skip: Skip results (default: 0)

    Returns:
        List of conversations with search/filter applied
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)

        # Build filter query
        query_filter = {}
        if user_id:
            query_filter["user_id"] = user_id
        if status:
            query_filter["status"] = status
        if provider:
            query_filter["provider_used"] = provider
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            query_filter["tags"] = {"$in": tag_list}
        if search:
            # Full-text search in title (MongoDB regex search)
            query_filter["title"] = {"$regex": search, "$options": "i"}

        # Build sort criteria
        sort_direction = 1 if sort_order == "asc" else -1
        sort_criteria = [(sort_by, sort_direction)]

        # Query conversations
        conversations = await conv_repo.list_conversations_advanced(
            query_filter=query_filter,
            sort_criteria=sort_criteria,
            limit=limit,
            skip=skip,
        )

        return {
            "conversations": [
                {
                    "id": str(conv.id),
                    "title": conv.title,
                    "provider_used": conv.provider_used,
                    "routing_decision": conv.routing_decision,
                    "metrics": {
                        "message_count": conv.metrics.message_count,
                        "total_tokens": conv.metrics.total_tokens,
                        "total_cost_usd": conv.metrics.total_cost_usd,
                        "execution_time_ms": conv.metrics.execution_time_ms,
                    },
                    "status": conv.status,
                    "tags": conv.tags,  # Enhancement 022
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                }
                for conv in conversations
            ],
            "total": len(conversations),
            "filters_applied": {
                "search": search,
                "tags": tags,
                "provider": provider,
                "status": status,
            },
        }
    except Exception as e:
        logger.error("list_conversations_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation by ID.

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation details
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)

        conversation = await conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "provider_used": conversation.provider_used,
            "routing_decision": conversation.routing_decision,
            "metrics": {
                "message_count": conversation.metrics.message_count,
                "total_tokens": conversation.metrics.total_tokens,
                "total_cost_usd": conversation.metrics.total_cost_usd,
                "execution_time_ms": conversation.metrics.execution_time_ms,
            },
            "status": conversation.status,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_conversation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int | None = None):
    """Get messages for a conversation.

    Args:
        conversation_id: Conversation ID
        limit: Optional limit

    Returns:
        List of messages
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import MessageRepository

        db_manager = await get_mongodb_manager()
        msg_repo = MessageRepository(db_manager)

        messages = await msg_repo.get_conversation_messages(
            conversation_id, limit=limit
        )

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "provider": msg.provider,
                    "model": msg.model,
                    "token_count": msg.token_count,
                    "cost_usd": msg.cost_usd,
                    "metadata": msg.metadata,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
            "total": len(messages),
        }
    except Exception as e:
        logger.error("get_conversation_messages_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/resume")
async def resume_conversation(conversation_id: str, request: ChatRequest):
    """Resume an existing conversation by loading its history.

    Args:
        conversation_id: ID of the conversation to resume
        request: Chat request with new message

    Returns:
        Chat response with conversation context loaded
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository, MessageRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)
        msg_repo = MessageRepository(db_manager)

        # Verify conversation exists
        conversation = await conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Load conversation messages for context
        messages = await msg_repo.get_conversation_messages(conversation_id)

        # Build context from conversation history
        context = request.context or {}
        context["conversation_id"] = conversation_id
        context["conversation_history"] = [
            {
                "role": msg.role,
                "content": msg.content,
                "provider": msg.provider,
            }
            for msg in messages
        ]
        context["conversation_metadata"] = {
            "title": conversation.title,
            "provider_used": conversation.provider_used,
            "message_count": conversation.metrics.message_count,
            "total_tokens": conversation.metrics.total_tokens,
        }

        # Create updated request with conversation context
        updated_request = ChatRequest(
            message=request.message,
            context=context,
            explicit_provider=request.explicit_provider,
            session_id=conversation_id,  # Use conversation_id as session_id
            enable_tools=request.enable_tools,
            enable_collaboration=request.enable_collaboration,
        )

        # Process the request with the orchestrator
        orchestrator = get_orchestrator()
        response = await orchestrator.process_request(updated_request)

        logger.info(
            "conversation_resumed",
            conversation_id=conversation_id,
            message_count=len(messages),
        )

        return {
            "response": response.message,
            "provider": response.provider.value,
            "conversation_id": conversation_id,
            "conversation_context": {
                "previous_messages": len(messages),
                "total_tokens": conversation.metrics.total_tokens,
                "total_cost_usd": conversation.metrics.total_cost_usd,
            },
            "routing_decision": {
                "provider": response.routing_decision.provider.value,
                "category": response.routing_decision.category.value,
                "confidence": response.routing_decision.confidence,
                "reasoning": response.routing_decision.reasoning,
            },
            "execution_time": response.execution_time,
            "timestamp": response.timestamp.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("resume_conversation_failed", error=str(e), conversation_id=conversation_id)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Enhancement 022: Tag Management Endpoints
# ============================================================================


@router.post("/{conversation_id}/tags")
async def add_conversation_tags(conversation_id: str, tags: list[str]):
    """Add tags to a conversation.

    Enhancement 022: Conversation tagging for organization.

    Args:
        conversation_id: Conversation ID
        tags: List of tags to add

    Returns:
        Updated conversation with tags
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)

        # Get conversation
        conversation = await conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Add new tags (avoid duplicates)
        existing_tags = set(conversation.tags)
        new_tags = existing_tags.union(set(tags))

        # Update conversation
        await conv_repo.update_conversation_tags(conversation_id, list(new_tags))

        logger.info(
            "conversation_tags_added",
            conversation_id=conversation_id,
            tags_added=tags,
            total_tags=len(new_tags),
        )

        return {
            "conversation_id": conversation_id,
            "tags": list(new_tags),
            "tags_added": tags,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("add_conversation_tags_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}/tags")
async def remove_conversation_tags(conversation_id: str, tags: list[str]):
    """Remove tags from a conversation.

    Enhancement 022: Tag management.

    Args:
        conversation_id: Conversation ID
        tags: List of tags to remove

    Returns:
        Updated conversation with remaining tags
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)

        # Get conversation
        conversation = await conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Remove specified tags
        remaining_tags = [t for t in conversation.tags if t not in tags]

        # Update conversation
        await conv_repo.update_conversation_tags(conversation_id, remaining_tags)

        logger.info(
            "conversation_tags_removed",
            conversation_id=conversation_id,
            tags_removed=tags,
            remaining_tags=len(remaining_tags),
        )

        return {
            "conversation_id": conversation_id,
            "tags": remaining_tags,
            "tags_removed": tags,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("remove_conversation_tags_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/list")
async def list_all_tags(user_id: str | None = None):
    """Get all unique tags across conversations.

    Enhancement 022: Tag autocomplete support.

    Args:
        user_id: Optional filter by user ID

    Returns:
        List of all unique tags with usage counts
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)

        # Get all tags
        all_tags = await conv_repo.get_all_tags(user_id=user_id)

        return {
            "tags": all_tags,
            "total": len(all_tags),
        }
    except Exception as e:
        logger.error("list_all_tags_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Enhancement 022: Export Endpoints
# ============================================================================


@router.get("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    format: str = "markdown",  # markdown, json, pdf
):
    """Export conversation in specified format.

    Enhancement 022: Conversation export functionality.

    Args:
        conversation_id: Conversation ID
        format: Export format (markdown, json, pdf)

    Returns:
        Exported conversation content
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository, MessageRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)
        msg_repo = MessageRepository(db_manager)

        # Get conversation and messages
        conversation = await conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = await msg_repo.get_conversation_messages(conversation_id)

        # Export based on format
        if format == "markdown":
            content = _export_to_markdown(conversation, messages)
            media_type = "text/markdown"
            filename = f"conversation_{conversation_id}.md"
        elif format == "json":
            content = _export_to_json(conversation, messages)
            media_type = "application/json"
            filename = f"conversation_{conversation_id}.json"
        elif format == "pdf":
            # For PDF, we'll return HTML that can be converted client-side
            # or use a library like WeasyPrint/ReportLab
            content = _export_to_html(conversation, messages)
            media_type = "text/html"
            filename = f"conversation_{conversation_id}.html"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        from fastapi.responses import Response

        logger.info(
            "conversation_exported",
            conversation_id=conversation_id,
            format=format,
            message_count=len(messages),
        )

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("export_conversation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export Helper Functions
# ============================================================================


def _export_to_markdown(conversation, messages):
    """Export conversation to Markdown format."""
    import json

    output = f"# {conversation.title or 'Untitled Conversation'}\n\n"
    output += f"**Provider:** {conversation.provider_used}\n"
    output += f"**Status:** {conversation.status}\n"
    if conversation.tags:
        output += f"**Tags:** {', '.join(conversation.tags)}\n"
    output += f"**Created:** {conversation.created_at.isoformat()}\n"
    output += f"**Messages:** {conversation.metrics.message_count}\n"
    output += f"**Total Cost:** ${conversation.metrics.total_cost_usd:.4f}\n"
    output += f"**Total Tokens:** {conversation.metrics.total_tokens:,}\n\n"
    output += "---\n\n"

    for msg in messages:
        role = msg.role.upper()
        output += f"## {role}\n\n"
        output += f"{msg.content}\n\n"

        if msg.provider:
            output += f"*Provider: {msg.provider}*  \n"
        if msg.token_count:
            output += f"*Tokens: {msg.token_count}*  \n"
        if msg.cost_usd:
            output += f"*Cost: ${msg.cost_usd:.4f}*  \n"
        output += "\n---\n\n"

    return output.encode("utf-8")


def _export_to_json(conversation, messages):
    """Export conversation to JSON format."""
    import json

    data = {
        "conversation": {
            "id": str(conversation.id),
            "title": conversation.title,
            "provider_used": conversation.provider_used,
            "status": conversation.status,
            "tags": conversation.tags,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "metrics": {
                "message_count": conversation.metrics.message_count,
                "total_tokens": conversation.metrics.total_tokens,
                "total_cost_usd": conversation.metrics.total_cost_usd,
                "execution_time_ms": conversation.metrics.execution_time_ms,
            },
            "routing_decision": conversation.routing_decision,
        },
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "provider": msg.provider,
                "model": msg.model,
                "token_count": msg.token_count,
                "cost_usd": msg.cost_usd,
                "metadata": msg.metadata,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ],
    }

    return json.dumps(data, indent=2).encode("utf-8")


def _export_to_html(conversation, messages):
    """Export conversation to HTML format (for PDF conversion)."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{conversation.title or 'Conversation Export'}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .metadata {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .message {{ margin-bottom: 30px; padding: 15px; border-left: 4px solid #4CAF50; background: #f9f9f9; }}
        .user {{ border-left-color: #2196F3; }}
        .assistant {{ border-left-color: #4CAF50; }}
        .role {{ font-weight: bold; color: #333; margin-bottom: 10px; }}
        .content {{ white-space: pre-wrap; }}
        .meta {{ font-size: 0.9em; color: #666; margin-top: 10px; }}
        code {{ background: #e0e0e0; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>{conversation.title or 'Untitled Conversation'}</h1>

    <div class="metadata">
        <strong>Provider:</strong> {conversation.provider_used}<br>
        <strong>Status:</strong> {conversation.status}<br>
        <strong>Tags:</strong> {', '.join(conversation.tags) if conversation.tags else 'None'}<br>
        <strong>Created:</strong> {conversation.created_at.isoformat()}<br>
        <strong>Total Cost:</strong> ${conversation.metrics.total_cost_usd:.4f}<br>
        <strong>Total Tokens:</strong> {conversation.metrics.total_tokens:,}<br>
        <strong>Messages:</strong> {conversation.metrics.message_count}
    </div>

    <hr>
"""

    for msg in messages:
        css_class = msg.role.lower()
        html += f"""
    <div class="message {css_class}">
        <div class="role">{msg.role.upper()}</div>
        <div class="content">{msg.content}</div>
        <div class="meta">
"""
        if msg.provider:
            html += f"Provider: {msg.provider} | "
        if msg.token_count:
            html += f"Tokens: {msg.token_count} | "
        if msg.cost_usd:
            html += f"Cost: ${msg.cost_usd:.4f}"

        html += """
        </div>
    </div>
"""

    html += """
</body>
</html>
"""

    return html.encode("utf-8")
