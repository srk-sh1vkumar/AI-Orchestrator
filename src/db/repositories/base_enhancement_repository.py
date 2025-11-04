"""
Abstract base class for enhancement repository.

Defines the interface that all repository implementations must follow,
enabling dual-mode support (YAML and Database).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.db.schemas.enhancement_schemas import (
    Project,
    Enhancement,
    Dependency,
    CompletionReport,
    ProgressSnapshot,
    ProjectResponse,
    EnhancementResponse,
    ProgressResponse
)


class BaseEnhancementRepository(ABC):
    """Abstract base class for enhancement data access."""

    # ============================================================================
    # Project Operations
    # ============================================================================

    @abstractmethod
    async def get_all_projects(self) -> List[ProjectResponse]:
        """Get all projects with summary statistics."""
        pass

    @abstractmethod
    async def get_project(self, project_tag: str) -> Optional[Project]:
        """Get project by tag."""
        pass

    @abstractmethod
    async def create_project(self, project: Project) -> str:
        """Create new project. Returns project_id."""
        pass

    @abstractmethod
    async def update_project(self, project_tag: str, updates: Dict[str, Any]) -> bool:
        """Update project. Returns success status."""
        pass

    @abstractmethod
    async def delete_project(self, project_tag: str) -> bool:
        """Delete project. Returns success status."""
        pass

    # ============================================================================
    # Enhancement Operations
    # ============================================================================

    @abstractmethod
    async def get_enhancements(
        self,
        project_tag: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        phase: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Enhancement]:
        """Get enhancements with optional filters."""
        pass

    @abstractmethod
    async def get_enhancement(
        self,
        project_tag: str,
        enhancement_number: str
    ) -> Optional[EnhancementResponse]:
        """Get enhancement by number with dependency info."""
        pass

    @abstractmethod
    async def create_enhancement(
        self,
        project_tag: str,
        enhancement: Enhancement
    ) -> str:
        """Create new enhancement. Returns enhancement_id."""
        pass

    @abstractmethod
    async def update_enhancement(
        self,
        project_tag: str,
        enhancement_number: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update enhancement. Returns success status."""
        pass

    @abstractmethod
    async def delete_enhancement(
        self,
        project_tag: str,
        enhancement_number: str
    ) -> bool:
        """Delete enhancement (soft delete - marks as Cancelled)."""
        pass

    # ============================================================================
    # Dependency Operations
    # ============================================================================

    @abstractmethod
    async def get_dependencies(self, enhancement_id: str) -> List[Dependency]:
        """Get all dependencies for an enhancement."""
        pass

    @abstractmethod
    async def add_dependency(self, dependency: Dependency) -> str:
        """Add dependency. Returns dependency_id."""
        pass

    @abstractmethod
    async def remove_dependency(self, dependency_id: str) -> bool:
        """Remove dependency. Returns success status."""
        pass

    # ============================================================================
    # Progress Operations
    # ============================================================================

    @abstractmethod
    async def get_progress(self, project_tag: str) -> ProgressResponse:
        """Get current progress statistics."""
        pass

    @abstractmethod
    async def get_progress_history(
        self,
        project_tag: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ProgressSnapshot]:
        """Get historical progress snapshots."""
        pass

    @abstractmethod
    async def create_progress_snapshot(
        self,
        project_tag: str
    ) -> str:
        """Create progress snapshot. Returns snapshot_id."""
        pass

    # ============================================================================
    # Completion Report Operations
    # ============================================================================

    @abstractmethod
    async def get_completion_report(
        self,
        enhancement_id: str
    ) -> Optional[CompletionReport]:
        """Get completion report for enhancement."""
        pass

    @abstractmethod
    async def create_completion_report(
        self,
        report: CompletionReport
    ) -> str:
        """Create completion report. Returns report_id."""
        pass

    # ============================================================================
    # Search and Query Operations
    # ============================================================================

    @abstractmethod
    async def search_enhancements(
        self,
        project_tag: str,
        search_text: str
    ) -> List[Enhancement]:
        """Search enhancements by text (title, summary, tags)."""
        pass

    @abstractmethod
    async def get_dependency_graph(
        self,
        project_tag: str
    ) -> Dict[str, List[str]]:
        """Get full dependency graph for a project.

        Returns dict mapping enhancement_number -> list of dependent enhancement_numbers.
        """
        pass

    @abstractmethod
    async def get_blocked_enhancements(
        self,
        project_tag: str
    ) -> List[Enhancement]:
        """Get enhancements blocked by incomplete dependencies."""
        pass
