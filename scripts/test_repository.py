#!/usr/bin/env python3
"""
Test script for enhancement repository.

Tests basic CRUD operations on the MongoDB repository.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

from src.db.repositories.mongo_enhancement_repository import MongoEnhancementRepository
from src.db.schemas.enhancement_schemas import Project, Enhancement


async def test_repository():
    """Test repository operations."""
    print("=" * 70)
    print("Testing Enhancement Repository")
    print("=" * 70)

    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.ai_orchestrator
    repo = MongoEnhancementRepository(db)

    # Test 1: Create a test project
    print("\n1. Creating test project...")
    test_project = Project(
        project_name="Test Project",
        project_tag="test_project",
        version="0.1.0",
        owner="Test Team",
        description="Test project for repository",
        technologies=["Python", "MongoDB"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    try:
        project_id = await repo.create_project(test_project)
        print(f"   ✅ Project created: {project_id}")
    except Exception as e:
        print(f"   ⚠️  Project might already exist: {e}")

    # Test 2: Get project
    print("\n2. Getting project...")
    project = await repo.get_project("test_project")
    if project:
        print(f"   ✅ Project retrieved: {project.project_name}")
    else:
        print("   ❌ Project not found")
        return

    # Test 3: Create enhancement
    print("\n3. Creating test enhancement...")
    test_enhancement = Enhancement(
        project_id=project.id,
        enhancement_number="001",
        db_reference="db-uuid-test-001",
        title="Test Enhancement",
        category="Testing",
        priority="High",
        status="Planned",
        phase=1,
        impact="Test impact",
        estimated_hours=4.0,
        completion_percentage=0,
        technical_summary="This is a test enhancement",
        success_criteria=["Test passes"],
        deliverables=["Test deliverable"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    try:
        enh_id = await repo.create_enhancement("test_project", test_enhancement)
        print(f"   ✅ Enhancement created: {enh_id}")
    except Exception as e:
        print(f"   ⚠️  Enhancement might already exist: {e}")

    # Test 4: Get enhancements
    print("\n4. Getting enhancements...")
    enhancements = await repo.get_enhancements("test_project")
    print(f"   ✅ Found {len(enhancements)} enhancements")
    for enh in enhancements:
        print(f"      - {enh.enhancement_number}: {enh.title} ({enh.status})")

    # Test 5: Update enhancement
    print("\n5. Updating enhancement...")
    success = await repo.update_enhancement(
        "test_project",
        "001",
        {"status": "In Progress", "completion_percentage": 50}
    )
    if success:
        print("   ✅ Enhancement updated")
    else:
        print("   ❌ Update failed")

    # Test 6: Get specific enhancement
    print("\n6. Getting specific enhancement...")
    enh_response = await repo.get_enhancement("test_project", "001")
    if enh_response:
        print(f"   ✅ Enhancement: {enh_response.title}")
        print(f"      Status: {enh_response.status}")
        print(f"      Completion: {enh_response.completion_percentage}%")
    else:
        print("   ❌ Enhancement not found")

    # Test 7: Get progress
    print("\n7. Getting progress statistics...")
    progress = await repo.get_progress("test_project")
    print(f"   ✅ Progress:")
    print(f"      Total: {progress.total_enhancements}")
    print(f"      Completed: {progress.completed}")
    print(f"      In Progress: {progress.in_progress}")
    print(f"      Planned: {progress.planned}")
    print(f"      Completion: {progress.completion_percentage}%")

    # Test 8: Create progress snapshot
    print("\n8. Creating progress snapshot...")
    snapshot_id = await repo.create_progress_snapshot("test_project")
    print(f"   ✅ Snapshot created: {snapshot_id}")

    # Test 9: Get progress history
    print("\n9. Getting progress history...")
    snapshots = await repo.get_progress_history("test_project")
    print(f"   ✅ Found {len(snapshots)} snapshots")
    for snap in snapshots[:3]:  # Show first 3
        print(f"      - {snap.snapshot_date.strftime('%Y-%m-%d')}: {snap.completion_percentage}%")

    # Test 10: Search enhancements
    print("\n10. Searching enhancements...")
    results = await repo.search_enhancements("test_project", "Test")
    print(f"   ✅ Found {len(results)} matching enhancements")

    # Test 11: Get all projects
    print("\n11. Getting all projects...")
    projects = await repo.get_all_projects()
    print(f"   ✅ Found {len(projects)} projects")
    for proj in projects:
        print(f"      - {proj.project_tag}: {proj.total_enhancements} enhancements ({proj.completion_percentage}%)")

    # Cleanup (optional)
    print("\n12. Cleanup...")
    choice = input("   Delete test project? (y/n): ")
    if choice.lower() == 'y':
        await repo.delete_project("test_project")
        print("   ✅ Test project deleted")
    else:
        print("   ⚠️  Test project kept for inspection")

    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)

    client.close()


if __name__ == "__main__":
    asyncio.run(test_repository())
