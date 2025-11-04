#!/usr/bin/env python3
"""
Create MongoDB collections with schema validation for enhancement tracking.

This script creates 5 collections with full schema validation, indexes,
and constraints to ensure data integrity.

Usage:
    python scripts/create_enhancement_collections.py
    python scripts/create_enhancement_collections.py --drop  # Drop existing collections first
    python scripts/create_enhancement_collections.py --dry-run  # Show what would be created
"""

import asyncio
import argparse
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid, OperationFailure
from datetime import datetime


# MongoDB connection configuration
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "ai_orchestrator"


# Schema validation rules
PROJECTS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["project_name", "project_tag", "version", "owner", "created_at", "updated_at"],
        "properties": {
            "project_name": {
                "bsonType": "string",
                "minLength": 1,
                "maxLength": 200,
                "description": "Project name is required and must be 1-200 characters"
            },
            "project_tag": {
                "bsonType": "string",
                "pattern": "^[a-z][a-z0-9_]*$",
                "minLength": 2,
                "maxLength": 50,
                "description": "Project tag must start with lowercase letter, contain only lowercase letters, numbers, and underscores"
            },
            "version": {
                "bsonType": "string",
                "pattern": "^\\d+\\.\\d+\\.\\d+$",
                "description": "Version must follow semantic versioning (e.g., 0.1.0)"
            },
            "owner": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Owner/team name is required"
            },
            "description": {
                "bsonType": "string",
                "description": "Optional project description"
            },
            "technologies": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Array of technology names"
            },
            "metadata": {
                "bsonType": "object",
                "description": "Additional project metadata (repository URL, docs, etc.)"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Project creation timestamp"
            },
            "updated_at": {
                "bsonType": "date",
                "description": "Last update timestamp"
            }
        }
    }
}


ENHANCEMENTS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "project_id", "enhancement_number", "title", "category",
            "priority", "status", "phase", "estimated_hours",
            "completion_percentage", "created_at", "updated_at"
        ],
        "properties": {
            "project_id": {
                "bsonType": "objectId",
                "description": "Foreign key to projects collection"
            },
            "enhancement_number": {
                "bsonType": "string",
                "pattern": "^\\d{3}$",
                "description": "Three-digit enhancement number (e.g., 001, 002)"
            },
            "db_reference": {
                "bsonType": "string",
                "description": "Unique database reference (e.g., db-uuid-001-intent-routing)"
            },
            "title": {
                "bsonType": "string",
                "minLength": 5,
                "maxLength": 200,
                "description": "Enhancement title (5-200 characters)"
            },
            "category": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Enhancement category (e.g., Routing & Intelligence)"
            },
            "priority": {
                "enum": ["Critical", "High", "Medium", "Low"],
                "description": "Priority level"
            },
            "status": {
                "enum": ["Planned", "Ideation", "In Progress", "Complete", "Completed", "Blocked", "Cancelled"],
                "description": "Current status"
            },
            "phase": {
                "bsonType": "int",
                "minimum": 1,
                "maximum": 5,
                "description": "Project phase (1-5)"
            },
            "impact": {
                "bsonType": "string",
                "description": "Business/technical impact description"
            },
            "related_agent": {
                "bsonType": "string",
                "description": "Component or agent this enhancement affects"
            },
            "estimated_hours": {
                "bsonType": "double",
                "minimum": 0,
                "description": "Estimated effort in hours"
            },
            "actual_hours": {
                "bsonType": ["double", "null"],
                "minimum": 0,
                "description": "Actual effort in hours (null if not started)"
            },
            "completion_percentage": {
                "bsonType": "int",
                "minimum": 0,
                "maximum": 100,
                "description": "Completion percentage (0-100)"
            },
            "completion_date": {
                "bsonType": ["date", "null"],
                "description": "Date when enhancement was completed"
            },
            "completion_report": {
                "bsonType": "string",
                "description": "Path to completion report markdown file"
            },
            "technical_summary": {
                "bsonType": "string",
                "description": "Technical description of the enhancement"
            },
            "success_criteria": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Array of success criteria"
            },
            "deliverables": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Array of deliverable descriptions"
            },
            "completion_notes": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Array of completion notes"
            },
            "implementation_notes": {
                "bsonType": "string",
                "description": "Implementation details and notes"
            },
            "tags": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Tags for categorization and search"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Creation timestamp"
            },
            "updated_at": {
                "bsonType": "date",
                "description": "Last update timestamp"
            }
        }
    }
}


DEPENDENCIES_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["enhancement_id", "dependency_type", "created_at"],
        "properties": {
            "enhancement_id": {
                "bsonType": "objectId",
                "description": "Enhancement that has the dependency"
            },
            "depends_on_id": {
                "bsonType": ["objectId", "null"],
                "description": "Enhancement that is depended upon (null for external dependencies)"
            },
            "yaml_id": {
                "bsonType": "string",
                "description": "Original YAML enhancement ID for legacy references"
            },
            "dependency_type": {
                "enum": ["required", "optional", "blocking"],
                "description": "Type of dependency relationship"
            },
            "note": {
                "bsonType": "string",
                "description": "Description of the dependency"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Creation timestamp"
            }
        }
    }
}


COMPLETION_REPORTS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["enhancement_id", "report_path", "completion_date", "created_at"],
        "properties": {
            "enhancement_id": {
                "bsonType": "objectId",
                "description": "Foreign key to enhancements collection"
            },
            "report_path": {
                "bsonType": "string",
                "minLength": 1,
                "description": "File path to completion report (e.g., docs/enhancements/ENHANCEMENT_001_COMPLETE.md)"
            },
            "report_content": {
                "bsonType": "string",
                "description": "Optional: Store full report content in database"
            },
            "completion_date": {
                "bsonType": "date",
                "description": "Date the enhancement was completed"
            },
            "metrics": {
                "bsonType": "object",
                "description": "Optional metrics (lines_of_code, tests_added, etc.)"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Report creation timestamp"
            }
        }
    }
}


PROGRESS_SNAPSHOTS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "project_id", "snapshot_date", "total_enhancements",
            "completed", "in_progress", "planned", "completion_percentage",
            "created_at"
        ],
        "properties": {
            "project_id": {
                "bsonType": "objectId",
                "description": "Foreign key to projects collection"
            },
            "snapshot_date": {
                "bsonType": "date",
                "description": "Date of this progress snapshot"
            },
            "total_enhancements": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Total number of enhancements"
            },
            "completed": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Number of completed enhancements"
            },
            "in_progress": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Number of in-progress enhancements"
            },
            "planned": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Number of planned enhancements"
            },
            "blocked": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Number of blocked enhancements"
            },
            "completion_percentage": {
                "bsonType": "double",
                "minimum": 0,
                "maximum": 100,
                "description": "Overall completion percentage"
            },
            "estimated_total_hours": {
                "bsonType": "double",
                "minimum": 0,
                "description": "Total estimated hours for all enhancements"
            },
            "actual_total_hours": {
                "bsonType": "double",
                "minimum": 0,
                "description": "Total actual hours spent"
            },
            "velocity": {
                "bsonType": "object",
                "properties": {
                    "enhancements_per_week": {"bsonType": "double"},
                    "hours_per_week": {"bsonType": "double"},
                    "avg_completion_time_days": {"bsonType": "double"}
                },
                "description": "Velocity metrics"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Snapshot creation timestamp"
            }
        }
    }
}


async def create_collection_with_validation(db, collection_name: str, validator: dict, dry_run: bool = False):
    """Create a collection with schema validation."""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Creating collection: {collection_name}")

    if dry_run:
        print(f"  Would create collection with validator:")
        print(f"  - Required fields: {validator['$jsonSchema'].get('required', [])}")
        print(f"  - Total properties: {len(validator['$jsonSchema'].get('properties', {}))}")
        return True

    try:
        await db.create_collection(collection_name, validator=validator)
        print(f"  ✅ Collection '{collection_name}' created successfully")
        return True
    except CollectionInvalid:
        print(f"  ⚠️  Collection '{collection_name}' already exists, updating validator...")
        try:
            await db.command({
                "collMod": collection_name,
                "validator": validator,
                "validationLevel": "strict",
                "validationAction": "error"
            })
            print(f"  ✅ Validator updated for '{collection_name}'")
            return True
        except Exception as e:
            print(f"  ❌ Failed to update validator: {e}")
            return False
    except Exception as e:
        print(f"  ❌ Failed to create collection: {e}")
        return False


async def create_indexes(db, dry_run: bool = False):
    """Create indexes for all collections."""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Creating indexes...")

    indexes = [
        # Projects indexes
        ("projects", [("project_tag", 1)], {"unique": True, "name": "project_tag_unique"}),
        ("projects", [("created_at", -1)], {"name": "created_at_desc"}),

        # Enhancements indexes
        ("enhancements", [("project_id", 1), ("enhancement_number", 1)],
         {"unique": True, "name": "project_enhancement_unique"}),
        ("enhancements", [("project_id", 1), ("status", 1)], {"name": "project_status"}),
        ("enhancements", [("priority", 1), ("status", 1)], {"name": "priority_status"}),
        ("enhancements", [("phase", 1)], {"name": "phase"}),
        ("enhancements", [("tags", 1)], {"name": "tags"}),
        ("enhancements", [("completion_date", -1)], {"name": "completion_date_desc"}),
        ("enhancements", [("status", 1), ("phase", 1)], {"name": "status_phase"}),

        # Dependencies indexes
        ("dependencies", [("enhancement_id", 1)], {"name": "enhancement_id"}),
        ("dependencies", [("depends_on_id", 1)], {"name": "depends_on_id"}),
        ("dependencies", [("enhancement_id", 1), ("depends_on_id", 1)],
         {"unique": True, "sparse": True, "name": "enhancement_dependency_unique"}),

        # Completion reports indexes
        ("completion_reports", [("enhancement_id", 1)], {"name": "enhancement_id"}),
        ("completion_reports", [("completion_date", -1)], {"name": "completion_date_desc"}),

        # Progress snapshots indexes
        ("progress_snapshots", [("project_id", 1), ("snapshot_date", -1)],
         {"name": "project_snapshot_date"}),
        ("progress_snapshots", [("project_id", 1), ("snapshot_date", 1)],
         {"unique": True, "name": "project_snapshot_unique"}),
    ]

    success_count = 0
    for collection_name, keys, options in indexes:
        try:
            if dry_run:
                print(f"  Would create index on {collection_name}: {keys}")
            else:
                await db[collection_name].create_index(keys, **options)
                print(f"  ✅ Created index '{options['name']}' on {collection_name}")
            success_count += 1
        except Exception as e:
            print(f"  ⚠️  Index '{options['name']}' on {collection_name}: {e}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Created {success_count}/{len(indexes)} indexes")
    return success_count == len(indexes)


async def drop_collections(db, dry_run: bool = False):
    """Drop all enhancement tracking collections."""
    collections = ["projects", "enhancements", "dependencies", "completion_reports", "progress_snapshots"]

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Dropping existing collections...")

    for collection_name in collections:
        if dry_run:
            print(f"  Would drop collection: {collection_name}")
        else:
            try:
                await db.drop_collection(collection_name)
                print(f"  ✅ Dropped collection: {collection_name}")
            except Exception as e:
                print(f"  ⚠️  Could not drop {collection_name}: {e}")


async def verify_collections(db):
    """Verify all collections were created successfully."""
    print("\n🔍 Verifying collections...")

    expected_collections = ["projects", "enhancements", "dependencies", "completion_reports", "progress_snapshots"]
    existing_collections = await db.list_collection_names()

    all_exist = True
    for collection_name in expected_collections:
        if collection_name in existing_collections:
            # Count documents
            count = await db[collection_name].count_documents({})
            print(f"  ✅ {collection_name}: exists ({count} documents)")
        else:
            print(f"  ❌ {collection_name}: missing")
            all_exist = False

    return all_exist


async def test_schema_validation(db):
    """Test schema validation with valid and invalid documents."""
    print("\n🧪 Testing schema validation...")

    # Test valid project document
    try:
        valid_project = {
            "project_name": "Test Project",
            "project_tag": "test_project",
            "version": "0.1.0",
            "owner": "Test Team",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.projects.insert_one(valid_project)
        print(f"  ✅ Valid project document accepted (ID: {result.inserted_id})")
        await db.projects.delete_one({"_id": result.inserted_id})
    except Exception as e:
        print(f"  ❌ Valid project document rejected: {e}")

    # Test invalid project document (missing required field)
    try:
        invalid_project = {
            "project_name": "Test Project",
            "project_tag": "test_project",
            # Missing version and owner
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.projects.insert_one(invalid_project)
        print(f"  ❌ Invalid project document was accepted (should have been rejected)")
    except Exception as e:
        print(f"  ✅ Invalid project document correctly rejected: {type(e).__name__}")

    # Test invalid project tag format
    try:
        invalid_tag = {
            "project_name": "Test Project",
            "project_tag": "Invalid-Tag",  # Contains hyphen (not allowed)
            "version": "0.1.0",
            "owner": "Test Team",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.projects.insert_one(invalid_tag)
        print(f"  ❌ Invalid tag format was accepted (should have been rejected)")
    except Exception as e:
        print(f"  ✅ Invalid tag format correctly rejected: {type(e).__name__}")


async def main():
    """Main function to create all collections and indexes."""
    parser = argparse.ArgumentParser(description="Create MongoDB collections for enhancement tracking")
    parser.add_argument("--drop", action="store_true", help="Drop existing collections first")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without making changes")
    parser.add_argument("--url", default=MONGODB_URL, help=f"MongoDB URL (default: {MONGODB_URL})")
    parser.add_argument("--database", default=DATABASE_NAME, help=f"Database name (default: {DATABASE_NAME})")
    parser.add_argument("--test", action="store_true", help="Run schema validation tests")

    args = parser.parse_args()

    print("=" * 70)
    print("MongoDB Enhancement Tracking Collections Setup")
    print("=" * 70)
    print(f"MongoDB URL: {args.url}")
    print(f"Database: {args.database}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 70)

    # Connect to MongoDB
    try:
        client = AsyncIOMotorClient(args.url)
        db = client[args.database]

        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully\n")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    # Drop existing collections if requested
    if args.drop:
        await drop_collections(db, args.dry_run)

    # Create collections with validation
    collections = [
        ("projects", PROJECTS_VALIDATOR),
        ("enhancements", ENHANCEMENTS_VALIDATOR),
        ("dependencies", DEPENDENCIES_VALIDATOR),
        ("completion_reports", COMPLETION_REPORTS_VALIDATOR),
        ("progress_snapshots", PROGRESS_SNAPSHOTS_VALIDATOR),
    ]

    success_count = 0
    for collection_name, validator in collections:
        if await create_collection_with_validation(db, collection_name, validator, args.dry_run):
            success_count += 1

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Created {success_count}/{len(collections)} collections")

    # Create indexes
    if not args.dry_run or args.dry_run:
        await create_indexes(db, args.dry_run)

    # Verify collections (skip in dry run)
    if not args.dry_run:
        all_exist = await verify_collections(db)

        # Run validation tests if requested
        if args.test:
            await test_schema_validation(db)

        if all_exist:
            print("\n" + "=" * 70)
            print("✅ All collections created successfully!")
            print("=" * 70)
            print("\nNext steps:")
            print("  1. Implement repository classes: src/db/repositories/")
            print("  2. Create migration script: scripts/migrate_yaml_to_db.py")
            print("  3. Add API endpoints: src/api/main.py")
            print("  4. Run tests: pytest tests/test_enhancement_repository.py")
        else:
            print("\n⚠️  Some collections are missing. Check errors above.")
            sys.exit(1)
    else:
        print("\n" + "=" * 70)
        print("✅ Dry run completed - no changes made")
        print("=" * 70)
        print("\nRun without --dry-run to create collections")

    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
