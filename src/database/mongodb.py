"""MongoDB connection manager and database layer.

This module provides async MongoDB connections using Motor and manages
database collections for the AI Orchestrator.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
import structlog

from src.core.config import settings

logger = structlog.get_logger()


class MongoDBManager:
    """MongoDB connection and collection manager."""

    def __init__(
        self,
        mongodb_url: Optional[str] = None,
        database_name: str = "ai_orchestrator",
    ):
        """Initialize MongoDB manager.

        Args:
            mongodb_url: MongoDB connection URL (default: from settings)
            database_name: Database name (default: ai_orchestrator)
        """
        self.logger = logger.bind(component="mongodb_manager")
        self.mongodb_url = mongodb_url or getattr(
            settings, "mongodb_url", "mongodb://localhost:27017"
        )
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Connect to MongoDB and initialize database."""
        try:
            self.logger.info("connecting_to_mongodb", url=self.mongodb_url)
            self.client = AsyncIOMotorClient(self.mongodb_url)

            # Test connection
            await self.client.admin.command("ping")

            self.db = self.client[self.database_name]
            self.logger.info(
                "mongodb_connected",
                database=self.database_name,
                url=self.mongodb_url,
            )

            # Initialize collections and indexes
            await self._init_collections()

        except Exception as e:
            self.logger.error("mongodb_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.logger.info("mongodb_disconnected")

    async def _init_collections(self) -> None:
        """Initialize collections with schema validation and indexes."""
        await self._init_enhancements_collection()
        await self._init_conversations_collection()
        await self._init_messages_collection()
        await self._init_tool_executions_collection()
        await self._init_context_events_collection()
        await self._init_provider_metrics_collection()
        await self._init_cost_records_collection()
        await self._init_budgets_collection()
        await self._init_budget_alerts_collection()

    async def _init_enhancements_collection(self) -> None:
        """Initialize enhancements collection with validation and indexes."""
        collection_name = "enhancements"

        # Schema validation
        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["yaml_id", "project_tag", "title", "status", "priority"],
                "properties": {
                    "yaml_id": {"bsonType": "string"},
                    "project_tag": {"bsonType": "string"},
                    "title": {"bsonType": "string"},
                    "category": {"bsonType": "string"},
                    "priority": {
                        "enum": ["High", "Medium", "Low"],
                    },
                    "status": {
                        "enum": [
                            "Ideation",
                            "Definition",
                            "Design",
                            "Implementation",
                            "Reflection",
                            "Integration",
                            "Complete",
                        ],
                    },
                    "completion_percentage": {
                        "bsonType": "int",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "estimated_hours": {"bsonType": ["double", "null"]},
                    "actual_hours": {"bsonType": ["double", "null"]},
                },
            }
        }

        # Create collection with validation if it doesn't exist
        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        # Create indexes
        collection = self.db[collection_name]
        await collection.create_index(
            [("yaml_id", ASCENDING)], unique=True, name="idx_yaml_id"
        )
        await collection.create_index(
            [("project_tag", ASCENDING)], name="idx_project_tag"
        )
        await collection.create_index([("status", ASCENDING)], name="idx_status")
        await collection.create_index([("priority", ASCENDING)], name="idx_priority")
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )

        self.logger.info("collection_initialized", collection=collection_name)

    async def _init_conversations_collection(self) -> None:
        """Initialize conversations collection with validation and indexes."""
        collection_name = "conversations"

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["provider_used", "routing_decision"],
                "properties": {
                    "user_id": {"bsonType": ["string", "null"]},
                    "title": {"bsonType": ["string", "null"]},
                    "provider_used": {"bsonType": "string"},
                    "routing_decision": {"bsonType": "object"},
                    "status": {
                        "enum": ["active", "archived", "deleted"],
                    },
                    "metrics": {
                        "bsonType": "object",
                        "properties": {
                            "message_count": {"bsonType": "int"},
                            "total_tokens": {"bsonType": "int"},
                            "total_cost_usd": {"bsonType": "double"},
                            "execution_time_ms": {"bsonType": "int"},
                        },
                    },
                },
            }
        }

        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        collection = self.db[collection_name]
        await collection.create_index([("user_id", ASCENDING)], name="idx_user_id")
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )
        await collection.create_index(
            [("provider_used", ASCENDING)], name="idx_provider"
        )
        await collection.create_index([("status", ASCENDING)], name="idx_status")

        self.logger.info("collection_initialized", collection=collection_name)

    async def _init_messages_collection(self) -> None:
        """Initialize messages collection with validation and indexes."""
        collection_name = "messages"

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["conversation_id", "role", "content"],
                "properties": {
                    "conversation_id": {"bsonType": "objectId"},
                    "role": {"enum": ["user", "assistant", "system"]},
                    "content": {"bsonType": "string"},
                    "provider": {"bsonType": ["string", "null"]},
                    "model": {"bsonType": ["string", "null"]},
                    "token_count": {"bsonType": ["int", "null"]},
                    "cost_usd": {"bsonType": ["double", "null"]},
                },
            }
        }

        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        collection = self.db[collection_name]
        await collection.create_index(
            [("conversation_id", ASCENDING)], name="idx_conversation_id"
        )
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )
        await collection.create_index([("role", ASCENDING)], name="idx_role")

        self.logger.info("collection_initialized", collection=collection_name)

    async def _init_tool_executions_collection(self) -> None:
        """Initialize tool_executions collection."""
        collection_name = "tool_executions"

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["conversation_id", "tool_type", "operation"],
                "properties": {
                    "conversation_id": {"bsonType": "objectId"},
                    "message_id": {"bsonType": "objectId"},
                    "tool_type": {"bsonType": "string"},
                    "operation": {"bsonType": "string"},
                    "success": {"bsonType": "bool"},
                    "execution_time_ms": {"bsonType": "int"},
                },
            }
        }

        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        collection = self.db[collection_name]
        await collection.create_index(
            [("conversation_id", ASCENDING)], name="idx_conversation_id"
        )
        await collection.create_index([("tool_type", ASCENDING)], name="idx_tool_type")
        await collection.create_index([("success", ASCENDING)], name="idx_success")
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )

        self.logger.info("collection_initialized", collection=collection_name)

    async def _init_context_events_collection(self) -> None:
        """Initialize context_events collection."""
        collection_name = "context_events"

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["conversation_id", "event_type", "provider"],
                "properties": {
                    "conversation_id": {"bsonType": "objectId"},
                    "event_type": {
                        "enum": ["check", "truncation", "overflow", "warning"]
                    },
                    "provider": {"bsonType": "string"},
                    "token_count": {"bsonType": "int"},
                    "limit": {"bsonType": "int"},
                },
            }
        }

        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        collection = self.db[collection_name]
        await collection.create_index(
            [("conversation_id", ASCENDING)], name="idx_conversation_id"
        )
        await collection.create_index(
            [("event_type", ASCENDING)], name="idx_event_type"
        )
        await collection.create_index([("provider", ASCENDING)], name="idx_provider")
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )

        self.logger.info("collection_initialized", collection=collection_name)

    async def _init_provider_metrics_collection(self) -> None:
        """Initialize provider_metrics collection."""
        collection_name = "provider_metrics"

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["provider", "metric_type"],
                "properties": {
                    "provider": {"bsonType": "string"},
                    "metric_type": {
                        "enum": [
                            "request",
                            "success",
                            "failure",
                            "latency",
                            "tokens",
                            "cost",
                        ]
                    },
                    "value": {"bsonType": "double"},
                },
            }
        }

        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        collection = self.db[collection_name]
        await collection.create_index([("provider", ASCENDING)], name="idx_provider")
        await collection.create_index(
            [("metric_type", ASCENDING)], name="idx_metric_type"
        )
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )

        self.logger.info("collection_initialized", collection=collection_name)

    async def _init_cost_records_collection(self) -> None:
        """Initialize cost_records collection."""
        collection_name = "cost_records"

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["provider", "model", "total_tokens", "total_cost"],
                "properties": {
                    "conversation_id": {"bsonType": ["objectId", "null"]},
                    "message_id": {"bsonType": ["objectId", "null"]},
                    "user_id": {"bsonType": ["string", "null"]},
                    "project_id": {"bsonType": ["string", "null"]},
                    "provider": {"bsonType": "string"},
                    "model": {"bsonType": "string"},
                    "input_tokens": {"bsonType": "int"},
                    "output_tokens": {"bsonType": "int"},
                    "total_tokens": {"bsonType": "int"},
                    "input_cost": {"bsonType": "double"},
                    "output_cost": {"bsonType": "double"},
                    "total_cost": {"bsonType": "double"},
                    "category": {"bsonType": ["string", "null"]},
                    "request_type": {"bsonType": ["string", "null"]},
                    "success": {"bsonType": "bool"},
                },
            }
        }

        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        collection = self.db[collection_name]
        await collection.create_index([("provider", ASCENDING)], name="idx_provider")
        await collection.create_index([("model", ASCENDING)], name="idx_model")
        await collection.create_index([("user_id", ASCENDING)], name="idx_user_id")
        await collection.create_index([("project_id", ASCENDING)], name="idx_project_id")
        await collection.create_index(
            [("conversation_id", ASCENDING)], name="idx_conversation_id"
        )
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )

        self.logger.info("collection_initialized", collection=collection_name)

    async def _init_budgets_collection(self) -> None:
        """Initialize budgets collection."""
        collection_name = "budgets"

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["budget_name", "is_active"],
                "properties": {
                    "budget_name": {"bsonType": "string"},
                    "user_id": {"bsonType": ["string", "null"]},
                    "project_id": {"bsonType": ["string", "null"]},
                    "provider": {"bsonType": ["string", "null"]},
                    "daily_limit": {"bsonType": ["double", "null"]},
                    "weekly_limit": {"bsonType": ["double", "null"]},
                    "monthly_limit": {"bsonType": ["double", "null"]},
                    "daily_spent": {"bsonType": "double"},
                    "weekly_spent": {"bsonType": "double"},
                    "monthly_spent": {"bsonType": "double"},
                    "warning_threshold": {"bsonType": "double"},
                    "critical_threshold": {"bsonType": "double"},
                    "is_active": {"bsonType": "bool"},
                },
            }
        }

        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        collection = self.db[collection_name]
        await collection.create_index([("user_id", ASCENDING)], name="idx_user_id")
        await collection.create_index([("project_id", ASCENDING)], name="idx_project_id")
        await collection.create_index([("provider", ASCENDING)], name="idx_provider")
        await collection.create_index([("is_active", ASCENDING)], name="idx_is_active")
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )

        self.logger.info("collection_initialized", collection=collection_name)

    async def _init_budget_alerts_collection(self) -> None:
        """Initialize budget_alerts collection."""
        collection_name = "budget_alerts"

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["budget_id", "alert_type", "threshold_type"],
                "properties": {
                    "budget_id": {"bsonType": "objectId"},
                    "alert_type": {"enum": ["warning", "critical", "exceeded"]},
                    "threshold_type": {"enum": ["daily", "weekly", "monthly"]},
                    "limit_usd": {"bsonType": "double"},
                    "spent_usd": {"bsonType": "double"},
                    "utilization_percent": {"bsonType": "double"},
                    "provider": {"bsonType": ["string", "null"]},
                    "notification_sent": {"bsonType": "bool"},
                },
            }
        }

        if collection_name not in await self.db.list_collection_names():
            await self.db.create_collection(
                collection_name, validator=validator
            )
            self.logger.info("collection_created", collection=collection_name)

        collection = self.db[collection_name]
        await collection.create_index([("budget_id", ASCENDING)], name="idx_budget_id")
        await collection.create_index([("alert_type", ASCENDING)], name="idx_alert_type")
        await collection.create_index(
            [("threshold_type", ASCENDING)], name="idx_threshold_type"
        )
        await collection.create_index(
            [("created_at", DESCENDING)], name="idx_created_at"
        )

        self.logger.info("collection_initialized", collection=collection_name)

    async def health_check(self) -> bool:
        """Check MongoDB connection health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.client:
                return False

            await self.client.admin.command("ping")
            return True

        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    def get_collection(self, collection_name: str):
        """Get a collection by name.

        Args:
            collection_name: Name of the collection

        Returns:
            AsyncIOMotorCollection
        """
        if self.db is None:
            raise RuntimeError("Database not connected")

        return self.db[collection_name]


# Global MongoDB manager instance
_mongodb_manager: Optional[MongoDBManager] = None


async def get_mongodb_manager(
    mongodb_url: Optional[str] = None,
    database_name: str = "ai_orchestrator",
) -> MongoDBManager:
    """Get global MongoDB manager instance (singleton).

    Args:
        mongodb_url: MongoDB connection URL
        database_name: Database name

    Returns:
        MongoDBManager instance
    """
    global _mongodb_manager

    if _mongodb_manager is None:
        _mongodb_manager = MongoDBManager(
            mongodb_url=mongodb_url, database_name=database_name
        )
        await _mongodb_manager.connect()

    return _mongodb_manager


async def close_mongodb_manager() -> None:
    """Close global MongoDB manager instance."""
    global _mongodb_manager

    if _mongodb_manager:
        await _mongodb_manager.disconnect()
        _mongodb_manager = None
