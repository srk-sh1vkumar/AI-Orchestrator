"""
MongoDB implementation of enhancement repository.

Provides full CRUD operations for projects, enhancements, dependencies,
and progress tracking using MongoDB with Motor async driver.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import structlog

from src.db.schemas.enhancement_schemas import (
    Project,
    Enhancement,
    Dependency,
    CompletionReport,
    ProgressSnapshot,
    ProjectResponse,
    EnhancementResponse,
    ProgressResponse,
    VelocityMetrics
)
from src.db.repositories.base_enhancement_repository import BaseEnhancementRepository

logger = structlog.get_logger(__name__)


class MongoEnhancementRepository(BaseEnhancementRepository):
    """MongoDB-based enhancement repository."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with MongoDB database instance."""
        self.db = db
        self.projects = db.projects
        self.enhancements = db.enhancements
        self.dependencies = db.dependencies
        self.completion_reports = db.completion_reports
        self.progress_snapshots = db.progress_snapshots

    # ============================================================================
    # Project Operations
    # ============================================================================

    async def get_all_projects(self) -> List[ProjectResponse]:
        """Get all projects with summary statistics."""
        cursor = self.projects.find({})
        projects = []

        async for doc in cursor:
            project = Project.from_mongo(doc)

            # Get enhancement stats
            stats = await self._get_project_stats(project.id)

            projects.append(ProjectResponse(
                project_id=str(project.id),
                project_name=project.project_name,
                project_tag=project.project_tag,
                version=project.version,
                owner=project.owner,
                description=project.description,
                technologies=project.technologies,
                total_enhancements=stats["total"],
                completed=stats["completed"],
                in_progress=stats["in_progress"],
                planned=stats["planned"],
                completion_percentage=stats["completion_percentage"],
                created_at=project.created_at,
                updated_at=project.updated_at
            ))

        return projects

    async def get_project(self, project_tag: str) -> Optional[Project]:
        """Get project by tag."""
        doc = await self.projects.find_one({"project_tag": project_tag})
        return Project.from_mongo(doc) if doc else None

    async def create_project(self, project: Project) -> str:
        """Create new project. Returns project_id."""
        project.created_at = datetime.utcnow()
        project.updated_at = datetime.utcnow()

        result = await self.projects.insert_one(project.to_mongo())
        logger.info("project_created", project_tag=project.project_tag, project_id=str(result.inserted_id))

        return str(result.inserted_id)

    async def update_project(self, project_tag: str, updates: Dict[str, Any]) -> bool:
        """Update project. Returns success status."""
        updates["updated_at"] = datetime.utcnow()

        result = await self.projects.update_one(
            {"project_tag": project_tag},
            {"$set": updates}
        )

        logger.info("project_updated", project_tag=project_tag, modified=result.modified_count)
        return result.modified_count > 0

    async def delete_project(self, project_tag: str) -> bool:
        """Delete project. Returns success status."""
        # Get project to delete enhancements
        project = await self.get_project(project_tag)
        if not project:
            return False

        # Delete all related data
        await self.enhancements.delete_many({"project_id": project.id})
        await self.progress_snapshots.delete_many({"project_id": project.id})

        result = await self.projects.delete_one({"project_tag": project_tag})

        logger.info("project_deleted", project_tag=project_tag, deleted=result.deleted_count)
        return result.deleted_count > 0

    # ============================================================================
    # Enhancement Operations
    # ============================================================================

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
        # Get project first
        project = await self.get_project(project_tag)
        if not project:
            return []

        # Build query
        query = {"project_id": project.id}
        if status:
            # Normalize status (handle both 'Complete' and 'Completed')
            if status == "Completed":
                status = "Complete"
            query["status"] = status
        if priority:
            query["priority"] = priority
        if phase:
            query["phase"] = phase

        # Execute query
        cursor = self.enhancements.find(query).skip(offset).limit(limit)
        enhancements = []

        async for doc in cursor:
            enhancements.append(Enhancement.from_mongo(doc))

        return enhancements

    async def get_enhancement(
        self,
        project_tag: str,
        enhancement_number: str
    ) -> Optional[EnhancementResponse]:
        """Get enhancement by number with dependency info."""
        # Get project first
        project = await self.get_project(project_tag)
        if not project:
            return None

        # Get enhancement
        doc = await self.enhancements.find_one({
            "project_id": project.id,
            "enhancement_number": enhancement_number
        })

        if not doc:
            return None

        enhancement = Enhancement.from_mongo(doc)

        # Get dependencies
        deps = await self.get_dependencies(str(enhancement.id))
        dependency_info = []

        for dep in deps:
            if dep.depends_on_id:
                # Get the dependent enhancement
                dep_doc = await self.enhancements.find_one({"_id": dep.depends_on_id})
                if dep_doc:
                    dependency_info.append({
                        "depends_on_number": dep_doc.get("enhancement_number"),
                        "depends_on_title": dep_doc.get("title"),
                        "dependency_type": dep.dependency_type,
                        "note": dep.note
                    })
            elif dep.yaml_id:
                # External dependency
                dependency_info.append({
                    "depends_on_number": dep.yaml_id,
                    "depends_on_title": "External Dependency",
                    "dependency_type": dep.dependency_type,
                    "note": dep.note
                })

        return EnhancementResponse(
            enhancement_id=str(enhancement.id),
            enhancement_number=enhancement.enhancement_number,
            title=enhancement.title,
            category=enhancement.category,
            priority=enhancement.priority,
            status=enhancement.status,
            phase=enhancement.phase,
            completion_percentage=enhancement.completion_percentage,
            estimated_hours=enhancement.estimated_hours,
            actual_hours=enhancement.actual_hours,
            completion_date=enhancement.completion_date,
            dependencies=dependency_info
        )

    async def create_enhancement(
        self,
        project_tag: str,
        enhancement: Enhancement
    ) -> str:
        """Create new enhancement. Returns enhancement_id."""
        # Get project
        project = await self.get_project(project_tag)
        if not project:
            raise ValueError(f"Project not found: {project_tag}")

        enhancement.project_id = project.id
        enhancement.created_at = datetime.utcnow()
        enhancement.updated_at = datetime.utcnow()

        result = await self.enhancements.insert_one(enhancement.to_mongo())

        logger.info(
            "enhancement_created",
            project_tag=project_tag,
            enhancement_number=enhancement.enhancement_number,
            enhancement_id=str(result.inserted_id)
        )

        return str(result.inserted_id)

    async def update_enhancement(
        self,
        project_tag: str,
        enhancement_number: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update enhancement. Returns success status."""
        # Get project
        project = await self.get_project(project_tag)
        if not project:
            return False

        updates["updated_at"] = datetime.utcnow()

        # Normalize status if present
        if "status" in updates and updates["status"] == "Completed":
            updates["status"] = "Complete"

        # Set completion_date if status is Complete and not already set
        if updates.get("status") == "Complete" and "completion_date" not in updates:
            updates["completion_date"] = datetime.utcnow()

        result = await self.enhancements.update_one(
            {"project_id": project.id, "enhancement_number": enhancement_number},
            {"$set": updates}
        )

        logger.info(
            "enhancement_updated",
            project_tag=project_tag,
            enhancement_number=enhancement_number,
            modified=result.modified_count
        )

        return result.modified_count > 0

    async def delete_enhancement(
        self,
        project_tag: str,
        enhancement_number: str
    ) -> bool:
        """Delete enhancement (soft delete - marks as Cancelled)."""
        return await self.update_enhancement(
            project_tag,
            enhancement_number,
            {"status": "Cancelled"}
        )

    # ============================================================================
    # Dependency Operations
    # ============================================================================

    async def get_dependencies(self, enhancement_id: str) -> List[Dependency]:
        """Get all dependencies for an enhancement."""
        cursor = self.dependencies.find({"enhancement_id": ObjectId(enhancement_id)})
        dependencies = []

        async for doc in cursor:
            dependencies.append(Dependency.from_mongo(doc))

        return dependencies

    async def add_dependency(self, dependency: Dependency) -> str:
        """Add dependency. Returns dependency_id."""
        dependency.created_at = datetime.utcnow()

        result = await self.dependencies.insert_one(dependency.to_mongo())

        logger.info("dependency_added", dependency_id=str(result.inserted_id))

        return str(result.inserted_id)

    async def remove_dependency(self, dependency_id: str) -> bool:
        """Remove dependency. Returns success status."""
        result = await self.dependencies.delete_one({"_id": ObjectId(dependency_id)})

        logger.info("dependency_removed", dependency_id=dependency_id, deleted=result.deleted_count)

        return result.deleted_count > 0

    # ============================================================================
    # Progress Operations
    # ============================================================================

    async def get_progress(self, project_tag: str) -> ProgressResponse:
        """Get current progress statistics."""
        project = await self.get_project(project_tag)
        if not project:
            raise ValueError(f"Project not found: {project_tag}")

        stats = await self._get_project_stats(project.id)

        # Calculate velocity from recent snapshots
        velocity = await self._calculate_velocity(project.id)

        return ProgressResponse(
            project_tag=project_tag,
            total_enhancements=stats["total"],
            completed=stats["completed"],
            in_progress=stats["in_progress"],
            planned=stats["planned"],
            blocked=stats["blocked"],
            completion_percentage=stats["completion_percentage"],
            estimated_total_hours=stats["estimated_total_hours"],
            actual_total_hours=stats["actual_total_hours"],
            remaining_hours=stats["estimated_total_hours"] - stats["actual_total_hours"],
            velocity=velocity
        )

    async def get_progress_history(
        self,
        project_tag: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ProgressSnapshot]:
        """Get historical progress snapshots."""
        project = await self.get_project(project_tag)
        if not project:
            return []

        # Build query
        query = {"project_id": project.id}
        if start_date or end_date:
            query["snapshot_date"] = {}
            if start_date:
                query["snapshot_date"]["$gte"] = start_date
            if end_date:
                query["snapshot_date"]["$lte"] = end_date

        cursor = self.progress_snapshots.find(query).sort("snapshot_date", -1)
        snapshots = []

        async for doc in cursor:
            snapshots.append(ProgressSnapshot.from_mongo(doc))

        return snapshots

    async def create_progress_snapshot(self, project_tag: str) -> str:
        """Create progress snapshot. Returns snapshot_id."""
        project = await self.get_project(project_tag)
        if not project:
            raise ValueError(f"Project not found: {project_tag}")

        stats = await self._get_project_stats(project.id)
        velocity = await self._calculate_velocity(project.id)

        snapshot = ProgressSnapshot(
            project_id=project.id,
            snapshot_date=datetime.utcnow(),
            total_enhancements=stats["total"],
            completed=stats["completed"],
            in_progress=stats["in_progress"],
            planned=stats["planned"],
            blocked=stats["blocked"],
            completion_percentage=stats["completion_percentage"],
            estimated_total_hours=stats["estimated_total_hours"],
            actual_total_hours=stats["actual_total_hours"],
            velocity=velocity,
            created_at=datetime.utcnow()
        )

        result = await self.progress_snapshots.insert_one(snapshot.to_mongo())

        logger.info("progress_snapshot_created", project_tag=project_tag, snapshot_id=str(result.inserted_id))

        return str(result.inserted_id)

    # ============================================================================
    # Completion Report Operations
    # ============================================================================

    async def get_completion_report(self, enhancement_id: str) -> Optional[CompletionReport]:
        """Get completion report for enhancement."""
        doc = await self.completion_reports.find_one({"enhancement_id": ObjectId(enhancement_id)})
        return CompletionReport.from_mongo(doc) if doc else None

    async def create_completion_report(self, report: CompletionReport) -> str:
        """Create completion report. Returns report_id."""
        report.created_at = datetime.utcnow()

        result = await self.completion_reports.insert_one(report.to_mongo())

        logger.info("completion_report_created", report_id=str(result.inserted_id))

        return str(result.inserted_id)

    # ============================================================================
    # Search and Query Operations
    # ============================================================================

    async def search_enhancements(
        self,
        project_tag: str,
        search_text: str
    ) -> List[Enhancement]:
        """Search enhancements by text (title, summary, tags)."""
        project = await self.get_project(project_tag)
        if not project:
            return []

        # Text search in title, technical_summary, and tags
        query = {
            "project_id": project.id,
            "$or": [
                {"title": {"$regex": search_text, "$options": "i"}},
                {"technical_summary": {"$regex": search_text, "$options": "i"}},
                {"tags": {"$in": [search_text.lower()]}}
            ]
        }

        cursor = self.enhancements.find(query)
        enhancements = []

        async for doc in cursor:
            enhancements.append(Enhancement.from_mongo(doc))

        return enhancements

    async def get_dependency_graph(self, project_tag: str) -> Dict[str, List[str]]:
        """Get full dependency graph for a project."""
        project = await self.get_project(project_tag)
        if not project:
            return {}

        # Get all enhancements for this project
        cursor = self.enhancements.find({"project_id": project.id})
        enhancement_map = {}

        async for doc in cursor:
            enhancement_map[str(doc["_id"])] = doc["enhancement_number"]

        # Get all dependencies
        dep_cursor = self.dependencies.find({})
        graph = {}

        async for dep_doc in dep_cursor:
            enhancement_id = str(dep_doc["enhancement_id"])
            if enhancement_id in enhancement_map:
                enhancement_num = enhancement_map[enhancement_id]

                if enhancement_num not in graph:
                    graph[enhancement_num] = []

                if dep_doc.get("depends_on_id"):
                    depends_on_id = str(dep_doc["depends_on_id"])
                    if depends_on_id in enhancement_map:
                        graph[enhancement_num].append(enhancement_map[depends_on_id])
                elif dep_doc.get("yaml_id"):
                    graph[enhancement_num].append(dep_doc["yaml_id"])

        return graph

    async def get_blocked_enhancements(self, project_tag: str) -> List[Enhancement]:
        """Get enhancements blocked by incomplete dependencies."""
        enhancements = await self.get_enhancements(project_tag, status="Blocked")
        return enhancements

    # ============================================================================
    # Private Helper Methods
    # ============================================================================

    async def _get_project_stats(self, project_id: ObjectId) -> Dict[str, Any]:
        """Get enhancement statistics for a project."""
        # Aggregate statistics
        pipeline = [
            {"$match": {"project_id": project_id}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "completed": {
                    "$sum": {
                        "$cond": [{"$in": ["$status", ["Complete", "Completed"]]}, 1, 0]
                    }
                },
                "in_progress": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "In Progress"]}, 1, 0]
                    }
                },
                "planned": {
                    "$sum": {
                        "$cond": [{"$in": ["$status", ["Planned", "Ideation"]]}, 1, 0]
                    }
                },
                "blocked": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "Blocked"]}, 1, 0]
                    }
                },
                "estimated_total_hours": {"$sum": "$estimated_hours"},
                "actual_total_hours": {"$sum": {"$ifNull": ["$actual_hours", 0]}}
            }}
        ]

        cursor = self.enhancements.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if result:
            stats = result[0]
            total = stats.get("total", 0)
            completed = stats.get("completed", 0)
            completion_pct = (completed / total * 100) if total > 0 else 0

            return {
                "total": total,
                "completed": completed,
                "in_progress": stats.get("in_progress", 0),
                "planned": stats.get("planned", 0),
                "blocked": stats.get("blocked", 0),
                "completion_percentage": round(completion_pct, 1),
                "estimated_total_hours": stats.get("estimated_total_hours", 0),
                "actual_total_hours": stats.get("actual_total_hours", 0)
            }
        else:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "planned": 0,
                "blocked": 0,
                "completion_percentage": 0,
                "estimated_total_hours": 0,
                "actual_total_hours": 0
            }

    async def _calculate_velocity(self, project_id: ObjectId) -> Optional[VelocityMetrics]:
        """Calculate velocity metrics from recent snapshots."""
        # Get last 4 weekly snapshots
        cursor = self.progress_snapshots.find(
            {"project_id": project_id}
        ).sort("snapshot_date", -1).limit(4)

        snapshots = await cursor.to_list(length=4)

        if len(snapshots) < 2:
            return None

        # Calculate averages
        total_weeks = len(snapshots) - 1
        enhancements_completed = snapshots[0]["completed"] - snapshots[-1]["completed"]
        hours_spent = snapshots[0]["actual_total_hours"] - snapshots[-1]["actual_total_hours"]

        # Calculate average completion time
        completed_enhancements = await self.enhancements.find({
            "project_id": project_id,
            "status": {"$in": ["Complete", "Completed"]},
            "completion_date": {"$exists": True}
        }).to_list(length=100)

        completion_times = []
        for enh in completed_enhancements:
            if enh.get("created_at") and enh.get("completion_date"):
                delta = enh["completion_date"] - enh["created_at"]
                completion_times.append(delta.days)

        avg_completion_days = sum(completion_times) / len(completion_times) if completion_times else 0

        return VelocityMetrics(
            enhancements_per_week=enhancements_completed / total_weeks if total_weeks > 0 else 0,
            hours_per_week=hours_spent / total_weeks if total_weeks > 0 else 0,
            avg_completion_time_days=avg_completion_days
        )
