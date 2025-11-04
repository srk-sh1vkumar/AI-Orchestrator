"""
Enhancement data source adapter with dual-mode support.

Provides unified interface for reading/writing enhancement data
from both YAML files and MongoDB database with configurable fallback.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import yaml
import structlog
from datetime import datetime, timezone

from src.db.repositories.mongo_enhancement_repository import MongoEnhancementRepository
from src.db.schemas.enhancement_schemas import Enhancement, Project

logger = structlog.get_logger(__name__)


class EnhancementDataAdapter:
    """Adapter for enhancement data with dual-mode support (YAML + Database)."""

    def __init__(self, config_file: str = "config/data_source_config.json"):
        """Initialize the adapter with configuration.

        Args:
            config_file: Path to data source configuration file
        """
        self.config = self._load_config(config_file)
        self.mode = self.config.get("enhancement_tracking", {}).get("mode", "dual")
        self.primary_source = self.config.get("enhancement_tracking", {}).get("primary_source", "database")
        self.fallback_source = self.config.get("enhancement_tracking", {}).get("fallback_source", "yaml")
        self.write_to_both = self.config.get("enhancement_tracking", {}).get("write_to_both", True)
        self.yaml_file = Path(self.config.get("enhancement_tracking", {}).get("yaml_file", "PROJECT_ENHANCEMENT_TRACKER_DB.yaml"))

        # Initialize repositories if database enabled
        self.db_enabled = self.config.get("enhancement_tracking", {}).get("mongodb_enabled", True)
        self.enhancement_repo = None

        if self.db_enabled and self.mode in ["database", "dual"]:
            try:
                from motor.motor_asyncio import AsyncIOMotorClient

                # Connect to MongoDB
                mongodb_url = "mongodb://localhost:27017"
                database_name = "ai_orchestrator"

                client = AsyncIOMotorClient(mongodb_url)
                db = client[database_name]

                self.enhancement_repo = MongoEnhancementRepository(db)
            except Exception as e:
                logger.warning("database_initialization_failed", error=str(e))
                self.db_enabled = False

        logger.info(
            "enhancement_adapter_initialized",
            mode=self.mode,
            primary_source=self.primary_source,
            db_enabled=self.db_enabled
        )

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file.

        Args:
            config_file: Path to config file

        Returns:
            Configuration dictionary
        """
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)

        # Default config
        return {
            "enhancement_tracking": {
                "mode": "dual",
                "primary_source": "database",
                "fallback_source": "yaml",
                "write_to_both": True,
                "yaml_file": "PROJECT_ENHANCEMENT_TRACKER_DB.yaml",
                "mongodb_enabled": True
            }
        }

    async def get_all_enhancements(
        self,
        project_tag: Optional[str] = None
    ) -> List[Enhancement]:
        """Get all enhancements, with fallback support.

        Args:
            project_tag: Optional project tag to filter by

        Returns:
            List of Enhancement objects
        """
        # Try primary source
        try:
            if self.primary_source == "database" and self.db_enabled:
                return await self._get_enhancements_from_db(project_tag)
            elif self.primary_source == "yaml":
                return await self._get_enhancements_from_yaml(project_tag)
        except Exception as e:
            logger.warning(
                "primary_source_failed",
                source=self.primary_source,
                error=str(e)
            )

        # Try fallback source
        if self.mode == "dual":
            try:
                if self.fallback_source == "database" and self.db_enabled:
                    return await self._get_enhancements_from_db(project_tag)
                elif self.fallback_source == "yaml":
                    return await self._get_enhancements_from_yaml(project_tag)
            except Exception as e:
                logger.error(
                    "fallback_source_failed",
                    source=self.fallback_source,
                    error=str(e)
                )

        return []

    async def _get_enhancements_from_db(
        self,
        project_tag: Optional[str] = None
    ) -> List[Enhancement]:
        """Get enhancements from database.

        Args:
            project_tag: Optional project tag filter

        Returns:
            List of Enhancement objects
        """
        # Use the correct repository method
        enhancements = await self.enhancement_repo.get_enhancements(
            project_tag=project_tag,
            status=None,
            priority=None,
            phase=None
        )

        logger.info(
            "enhancements_loaded_from_db",
            count=len(enhancements),
            project_tag=project_tag
        )

        return enhancements

    async def _get_enhancements_from_yaml(
        self,
        project_tag: Optional[str] = None
    ) -> List[Enhancement]:
        """Get enhancements from YAML file.

        Args:
            project_tag: Optional project tag filter

        Returns:
            List of Enhancement objects
        """
        if not self.yaml_file.exists():
            logger.warning("yaml_file_not_found", path=str(self.yaml_file))
            return []

        with open(self.yaml_file, 'r') as f:
            data = yaml.safe_load(f)

        enhancements = []
        projects = data.get("projects", [])

        for project in projects:
            current_project_tag = project.get("project_tag", "")

            # Filter by project tag if specified
            if project_tag and current_project_tag != project_tag:
                continue

            for enh in project.get("enhancements", []):
                # Convert YAML format to Enhancement model
                enhancement = Enhancement(
                    project_tag=current_project_tag,
                    enhancement_number=enh.get("enhancement_id", ""),
                    title=enh.get("title", ""),
                    category=enh.get("category", ""),
                    priority=enh.get("priority", "medium"),
                    status=enh.get("status", "pending"),
                    phase=enh.get("phase", 1),
                    description=enh.get("description", ""),
                    success_criteria=enh.get("success_criteria", []),
                    deliverables=enh.get("deliverables", []),
                    estimated_hours=enh.get("estimated_hours", 0.0),
                    actual_hours=enh.get("actual_hours", 0.0),
                    completion_percentage=enh.get("completion_percentage", 0),
                    completion_date=enh.get("completion_date"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                enhancements.append(enhancement)

        logger.info(
            "enhancements_loaded_from_yaml",
            count=len(enhancements),
            project_tag=project_tag
        )

        return enhancements

    async def get_enhancement(
        self,
        enhancement_number: str,
        project_tag: Optional[str] = None
    ) -> Optional[Enhancement]:
        """Get a specific enhancement by number.

        Args:
            enhancement_number: Enhancement ID (e.g., "001")
            project_tag: Optional project tag

        Returns:
            Enhancement object or None
        """
        # Try primary source
        try:
            if self.primary_source == "database" and self.db_enabled:
                return await self.enhancement_repo.get_enhancement(
                    project_tag=project_tag,
                    enhancement_number=enhancement_number
                )
            elif self.primary_source == "yaml":
                enhancements = await self._get_enhancements_from_yaml(project_tag)
                for enh in enhancements:
                    if enh.enhancement_number == enhancement_number:
                        return enh
        except Exception as e:
            logger.warning(
                "primary_source_failed",
                source=self.primary_source,
                error=str(e)
            )

        # Try fallback
        if self.mode == "dual":
            try:
                if self.fallback_source == "database" and self.db_enabled:
                    return await self.enhancement_repo.get_enhancement(
                        project_tag=project_tag,
                        enhancement_number=enhancement_number
                    )
                elif self.fallback_source == "yaml":
                    enhancements = await self._get_enhancements_from_yaml(project_tag)
                    for enh in enhancements:
                        if enh.enhancement_number == enhancement_number:
                            return enh
            except Exception as e:
                logger.error(
                    "fallback_source_failed",
                    source=self.fallback_source,
                    error=str(e)
                )

        return None

    async def save_enhancement(self, enhancement: Enhancement) -> Enhancement:
        """Save enhancement to configured data sources.

        Args:
            enhancement: Enhancement object to save

        Returns:
            Saved enhancement
        """
        saved = None

        # Save to database if enabled
        if self.db_enabled and self.mode in ["database", "dual"]:
            try:
                # Check if enhancement exists
                existing = await self.enhancement_repo.get_enhancement(
                    project_tag=enhancement.project_tag,
                    enhancement_number=enhancement.enhancement_number
                )

                if existing:
                    # Update existing
                    await self.enhancement_repo.update_enhancement(
                        project_tag=enhancement.project_tag,
                        enhancement_number=enhancement.enhancement_number,
                        updates=enhancement.model_dump(exclude={"id"})
                    )
                    saved = enhancement
                    logger.info(
                        "enhancement_updated_in_db",
                        enhancement_number=enhancement.enhancement_number
                    )
                else:
                    # Create new
                    await self.enhancement_repo.create_enhancement(enhancement)
                    saved = enhancement
                    logger.info(
                        "enhancement_created_in_db",
                        enhancement_number=enhancement.enhancement_number
                    )
            except Exception as e:
                logger.error(
                    "database_save_failed",
                    enhancement_number=enhancement.enhancement_number,
                    error=str(e)
                )

                # If database is primary and fails, raise error
                if self.mode == "database":
                    raise

        # Save to YAML if configured
        if (self.mode == "yaml") or (self.mode == "dual" and self.write_to_both):
            try:
                await self._save_enhancement_to_yaml(enhancement)
                logger.info(
                    "enhancement_saved_to_yaml",
                    enhancement_number=enhancement.enhancement_number
                )
            except Exception as e:
                logger.error(
                    "yaml_save_failed",
                    enhancement_number=enhancement.enhancement_number,
                    error=str(e)
                )

                # If YAML is primary and fails, raise error
                if self.mode == "yaml":
                    raise

        return saved or enhancement

    async def _save_enhancement_to_yaml(self, enhancement: Enhancement):
        """Save enhancement to YAML file.

        Args:
            enhancement: Enhancement to save
        """
        # Load existing YAML
        if self.yaml_file.exists():
            with open(self.yaml_file, 'r') as f:
                data = yaml.safe_load(f)
        else:
            data = {"projects": []}

        # Find or create project
        project = None
        for p in data["projects"]:
            if p.get("project_tag") == enhancement.project_tag:
                project = p
                break

        if not project:
            project = {
                "project_tag": enhancement.project_tag,
                "enhancements": []
            }
            data["projects"].append(project)

        # Find or create enhancement entry
        enh_entry = None
        for e in project["enhancements"]:
            if e.get("enhancement_id") == enhancement.enhancement_number:
                enh_entry = e
                break

        # Convert Enhancement to YAML format
        yaml_data = {
            "enhancement_id": enhancement.enhancement_number,
            "title": enhancement.title,
            "category": enhancement.category,
            "priority": enhancement.priority,
            "status": enhancement.status,
            "phase": enhancement.phase,
            "description": enhancement.description,
            "success_criteria": enhancement.success_criteria,
            "deliverables": enhancement.deliverables,
            "estimated_hours": enhancement.estimated_hours,
            "actual_hours": enhancement.actual_hours,
            "completion_percentage": enhancement.completion_percentage,
            "completion_date": enhancement.completion_date
        }

        if enh_entry:
            # Update existing
            enh_entry.update(yaml_data)
        else:
            # Add new
            project["enhancements"].append(yaml_data)

        # Save YAML
        with open(self.yaml_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# Global adapter instance
_adapter: Optional[EnhancementDataAdapter] = None


def get_enhancement_adapter() -> EnhancementDataAdapter:
    """Get or create global enhancement adapter instance.

    Returns:
        EnhancementDataAdapter instance
    """
    global _adapter
    if _adapter is None:
        _adapter = EnhancementDataAdapter()
    return _adapter
