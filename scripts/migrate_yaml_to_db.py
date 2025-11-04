#!/usr/bin/env python3
"""
Migrate YAML enhancement trackers to MongoDB.

This script migrates enhancement tracking data from YAML files to MongoDB,
supporting validation, dry-run mode, and rollback capabilities.

Usage:
    # Dry run (validation only)
    python scripts/migrate_yaml_to_db.py --dry-run --project ai_orchestrator

    # Migrate single project
    python scripts/migrate_yaml_to_db.py --project ai_orchestrator

    # Migrate all projects
    python scripts/migrate_yaml_to_db.py --all

    # Rollback (delete all data for a project)
    python scripts/migrate_yaml_to_db.py --rollback --project ai_orchestrator

    # Clear existing data before migration
    python scripts/migrate_yaml_to_db.py --clear --project ai_orchestrator
"""

import asyncio
import argparse
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import structlog

from src.db.repositories.mongo_enhancement_repository import MongoEnhancementRepository
from src.db.schemas.enhancement_schemas import (
    Project,
    Enhancement,
    Dependency,
    CompletionReport,
    ProgressSnapshot
)

logger = structlog.get_logger(__name__)

# MongoDB connection
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "ai_orchestrator"

# Project configurations
PROJECTS = {
    "ai_orchestrator": {
        "yaml_path": "PROJECT_ENHANCEMENT_TRACKER_DB.yaml",
        "yaml_structure": "flat",  # flat or nested
    },
    "ecommerce": {
        "yaml_path": "../ecommerce-microservices/ECOMMERCE_ENHANCEMENT_TRACKER.yaml",
        "yaml_structure": "nested",
    },
    "sre_analytics": {
        "yaml_path": "../sre-analytics/SRE_ANALYTICS_ENHANCEMENT_TRACKER.yaml",
        "yaml_structure": "nested",
    }
}


class MigrationStats:
    """Track migration statistics."""

    def __init__(self):
        self.projects = 0
        self.enhancements = 0
        self.dependencies = 0
        self.completion_reports = 0
        self.errors = []
        self.warnings = []

    def add_error(self, error: str):
        self.errors.append(error)
        logger.error("migration_error", error=error)

    def add_warning(self, warning: str):
        self.warnings.append(warning)
        logger.warning("migration_warning", warning=warning)

    def print_summary(self):
        """Print migration summary."""
        print("\n" + "=" * 70)
        print("Migration Summary")
        print("=" * 70)
        print(f"Projects migrated: {self.projects}")
        print(f"Enhancements migrated: {self.enhancements}")
        print(f"Dependencies created: {self.dependencies}")
        print(f"Completion reports: {self.completion_reports}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print("\n⚠️  Errors:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("=" * 70)


class YamlMigrator:
    """Handles YAML to MongoDB migration."""

    def __init__(self, repo: MongoEnhancementRepository, dry_run: bool = False):
        self.repo = repo
        self.dry_run = dry_run
        self.stats = MigrationStats()

    async def migrate_project(self, project_tag: str, config: Dict[str, Any]) -> bool:
        """Migrate a single project from YAML to MongoDB."""
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Migrating project: {project_tag}")
        print("=" * 70)

        # Step 1: Load and validate YAML
        yaml_path = Path(config["yaml_path"])
        if not yaml_path.exists():
            self.stats.add_error(f"YAML file not found: {yaml_path}")
            return False

        print(f"1. Loading YAML from: {yaml_path}")
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
            print(f"   ✅ YAML loaded successfully")
        except Exception as e:
            self.stats.add_error(f"Failed to load YAML: {e}")
            return False

        # Step 2: Validate YAML structure
        print("2. Validating YAML structure...")
        validation_errors = self._validate_yaml(data, config)
        if validation_errors:
            for error in validation_errors:
                self.stats.add_error(error)
            return False
        print(f"   ✅ YAML structure valid")

        # Step 3: Extract project metadata
        print("3. Extracting project metadata...")
        try:
            project = self._extract_project(data, project_tag, config)
            print(f"   ✅ Project: {project.project_name} v{project.version}")
        except Exception as e:
            self.stats.add_error(f"Failed to extract project: {e}")
            return False

        # Step 4: Check if project already exists
        existing_project = await self.repo.get_project(project_tag)
        if existing_project and not self.dry_run:
            self.stats.add_warning(f"Project {project_tag} already exists, will update")

        # Step 5: Create or update project
        if not self.dry_run:
            try:
                if existing_project:
                    await self.repo.update_project(project_tag, project.model_dump(exclude={"id"}))
                    project_id = existing_project.id
                    print(f"   ✅ Project updated: {project_id}")
                else:
                    project_id_str = await self.repo.create_project(project)
                    project_id = ObjectId(project_id_str)
                    print(f"   ✅ Project created: {project_id}")
                self.stats.projects += 1
            except Exception as e:
                self.stats.add_error(f"Failed to create/update project: {e}")
                return False
        else:
            project_id = ObjectId()
            print(f"   Would create project: {project.project_name}")

        # Step 6: Extract and migrate enhancements
        print("4. Migrating enhancements...")
        enhancements_data = data.get("enhancements", [])
        print(f"   Found {len(enhancements_data)} enhancements")

        enhancement_map = {}  # Map enhancement_number -> ObjectId
        for enh_data in enhancements_data:
            try:
                enhancement = self._extract_enhancement(enh_data, project_id)
                enhancement_map[enhancement.enhancement_number] = enhancement

                if not self.dry_run:
                    # Check if enhancement exists
                    existing = await self.repo.get_enhancement(
                        project_tag,
                        enhancement.enhancement_number
                    )

                    if existing:
                        # Update existing
                        await self.repo.update_enhancement(
                            project_tag,
                            enhancement.enhancement_number,
                            enhancement.model_dump(exclude={"id", "project_id", "created_at"})
                        )
                        enh_id = ObjectId(existing.enhancement_id)
                    else:
                        # Create new
                        enh_id_str = await self.repo.create_enhancement(project_tag, enhancement)
                        enh_id = ObjectId(enh_id_str)

                    enhancement_map[enhancement.enhancement_number] = enh_id
                    self.stats.enhancements += 1

                    print(f"   ✅ {enhancement.enhancement_number}: {enhancement.title} ({enhancement.status})")
                else:
                    print(f"   Would migrate: {enhancement.enhancement_number}: {enhancement.title}")

            except Exception as e:
                self.stats.add_error(f"Failed to migrate enhancement {enh_data.get('id', 'unknown')}: {e}")
                continue

        # Step 7: Migrate dependencies
        print("5. Migrating dependencies...")
        dep_count = await self._migrate_dependencies(
            enhancements_data,
            enhancement_map,
            project_tag
        )
        print(f"   ✅ Created {dep_count} dependencies")

        # Step 8: Migrate completion reports
        print("6. Migrating completion reports...")
        report_count = await self._migrate_completion_reports(
            data,
            enhancement_map,
            project_tag
        )
        print(f"   ✅ Created {report_count} completion reports")

        # Step 9: Create initial progress snapshot
        if not self.dry_run:
            print("7. Creating progress snapshot...")
            try:
                snapshot_id = await self.repo.create_progress_snapshot(project_tag)
                print(f"   ✅ Progress snapshot created: {snapshot_id}")
            except Exception as e:
                self.stats.add_warning(f"Failed to create progress snapshot: {e}")
        else:
            print("7. Would create progress snapshot")

        print(f"\n✅ {'[DRY RUN] ' if self.dry_run else ''}Migration completed for {project_tag}")
        return True

    def _validate_yaml(self, data: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """Validate YAML structure and required fields."""
        errors = []

        # Check for required top-level keys
        if config["yaml_structure"] == "flat":
            required_keys = ["project_name", "project_tag", "version", "enhancements"]
        else:
            required_keys = ["project", "enhancements"]

        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")

        # Validate enhancements
        if "enhancements" in data:
            if not isinstance(data["enhancements"], list):
                errors.append("'enhancements' must be a list")
            elif len(data["enhancements"]) == 0:
                errors.append("No enhancements found")
            else:
                # Validate each enhancement has required fields
                for i, enh in enumerate(data["enhancements"]):
                    if not isinstance(enh, dict):
                        errors.append(f"Enhancement {i} is not a dictionary")
                        continue

                    required_enh_fields = ["id", "title", "status"]
                    for field in required_enh_fields:
                        if field not in enh:
                            errors.append(f"Enhancement {i} missing required field: {field}")

        return errors

    def _extract_project(
        self,
        data: Dict[str, Any],
        project_tag: str,
        config: Dict[str, Any]
    ) -> Project:
        """Extract project metadata from YAML."""
        if config["yaml_structure"] == "flat":
            # AI Orchestrator format
            project_data = {
                "project_name": data.get("project_name"),
                "project_tag": data.get("project_tag"),
                "version": data.get("version"),
                "owner": data.get("owner", "Development Team"),
                "description": data.get("description"),
                "technologies": data.get("technologies", []),
                "metadata": data.get("metadata", {}),
            }
        else:
            # Nested format (e-commerce, SRE)
            project = data.get("project", {})
            project_data = {
                "project_name": project.get("name"),
                "project_tag": project.get("project_tag", project_tag),
                "version": project.get("version"),
                "owner": project.get("owner", "Development Team"),
                "description": project.get("description"),
                "technologies": project.get("technologies", []),
                "metadata": {
                    "repository": project.get("repository"),
                    "documentation": project.get("documentation"),
                },
            }

        # Add timestamps
        project_data["created_at"] = datetime.now(timezone.utc)
        project_data["updated_at"] = datetime.now(timezone.utc)

        return Project(**project_data)

    def _extract_enhancement(
        self,
        enh_data: Dict[str, Any],
        project_id: ObjectId
    ) -> Enhancement:
        """Extract enhancement from YAML data."""
        # Normalize enhancement number to 3 digits
        enh_id = str(enh_data.get("id", "000"))
        enhancement_number = enh_id.zfill(3)

        # Parse status (handle variations)
        status = enh_data.get("status", "Planned")
        if status in ["Completed", "Complete"]:
            status = "Complete"

        # Parse completion date
        completion_date = None
        if "completion_date" in enh_data:
            try:
                completion_date = datetime.fromisoformat(enh_data["completion_date"])
            except:
                # Try parsing as date string
                try:
                    completion_date = datetime.strptime(enh_data["completion_date"], "%Y-%m-%d")
                except:
                    pass

        # Normalize list fields (handle both list and dict formats)
        success_criteria = enh_data.get("success_criteria", [])
        if isinstance(success_criteria, dict):
            # Convert dict to list of strings
            success_criteria = [f"{k}: {v}" if isinstance(v, str) else f"{k}: {', '.join(v) if isinstance(v, list) else str(v)}"
                              for k, v in success_criteria.items()]
        elif not isinstance(success_criteria, list):
            success_criteria = []

        deliverables = enh_data.get("deliverables", [])
        if isinstance(deliverables, dict):
            # Convert dict to list of strings
            deliverables = [f"{k}: {v}" if isinstance(v, str) else f"{k}: {', '.join(v) if isinstance(v, list) else str(v)}"
                          for k, v in deliverables.items()]
        elif not isinstance(deliverables, list):
            deliverables = []

        completion_notes = enh_data.get("completion_notes", [])
        if not isinstance(completion_notes, list):
            completion_notes = []

        tags = enh_data.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        # Build enhancement object
        enhancement_data = {
            "project_id": project_id,
            "enhancement_number": enhancement_number,
            "db_reference": enh_data.get("db_reference", f"db-uuid-{enhancement_number}"),
            "title": enh_data["title"],
            "category": enh_data.get("category", "General"),
            "priority": enh_data.get("priority", "Medium"),
            "status": status,
            "phase": enh_data.get("phase", 1),
            "impact": enh_data.get("impact"),
            "related_agent": enh_data.get("related_agent"),
            "estimated_hours": float(enh_data.get("estimated_hours", 0)),
            "actual_hours": float(enh_data["actual_hours"]) if enh_data.get("actual_hours") else None,
            "completion_percentage": int(enh_data.get("completion_percentage", 0)),
            "completion_date": completion_date,
            "completion_report": enh_data.get("completion_report"),
            "technical_summary": enh_data.get("technical_summary"),
            "success_criteria": success_criteria,
            "deliverables": deliverables,
            "completion_notes": completion_notes,
            "implementation_notes": enh_data.get("implementation_notes"),
            "tags": tags,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        return Enhancement(**enhancement_data)

    async def _migrate_dependencies(
        self,
        enhancements_data: List[Dict[str, Any]],
        enhancement_map: Dict[str, Any],
        project_tag: str
    ) -> int:
        """Migrate dependencies between enhancements."""
        dep_count = 0

        for enh_data in enhancements_data:
            enh_id = str(enh_data.get("id", "000")).zfill(3)

            if enh_id not in enhancement_map:
                continue

            enhancement_obj_id = enhancement_map[enh_id]
            if isinstance(enhancement_obj_id, Enhancement):
                # In dry-run mode, skip dependencies
                continue

            dependencies = enh_data.get("dependencies", [])
            for dep_data in dependencies:
                if isinstance(dep_data, dict):
                    yaml_id = dep_data.get("yaml_id")
                    note = dep_data.get("note", "")
                else:
                    # Simple string format
                    yaml_id = dep_data
                    note = ""

                if not yaml_id:
                    continue

                # Normalize yaml_id to 3 digits
                yaml_id_normalized = str(yaml_id).zfill(3)

                # Check if dependency exists in map
                depends_on_id = None
                if yaml_id_normalized in enhancement_map:
                    dep_obj = enhancement_map[yaml_id_normalized]
                    if isinstance(dep_obj, ObjectId):
                        depends_on_id = dep_obj

                # Determine dependency type
                dep_type = "optional"
                if "required" in note.lower():
                    dep_type = "required"
                elif "blocking" in note.lower():
                    dep_type = "blocking"

                # Create dependency
                if not self.dry_run:
                    try:
                        dependency = Dependency(
                            enhancement_id=enhancement_obj_id,
                            depends_on_id=depends_on_id,
                            yaml_id=yaml_id_normalized,
                            dependency_type=dep_type,
                            note=note,
                            created_at=datetime.now(timezone.utc)
                        )

                        await self.repo.add_dependency(dependency)
                        dep_count += 1
                        self.stats.dependencies += 1
                    except Exception as e:
                        self.stats.add_warning(f"Failed to create dependency {enh_id} -> {yaml_id}: {e}")

        return dep_count

    async def _migrate_completion_reports(
        self,
        data: Dict[str, Any],
        enhancement_map: Dict[str, Any],
        project_tag: str
    ) -> int:
        """Migrate completion reports."""
        report_count = 0

        completion_reports = data.get("completion_reports", [])
        for report_data in completion_reports:
            if isinstance(report_data, dict):
                enh_id = str(report_data.get("enhancement_id", "000")).zfill(3)

                if enh_id not in enhancement_map:
                    continue

                enhancement_obj_id = enhancement_map[enh_id]
                if isinstance(enhancement_obj_id, Enhancement):
                    # Dry-run mode
                    continue

                # Parse completion date
                completion_date = datetime.now(timezone.utc)
                if "completion_date" in report_data:
                    try:
                        completion_date = datetime.fromisoformat(report_data["completion_date"])
                    except:
                        try:
                            completion_date = datetime.strptime(report_data["completion_date"], "%Y-%m-%d")
                        except:
                            pass

                if not self.dry_run:
                    try:
                        report = CompletionReport(
                            enhancement_id=enhancement_obj_id,
                            report_path=report_data.get("report_path", ""),
                            completion_date=completion_date,
                            created_at=datetime.now(timezone.utc)
                        )

                        await self.repo.create_completion_report(report)
                        report_count += 1
                        self.stats.completion_reports += 1
                    except Exception as e:
                        self.stats.add_warning(f"Failed to create completion report for {enh_id}: {e}")

        return report_count

    async def rollback_project(self, project_tag: str) -> bool:
        """Rollback migration by deleting all data for a project."""
        print(f"\n⚠️  Rollback: Deleting all data for {project_tag}")
        print("=" * 70)

        try:
            success = await self.repo.delete_project(project_tag)
            if success:
                print(f"✅ Project {project_tag} and all related data deleted")
                return True
            else:
                print(f"❌ Project {project_tag} not found")
                return False
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate YAML enhancement trackers to MongoDB")
    parser.add_argument("--project", help="Project to migrate (ai_orchestrator, ecommerce, sre_analytics)")
    parser.add_argument("--all", action="store_true", help="Migrate all projects")
    parser.add_argument("--dry-run", action="store_true", help="Validate without making changes")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration (delete data)")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before migration")
    parser.add_argument("--url", default=MONGODB_URL, help=f"MongoDB URL (default: {MONGODB_URL})")
    parser.add_argument("--database", default=DATABASE_NAME, help=f"Database name (default: {DATABASE_NAME})")

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.project:
        print("❌ Error: Must specify --project or --all")
        sys.exit(1)

    if args.all and args.project:
        print("❌ Error: Cannot specify both --project and --all")
        sys.exit(1)

    if args.rollback and args.all:
        print("❌ Error: Cannot rollback all projects at once (safety measure)")
        sys.exit(1)

    # Determine projects to migrate
    if args.all:
        projects_to_migrate = list(PROJECTS.keys())
    else:
        if args.project not in PROJECTS:
            print(f"❌ Error: Unknown project: {args.project}")
            print(f"Available projects: {', '.join(PROJECTS.keys())}")
            sys.exit(1)
        projects_to_migrate = [args.project]

    print("=" * 70)
    print("Enhancement Tracker Migration")
    print("=" * 70)
    print(f"MongoDB URL: {args.url}")
    print(f"Database: {args.database}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'ROLLBACK' if args.rollback else 'LIVE'}")
    print(f"Projects: {', '.join(projects_to_migrate)}")
    print("=" * 70)

    # Connect to MongoDB
    try:
        client = AsyncIOMotorClient(args.url)
        db = client[args.database]
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully\n")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    # Create repository
    repo = MongoEnhancementRepository(db)

    # Create migrator
    migrator = YamlMigrator(repo, dry_run=args.dry_run)

    # Process each project
    success_count = 0
    for project_tag in projects_to_migrate:
        config = PROJECTS[project_tag]

        if args.rollback:
            # Rollback mode
            if await migrator.rollback_project(project_tag):
                success_count += 1
        else:
            # Clear existing data if requested
            if args.clear and not args.dry_run:
                print(f"\n⚠️  Clearing existing data for {project_tag}...")
                await repo.delete_project(project_tag)
                print("✅ Data cleared\n")

            # Migrate project
            if await migrator.migrate_project(project_tag, config):
                success_count += 1

    # Print summary
    if not args.rollback:
        migrator.stats.print_summary()

    print(f"\n{'✅' if success_count == len(projects_to_migrate) else '⚠️'} " +
          f"{success_count}/{len(projects_to_migrate)} projects processed successfully")

    # Close connection
    client.close()

    # Exit with appropriate code
    sys.exit(0 if success_count == len(projects_to_migrate) else 1)


if __name__ == "__main__":
    asyncio.run(main())
