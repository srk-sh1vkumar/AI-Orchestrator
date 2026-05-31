"""Archive API endpoints for session history and project archival.

Enhancement 014: Session History & Project Archive System
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timedelta
from bson import ObjectId
import structlog
import csv
import io

from src.database.mongodb import get_mongodb_manager

logger = structlog.get_logger()
router = APIRouter(prefix="/api/archives", tags=["archives"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ArchiveConversationRequest(BaseModel):
    """Request to archive a conversation."""
    archive_reason: Literal["manual", "auto_retention", "project_complete"]
    tags: List[str] = []
    notes: Optional[str] = None


class ArchiveConversationResponse(BaseModel):
    """Response after archiving a conversation."""
    archive_id: str
    original_id: str
    archived_at: datetime
    message: str


class SessionArchiveRequest(BaseModel):
    """Request to create a session archive."""
    session_date: datetime
    session_duration_hours: float
    projects: List[Literal["ai-orchestrator", "ecommerce-microservices", "sre-analytics", "monitoring-hub"]]
    accomplishments: List[str]
    enhancements_completed: List[Dict[str, Any]] = []
    files_created: List[str] = []
    files_modified: List[str] = []
    lines_of_code: int = 0
    blockers: List[str] = []
    next_priorities: List[str] = []
    notes: Optional[str] = None
    conversation_ids: List[str] = []


class SessionArchiveResponse(BaseModel):
    """Response after creating session archive."""
    archive_id: str
    session_date: datetime
    message: str


class ProjectSnapshotRequest(BaseModel):
    """Request to create a project snapshot."""
    project_name: Literal["ai-orchestrator", "ecommerce-microservices", "sre-analytics", "monitoring-hub"]
    archive_type: Literal["milestone", "release", "backup", "experiment"]
    version: Optional[str] = None
    description: str
    enhancements_snapshot: List[Dict[str, Any]] = []
    metrics_snapshot: Dict[str, Any] = {}
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None
    files_snapshot: List[Dict[str, Any]] = []
    tags: List[str] = []
    notes: Optional[str] = None


class ProjectSnapshotResponse(BaseModel):
    """Response after creating project snapshot."""
    archive_id: str
    project_name: str
    snapshot_date: datetime
    message: str


class ArchivedConversation(BaseModel):
    """Archived conversation record."""
    id: str
    original_id: str
    user_id: Optional[str]
    title: Optional[str]
    provider_used: str
    archived_at: datetime
    archive_reason: str
    tags: List[str]
    metrics: Dict[str, Any]


class ArchivedSession(BaseModel):
    """Archived session record."""
    id: str
    session_date: datetime
    session_duration_hours: float
    projects: List[str]
    accomplishments: List[str]
    enhancements_completed: List[Dict[str, Any]]
    lines_of_code: int


class ProjectArchive(BaseModel):
    """Project archive record."""
    id: str
    project_name: str
    archive_type: str
    snapshot_date: datetime
    version: Optional[str]
    description: str
    metrics_snapshot: Dict[str, Any]
    tags: List[str]


# ============================================================================
# Archive Endpoints
# ============================================================================

@router.post("/conversations/{conversation_id}", response_model=ArchiveConversationResponse)
async def archive_conversation(
    conversation_id: str,
    request: ArchiveConversationRequest
) -> ArchiveConversationResponse:
    """Archive a conversation for long-term storage.

    Moves conversation and associated messages to archived_conversations collection.
    """
    try:
        db_manager = await get_mongodb_manager()
        conversations = db_manager.get_collection("conversations")
        messages = db_manager.get_collection("messages")
        archived_conversations = db_manager.get_collection("archived_conversations")

        # Fetch conversation
        conversation_oid = ObjectId(conversation_id)
        conversation = await conversations.find_one({"_id": conversation_oid})

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Fetch all messages for this conversation
        conversation_messages = await messages.find(
            {"conversation_id": conversation_oid}
        ).to_list(length=None)

        # Create archive document
        archive_doc = {
            "original_id": conversation_oid,
            "user_id": conversation.get("user_id"),
            "title": conversation.get("title"),
            "provider_used": conversation["provider_used"],
            "routing_decision": conversation["routing_decision"],
            "messages": [
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "provider": msg.get("provider"),
                    "model": msg.get("model"),
                    "token_count": msg.get("token_count"),
                    "cost_usd": msg.get("cost_usd"),
                    "created_at": msg.get("created_at"),
                }
                for msg in conversation_messages
            ],
            "metrics": conversation.get("metrics", {}),
            "archived_at": datetime.utcnow(),
            "archive_reason": request.archive_reason,
            "tags": request.tags,
            "notes": request.notes,
            "created_at": conversation.get("created_at"),
            "updated_at": conversation.get("updated_at"),
        }

        # Insert into archive
        result = await archived_conversations.insert_one(archive_doc)

        # Update original conversation status
        await conversations.update_one(
            {"_id": conversation_oid},
            {"$set": {"status": "archived", "archived_at": datetime.utcnow()}}
        )

        logger.info(
            "conversation_archived",
            conversation_id=conversation_id,
            archive_id=str(result.inserted_id),
            reason=request.archive_reason
        )

        return ArchiveConversationResponse(
            archive_id=str(result.inserted_id),
            original_id=conversation_id,
            archived_at=archive_doc["archived_at"],
            message=f"Conversation archived successfully ({request.archive_reason})"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("archive_conversation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to archive conversation: {str(e)}")


@router.post("/sessions", response_model=SessionArchiveResponse)
async def create_session_archive(
    request: SessionArchiveRequest
) -> SessionArchiveResponse:
    """Create a session archive for project work completed.

    Records accomplishments, enhancements completed, files changed, and metrics.
    """
    try:
        db_manager = await get_mongodb_manager()
        archived_sessions = db_manager.get_collection("archived_sessions")

        # Convert conversation IDs to ObjectId
        conversation_oids = [
            ObjectId(cid) for cid in request.conversation_ids
            if ObjectId.is_valid(cid)
        ]

        # Create session archive document
        archive_doc = {
            "session_date": request.session_date,
            "session_duration_hours": request.session_duration_hours,
            "projects": request.projects,
            "accomplishments": request.accomplishments,
            "enhancements_completed": request.enhancements_completed,
            "files_created": request.files_created,
            "files_modified": request.files_modified,
            "lines_of_code": request.lines_of_code,
            "blockers": request.blockers,
            "next_priorities": request.next_priorities,
            "notes": request.notes,
            "conversation_ids": conversation_oids,
            "created_at": datetime.utcnow(),
        }

        result = await archived_sessions.insert_one(archive_doc)

        logger.info(
            "session_archived",
            archive_id=str(result.inserted_id),
            projects=request.projects,
            enhancements_count=len(request.enhancements_completed)
        )

        return SessionArchiveResponse(
            archive_id=str(result.inserted_id),
            session_date=request.session_date,
            message=f"Session archive created for {len(request.projects)} project(s)"
        )

    except Exception as e:
        logger.error("create_session_archive_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create session archive: {str(e)}")


@router.post("/projects", response_model=ProjectSnapshotResponse)
async def create_project_snapshot(
    request: ProjectSnapshotRequest
) -> ProjectSnapshotResponse:
    """Create a project snapshot for milestones, releases, or backups.

    Captures project state including enhancements, metrics, git commit, and files.
    """
    try:
        db_manager = await get_mongodb_manager()
        project_archives = db_manager.get_collection("project_archives")

        # Create snapshot document
        snapshot_doc = {
            "project_name": request.project_name,
            "archive_type": request.archive_type,
            "snapshot_date": datetime.utcnow(),
            "version": request.version,
            "description": request.description,
            "enhancements_snapshot": request.enhancements_snapshot,
            "metrics_snapshot": request.metrics_snapshot,
            "git_commit": request.git_commit,
            "git_branch": request.git_branch,
            "files_snapshot": request.files_snapshot,
            "tags": request.tags,
            "notes": request.notes,
            "created_at": datetime.utcnow(),
        }

        result = await project_archives.insert_one(snapshot_doc)

        logger.info(
            "project_snapshot_created",
            archive_id=str(result.inserted_id),
            project=request.project_name,
            type=request.archive_type,
            version=request.version
        )

        return ProjectSnapshotResponse(
            archive_id=str(result.inserted_id),
            project_name=request.project_name,
            snapshot_date=snapshot_doc["snapshot_date"],
            message=f"{request.archive_type.capitalize()} snapshot created for {request.project_name}"
        )

    except Exception as e:
        logger.error("create_project_snapshot_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create project snapshot: {str(e)}")


# ============================================================================
# List and Retrieve Endpoints
# ============================================================================

@router.get("/conversations")
async def list_archived_conversations(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    archive_reason: Optional[str] = None,
    tags: Optional[str] = None
) -> Dict[str, Any]:
    """List archived conversations with optional filtering."""
    try:
        db_manager = await get_mongodb_manager()
        archived_conversations = db_manager.get_collection("archived_conversations")

        # Build query
        query = {}
        if archive_reason:
            query["archive_reason"] = archive_reason
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            query["tags"] = {"$in": tag_list}

        # Get total count
        total = await archived_conversations.count_documents(query)

        # Fetch archived conversations
        cursor = archived_conversations.find(query).sort("archived_at", -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)

        # Convert to response model
        conversations = [
            {
                "id": str(doc["_id"]),
                "original_id": str(doc["original_id"]),
                "user_id": doc.get("user_id"),
                "title": doc.get("title"),
                "provider_used": doc["provider_used"],
                "archived_at": doc["archived_at"].isoformat() if doc.get("archived_at") else None,
                "archive_reason": doc["archive_reason"],
                "tags": doc.get("tags", []),
                "metrics": doc.get("metrics", {})
            }
            for doc in results
        ]

        return {
            "conversations": conversations,
            "total": total,
            "limit": limit,
            "skip": skip
        }

    except Exception as e:
        logger.error("list_archived_conversations_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list archived conversations: {str(e)}")


@router.get("/sessions")
async def list_archived_sessions(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    project: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """List archived sessions with optional filtering."""
    try:
        db_manager = await get_mongodb_manager()
        archived_sessions = db_manager.get_collection("archived_sessions")

        # Build query
        query = {}
        if project:
            query["projects"] = project
        if start_date or end_date:
            query["session_date"] = {}
            if start_date:
                query["session_date"]["$gte"] = start_date
            if end_date:
                query["session_date"]["$lte"] = end_date

        # Get total count
        total = await archived_sessions.count_documents(query)

        # Fetch archived sessions
        cursor = archived_sessions.find(query).sort("session_date", -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)

        # Convert to response model
        sessions = [
            {
                "id": str(doc["_id"]),
                "session_date": doc["session_date"].isoformat() if doc.get("session_date") else None,
                "session_duration_hours": doc["session_duration_hours"],
                "projects": doc["projects"],
                "accomplishments": doc["accomplishments"],
                "enhancements_completed": doc.get("enhancements_completed", []),
                "lines_of_code": doc.get("lines_of_code", 0)
            }
            for doc in results
        ]

        return {
            "sessions": sessions,
            "total": total,
            "limit": limit,
            "skip": skip
        }

    except Exception as e:
        logger.error("list_archived_sessions_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list archived sessions: {str(e)}")


@router.get("/projects")
async def list_project_archives(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    project_name: Optional[str] = None,
    archive_type: Optional[str] = None,
    tags: Optional[str] = None
) -> Dict[str, Any]:
    """List project archives with optional filtering."""
    try:
        db_manager = await get_mongodb_manager()
        project_archives = db_manager.get_collection("project_archives")

        # Build query
        query = {}
        if project_name:
            query["project_name"] = project_name
        if archive_type:
            query["archive_type"] = archive_type
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            query["tags"] = {"$in": tag_list}

        # Get total count
        total = await project_archives.count_documents(query)

        # Fetch project archives
        cursor = project_archives.find(query).sort("snapshot_date", -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)

        # Convert to response model
        projects = [
            {
                "id": str(doc["_id"]),
                "project_name": doc["project_name"],
                "archive_type": doc["archive_type"],
                "snapshot_date": doc["snapshot_date"].isoformat() if doc.get("snapshot_date") else None,
                "version": doc.get("version"),
                "description": doc["description"],
                "metrics_snapshot": doc.get("metrics_snapshot", {}),
                "tags": doc.get("tags", [])
            }
            for doc in results
        ]

        return {
            "projects": projects,
            "total": total,
            "limit": limit,
            "skip": skip
        }

    except Exception as e:
        logger.error("list_project_archives_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list project archives: {str(e)}")


# ============================================================================
# Search Endpoint
# ============================================================================

@router.get("/search")
async def search_archives(
    q: str = Query(..., min_length=3, description="Search query"),
    collection: Optional[Literal["conversations", "sessions", "projects"]] = None,
    limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """Full-text search across all archive collections."""
    try:
        db_manager = await get_mongodb_manager()

        results = {
            "query": q,
            "conversations": [],
            "sessions": [],
            "projects": []
        }

        # Search archived conversations
        if collection is None or collection == "conversations":
            archived_conversations = db_manager.get_collection("archived_conversations")
            conv_cursor = archived_conversations.find(
                {"$text": {"$search": q}}
            ).limit(limit)
            conv_results = await conv_cursor.to_list(length=limit)
            results["conversations"] = [
                {
                    "id": str(doc["_id"]),
                    "title": doc.get("title"),
                    "archived_at": doc["archived_at"].isoformat(),
                    "tags": doc.get("tags", []),
                    "score": doc.get("score", 0)
                }
                for doc in conv_results
            ]

        # Search archived sessions
        if collection is None or collection == "sessions":
            archived_sessions = db_manager.get_collection("archived_sessions")
            session_cursor = archived_sessions.find(
                {"$text": {"$search": q}}
            ).limit(limit)
            session_results = await session_cursor.to_list(length=limit)
            results["sessions"] = [
                {
                    "id": str(doc["_id"]),
                    "session_date": doc["session_date"].isoformat(),
                    "projects": doc["projects"],
                    "accomplishments": doc["accomplishments"][:3],  # Preview
                    "score": doc.get("score", 0)
                }
                for doc in session_results
            ]

        # Search project archives
        if collection is None or collection == "projects":
            project_archives = db_manager.get_collection("project_archives")
            project_cursor = project_archives.find(
                {"$text": {"$search": q}}
            ).limit(limit)
            project_results = await project_cursor.to_list(length=limit)
            results["projects"] = [
                {
                    "id": str(doc["_id"]),
                    "project_name": doc["project_name"],
                    "description": doc["description"],
                    "snapshot_date": doc["snapshot_date"].isoformat(),
                    "version": doc.get("version"),
                    "score": doc.get("score", 0)
                }
                for doc in project_results
            ]

        total_results = len(results["conversations"]) + len(results["sessions"]) + len(results["projects"])
        results["total_results"] = total_results

        logger.info("archive_search", query=q, total_results=total_results)

        return results

    except Exception as e:
        logger.error("search_archives_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ============================================================================
# Restore Endpoint
# ============================================================================

@router.post("/restore/{archive_id}")
async def restore_conversation(archive_id: str) -> Dict[str, Any]:
    """Restore an archived conversation back to active conversations.

    Note: Only supports conversation restoration currently.
    """
    try:
        db_manager = await get_mongodb_manager()
        archived_conversations = db_manager.get_collection("archived_conversations")
        conversations = db_manager.get_collection("conversations")
        messages = db_manager.get_collection("messages")

        # Fetch archived conversation
        archive_oid = ObjectId(archive_id)
        archive_doc = await archived_conversations.find_one({"_id": archive_oid})

        if not archive_doc:
            raise HTTPException(status_code=404, detail="Archive not found")

        # Restore conversation
        conversation_doc = {
            "user_id": archive_doc.get("user_id"),
            "title": archive_doc.get("title"),
            "provider_used": archive_doc["provider_used"],
            "routing_decision": archive_doc["routing_decision"],
            "status": "active",
            "metrics": archive_doc.get("metrics", {}),
            "created_at": archive_doc.get("created_at", datetime.utcnow()),
            "updated_at": datetime.utcnow(),
            "restored_from": archive_oid,
            "restored_at": datetime.utcnow(),
        }

        conv_result = await conversations.insert_one(conversation_doc)
        conversation_id = conv_result.inserted_id

        # Restore messages
        restored_messages = []
        for msg in archive_doc.get("messages", []):
            message_doc = {
                "conversation_id": conversation_id,
                "role": msg["role"],
                "content": msg["content"],
                "provider": msg.get("provider"),
                "model": msg.get("model"),
                "token_count": msg.get("token_count"),
                "cost_usd": msg.get("cost_usd"),
                "created_at": msg.get("created_at", datetime.utcnow()),
            }
            msg_result = await messages.insert_one(message_doc)
            restored_messages.append(str(msg_result.inserted_id))

        logger.info(
            "conversation_restored",
            archive_id=archive_id,
            conversation_id=str(conversation_id),
            message_count=len(restored_messages)
        )

        return {
            "message": "Conversation restored successfully",
            "conversation_id": str(conversation_id),
            "messages_restored": len(restored_messages)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("restore_conversation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


# ============================================================================
# Export Endpoint
# ============================================================================

@router.get("/export")
async def export_archives(
    collection: Literal["conversations", "sessions", "projects"],
    format: Literal["json", "csv"] = "json",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Export archive data in JSON or CSV format."""
    try:
        db_manager = await get_mongodb_manager()

        # Determine collection and date field
        if collection == "conversations":
            coll = db_manager.get_collection("archived_conversations")
            date_field = "archived_at"
        elif collection == "sessions":
            coll = db_manager.get_collection("archived_sessions")
            date_field = "session_date"
        else:  # projects
            coll = db_manager.get_collection("project_archives")
            date_field = "snapshot_date"

        # Build query
        query = {}
        if start_date or end_date:
            query[date_field] = {}
            if start_date:
                query[date_field]["$gte"] = start_date
            if end_date:
                query[date_field]["$lte"] = end_date

        # Fetch data
        cursor = coll.find(query).limit(1000)  # Safety limit
        results = await cursor.to_list(length=1000)

        # Convert ObjectId to string for JSON serialization
        for doc in results:
            doc["_id"] = str(doc["_id"])
            if "original_id" in doc:
                doc["original_id"] = str(doc["original_id"])
            if "conversation_ids" in doc:
                doc["conversation_ids"] = [str(cid) for cid in doc["conversation_ids"]]

        if format == "json":
            return {
                "collection": collection,
                "count": len(results),
                "data": results
            }
        else:  # CSV
            # Generate CSV
            if not results:
                return {"message": "No data to export"}

            output = io.StringIO()

            # Flatten nested structures for CSV
            flat_results = []
            for doc in results:
                flat_doc = {}
                for key, value in doc.items():
                    if isinstance(value, (list, dict)):
                        flat_doc[key] = str(value)
                    elif isinstance(value, datetime):
                        flat_doc[key] = value.isoformat()
                    else:
                        flat_doc[key] = value
                flat_results.append(flat_doc)

            if flat_results:
                writer = csv.DictWriter(output, fieldnames=flat_results[0].keys())
                writer.writeheader()
                writer.writerows(flat_results)

            csv_data = output.getvalue()
            output.close()

            return {
                "collection": collection,
                "count": len(results),
                "format": "csv",
                "data": csv_data
            }

    except Exception as e:
        logger.error("export_archives_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ============================================================================
# Statistics Endpoint
# ============================================================================

@router.get("/stats")
async def get_archive_statistics() -> Dict[str, Any]:
    """Get statistics about archived data."""
    try:
        db_manager = await get_mongodb_manager()

        # Count documents in each collection
        conversations_count = await db_manager.get_collection("archived_conversations").count_documents({})
        sessions_count = await db_manager.get_collection("archived_sessions").count_documents({})
        projects_count = await db_manager.get_collection("project_archives").count_documents({})

        # Get recent archives
        recent_conversations = await db_manager.get_collection("archived_conversations").find().sort("archived_at", -1).limit(5).to_list(length=5)
        recent_sessions = await db_manager.get_collection("archived_sessions").find().sort("session_date", -1).limit(5).to_list(length=5)

        return {
            "total_archived_conversations": conversations_count,
            "total_archived_sessions": sessions_count,
            "total_project_snapshots": projects_count,
            "recent_conversations": [
                {
                    "id": str(doc["_id"]),
                    "title": doc.get("title"),
                    "archived_at": doc["archived_at"].isoformat()
                }
                for doc in recent_conversations
            ],
            "recent_sessions": [
                {
                    "id": str(doc["_id"]),
                    "session_date": doc["session_date"].isoformat(),
                    "projects": doc["projects"]
                }
                for doc in recent_sessions
            ]
        }

    except Exception as e:
        logger.error("get_archive_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
