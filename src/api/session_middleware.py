"""
Session tracking middleware for FastAPI.

Automatically tracks API activities and updates the session tracker in real-time.
"""

from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from src.core.session_tracker import get_session_tracker

logger = structlog.get_logger(__name__)


class SessionTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track API activities."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.session_tracker = get_session_tracker()
        self.tracked_endpoints = {
            "/api/chat": "llm_chat",
            "/api/chat/stream": "llm_streaming",
            "/api/tracker": "personal_tracker",
            "/api/growth": "growth_tracking",
            "/api/enhancements": "enhancement_tracking",
            "/api/conversations": "conversation_management"
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track API activity before and after request."""

        # Get request details
        method = request.method
        path = request.url.path

        # Skip tracking for health checks and static files
        if path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Track activity start
        start_time = datetime.now()

        # Determine activity type
        activity_type = self._get_activity_type(path, method)

        # Process request
        response = await call_next(request)

        # Track activity completion
        if activity_type:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Track the activity
            self.session_tracker.track_activity(
                activity_type=activity_type,
                description=self._get_activity_description(path, method),
                metadata={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )

            # Track technologies used
            self._track_technologies(path)

            # Track topics based on endpoint
            self._track_topics(path)

        return response

    def _get_activity_type(self, path: str, method: str) -> str:
        """Determine activity type from path and method.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Activity type string
        """
        for endpoint, activity in self.tracked_endpoints.items():
            if path.startswith(endpoint):
                return activity

        # Default activity types
        if method == "POST":
            return "api_creation"
        elif method == "PUT" or method == "PATCH":
            return "api_update"
        elif method == "DELETE":
            return "api_deletion"
        elif method == "GET":
            return "api_query"

        return "api_interaction"

    def _get_activity_description(self, path: str, method: str) -> str:
        """Generate human-readable activity description.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Activity description
        """
        if "chat" in path:
            if method == "POST":
                return "Generated LLM response"
            return "Accessed chat interface"

        if "tracker" in path:
            if "goals" in path:
                return "Managed personal goals"
            return "Accessed personal tracker"

        if "growth" in path:
            if "reflections" in path:
                if method == "POST":
                    return "Created weekly reflection"
                return "Viewed growth reflections"
            if "summary" in path:
                return "Viewed growth summary"
            return "Tracked personal growth"

        if "enhancements" in path:
            return "Worked on project enhancements"

        if "conversations" in path:
            return "Managed conversations"

        return f"{method} {path}"

    def _track_technologies(self, path: str):
        """Track technologies used based on endpoint.

        Args:
            path: Request path
        """
        tech_map = {
            "/api/chat": ["LLM APIs", "FastAPI", "AsyncIO"],
            "/api/tracker": ["React", "FastAPI", "JSON Storage"],
            "/api/growth": ["Python", "Data Analytics", "FastAPI"],
            "/api/enhancements": ["YAML", "Project Management", "FastAPI"]
        }

        for endpoint, technologies in tech_map.items():
            if path.startswith(endpoint):
                for tech in technologies:
                    self.session_tracker.add_technology(tech)
                break

    def _track_topics(self, path: str):
        """Track learning topics based on endpoint.

        Args:
            path: Request path
        """
        topic_map = {
            "/api/chat": "LLM Orchestration",
            "/api/chat/stream": "Server-Sent Events (SSE)",
            "/api/tracker": "Personal Development Tracking",
            "/api/growth": "Growth Tracking & Reflections",
            "/api/enhancements": "Project Enhancement Management",
            "/api/monitoring": "System Monitoring",
            "/api/analytics": "Analytics & Metrics"
        }

        for endpoint, topic in topic_map.items():
            if path.startswith(endpoint):
                self.session_tracker.add_topic(topic)
                break


def track_file_operation(file_path: str, operation: str):
    """Helper function to track file operations.

    Args:
        file_path: Path to the file
        operation: Operation type (create, edit, delete, read)
    """
    tracker = get_session_tracker()
    tracker.track_file_modification(file_path, operation)
    logger.info("file_operation_tracked", path=file_path, operation=operation)


def track_accomplishment(description: str):
    """Helper function to track accomplishments.

    Args:
        description: Accomplishment description
    """
    tracker = get_session_tracker()
    tracker.add_accomplishment(description)
    logger.info("accomplishment_tracked", description=description)


def track_blocker(description: str):
    """Helper function to track blockers.

    Args:
        description: Blocker description
    """
    tracker = get_session_tracker()
    tracker.add_blocker(description)
    logger.info("blocker_tracked", description=description)
