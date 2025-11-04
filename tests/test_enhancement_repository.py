"""
Unit tests for enhancement database repository.

Tests CRUD operations, filtering, and business logic for enhancement tracking.
"""

import pytest
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import AsyncGenerator

from src.db.repositories.mongo_enhancement_repository import MongoEnhancementRepository
from src.db.schemas.enhancement_schemas import (
    Enhancement,
    Project,
    Dependency,
    CompletionReport,
    ProgressSnapshot
)


# Test configuration
TEST_DATABASE_NAME = "ai_orchestrator_test"
TEST_MONGODB_URL = "mongodb://localhost:27017"


@pytest.fixture
async def test_db() -> AsyncGenerator:
    """Create test database connection."""
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    db = client[TEST_DATABASE_NAME]

    yield db

    # Cleanup: Drop test database after tests
    await client.drop_database(TEST_DATABASE_NAME)
    client.close()


@pytest.fixture
async def repository(test_db) -> MongoEnhancementRepository:
    """Create repository instance with test database."""
    return MongoEnhancementRepository(test_db)


@pytest.fixture
async def sample_project(repository: MongoEnhancementRepository) -> Project:
    """Create a sample project for testing."""
    project = Project(
        project_name="Test Project",
        project_tag="test_project",
        version="1.0.0",
        owner="test_user",
        description="A test project for enhancement testing",
        technologies=["Python", "MongoDB"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await repository.create_project(project)
    return project


@pytest.fixture
async def sample_enhancement(
    repository: MongoEnhancementRepository,
    sample_project: Project
) -> Enhancement:
    """Create a sample enhancement for testing."""
    enhancement = Enhancement(
        project_tag="test_project",
        enhancement_number="001",
        title="Test Enhancement",
        category="Feature",
        priority="high",
        status="In Progress",
        phase=1,
        description="A test enhancement for unit testing",
        success_criteria=["Criteria 1", "Criteria 2"],
        deliverables=["Deliverable 1"],
        estimated_hours=10.0,
        actual_hours=5.0,
        completion_percentage=50,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await repository.create_enhancement(enhancement)
    return enhancement


# ============================================================================
# Project Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_project(repository: MongoEnhancementRepository):
    """Test creating a new project."""
    project = Project(project_name="New Project", project_tag="new_project", version="1.0.0", owner="test_user", description="Test project creation",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    project_id = await repository.create_project(project)

    assert project_id is not None
    assert isinstance(project_id, str)

    # Verify project was created
    retrieved = await repository.get_project("new_project")
    assert retrieved is not None
    assert retrieved.project_tag == "new_project"
    assert retrieved.name == "New Project"


@pytest.mark.asyncio
async def test_get_all_projects(
    repository: MongoEnhancementRepository,
    sample_project: Project
):
    """Test retrieving all projects."""
    # Create another project
    project2 = Project(project_name="Project 2", project_tag="project2", version="1.0.0", owner="test_user", description="Second test project",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await repository.create_project(project2)

    # Get all projects
    projects = await repository.get_all_projects()

    assert len(projects) >= 2
    project_tags = [p.project_tag for p in projects]
    assert "test_project" in project_tags
    assert "project2" in project_tags


@pytest.mark.asyncio
async def test_update_project(
    repository: MongoEnhancementRepository,
    sample_project: Project
):
    """Test updating project information."""
    updates = {
        "name": "Updated Project Name",
        "description": "Updated description"
    }

    success = await repository.update_project("test_project", updates)

    assert success is True

    # Verify updates
    updated = await repository.get_project("test_project")
    assert updated.name == "Updated Project Name"
    assert updated.description == "Updated description"


@pytest.mark.asyncio
async def test_delete_project(
    repository: MongoEnhancementRepository,
    sample_project: Project
):
    """Test deleting a project."""
    success = await repository.delete_project("test_project")

    assert success is True

    # Verify project was deleted
    deleted = await repository.get_project("test_project")
    assert deleted is None


# ============================================================================
# Enhancement Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_enhancement(
    repository: MongoEnhancementRepository,
    sample_project: Project
):
    """Test creating a new enhancement."""
    enhancement = Enhancement(
        project_tag="test_project",
        enhancement_number="002",
        title="New Enhancement",
        category="Bug Fix",
        priority="medium",
        status="Pending",
        phase=1,
        description="Test enhancement creation",
        success_criteria=["Criterion 1"],
        deliverables=["Deliverable 1"],
        estimated_hours=8.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    enhancement_id = await repository.create_enhancement(enhancement)

    assert enhancement_id is not None
    assert isinstance(enhancement_id, str)

    # Verify enhancement was created
    retrieved = await repository.get_enhancement("test_project", "002")
    assert retrieved is not None
    assert retrieved.enhancement_number == "002"
    assert retrieved.title == "New Enhancement"


@pytest.mark.asyncio
async def test_get_enhancements_with_filters(
    repository: MongoEnhancementRepository,
    sample_project: Project,
    sample_enhancement: Enhancement
):
    """Test retrieving enhancements with filters."""
    # Create additional enhancements with different attributes
    enh2 = Enhancement(
        project_tag="test_project",
        enhancement_number="002",
        title="Enhancement 2",
        category="Feature",
        priority="low",
        status="Complete",
        phase=1,
        description="Second enhancement",
        estimated_hours=5.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await repository.create_enhancement(enh2)

    enh3 = Enhancement(
        project_tag="test_project",
        enhancement_number="003",
        title="Enhancement 3",
        category="Feature",
        priority="high",
        status="In Progress",
        phase=2,
        description="Third enhancement",
        estimated_hours=15.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await repository.create_enhancement(enh3)

    # Test filtering by status
    in_progress = await repository.get_enhancements(
        project_tag="test_project",
        status="In Progress"
    )
    assert len(in_progress) == 2

    # Test filtering by priority
    high_priority = await repository.get_enhancements(
        project_tag="test_project",
        priority="high"
    )
    assert len(high_priority) == 2

    # Test filtering by phase
    phase_2 = await repository.get_enhancements(
        project_tag="test_project",
        phase=2
    )
    assert len(phase_2) == 1
    assert phase_2[0].enhancement_number == "003"


@pytest.mark.asyncio
async def test_update_enhancement(
    repository: MongoEnhancementRepository,
    sample_enhancement: Enhancement
):
    """Test updating enhancement."""
    updates = {
        "status": "Complete",
        "completion_percentage": 100,
        "actual_hours": 12.0
    }

    success = await repository.update_enhancement(
        "test_project",
        "001",
        updates
    )

    assert success is True

    # Verify updates
    updated = await repository.get_enhancement("test_project", "001")
    assert updated.status == "Complete"
    assert updated.completion_percentage == 100
    assert updated.actual_hours == 12.0


@pytest.mark.asyncio
async def test_delete_enhancement(
    repository: MongoEnhancementRepository,
    sample_enhancement: Enhancement
):
    """Test deleting an enhancement."""
    success = await repository.delete_enhancement("test_project", "001")

    assert success is True

    # Verify enhancement was deleted
    deleted = await repository.get_enhancement("test_project", "001")
    assert deleted is None


@pytest.mark.asyncio
async def test_search_enhancements(
    repository: MongoEnhancementRepository,
    sample_project: Project,
    sample_enhancement: Enhancement
):
    """Test searching enhancements by text."""
    # Create another enhancement with specific keywords
    enh2 = Enhancement(
        project_tag="test_project",
        enhancement_number="002",
        title="Database Performance Optimization",
        category="Performance",
        priority="high",
        status="In Progress",
        phase=1,
        description="Optimize database queries for better performance",
        estimated_hours=20.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await repository.create_enhancement(enh2)

    # Search for "database"
    results = await repository.search_enhancements(
        project_tag="test_project",
        search_term="database"
    )

    assert len(results) >= 1
    assert any("Database" in e.title for e in results)


# ============================================================================
# Dependency Tests
# ============================================================================

@pytest.mark.asyncio
async def test_add_dependency(
    repository: MongoEnhancementRepository,
    sample_project: Project,
    sample_enhancement: Enhancement
):
    """Test adding enhancement dependency."""
    # Create another enhancement to depend on
    enh2 = Enhancement(
        project_tag="test_project",
        enhancement_number="002",
        title="Dependent Enhancement",
        category="Feature",
        priority="medium",
        status="Pending",
        phase=1,
        description="Depends on enhancement 001",
        estimated_hours=5.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await repository.create_enhancement(enh2)

    # Add dependency
    dependency = Dependency(
        enhancement_id="002",
        depends_on="001",
        dependency_type="blocking"
    )

    dep_id = await repository.add_dependency(dependency)

    assert dep_id is not None

    # Get dependencies
    deps = await repository.get_dependencies("002")
    assert len(deps) == 1
    assert deps[0].depends_on == "001"


# ============================================================================
# Progress Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_progress(
    repository: MongoEnhancementRepository,
    sample_project: Project,
    sample_enhancement: Enhancement
):
    """Test getting project progress statistics."""
    # Create more enhancements with different statuses
    enh2 = Enhancement(
        project_tag="test_project",
        enhancement_number="002",
        title="Enhancement 2",
        category="Feature",
        priority="medium",
        status="Complete",
        phase=1,
        description="Completed enhancement",
        estimated_hours=10.0,
        actual_hours=12.0,
        completion_percentage=100,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await repository.create_enhancement(enh2)

    # Get progress
    progress = await repository.get_progress("test_project")

    assert progress.project_tag == "test_project"
    assert progress.total_enhancements == 2
    assert progress.completed_enhancements == 1
    assert progress.in_progress_enhancements == 1
    assert progress.overall_progress == 50.0  # Average of 50% and 100%


@pytest.mark.asyncio
async def test_create_progress_snapshot(
    repository: MongoEnhancementRepository,
    sample_project: Project,
    sample_enhancement: Enhancement
):
    """Test creating progress snapshot."""
    snapshot_id = await repository.create_progress_snapshot("test_project")

    assert snapshot_id is not None

    # Verify snapshot was created
    snapshots = await repository.get_progress_history(
        "test_project",
        limit=1
    )

    assert len(snapshots) == 1
    assert snapshots[0].project_tag == "test_project"


# ============================================================================
# Completion Report Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_completion_report(
    repository: MongoEnhancementRepository,
    sample_enhancement: Enhancement
):
    """Test creating completion report."""
    report = CompletionReport(
        enhancement_id="001",
        completed_at=datetime.now(timezone.utc),
        completion_notes="Successfully completed all requirements",
        lessons_learned=["Lesson 1", "Lesson 2"],
        created_at=datetime.now(timezone.utc)
    )

    report_id = await repository.create_completion_report(report)

    assert report_id is not None

    # Verify report was created
    retrieved = await repository.get_completion_report("001")
    assert retrieved is not None
    assert retrieved.enhancement_id == "001"
    assert len(retrieved.lessons_learned) == 2


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_get_nonexistent_project(repository: MongoEnhancementRepository):
    """Test retrieving non-existent project."""
    project = await repository.get_project("nonexistent")
    assert project is None


@pytest.mark.asyncio
async def test_get_nonexistent_enhancement(repository: MongoEnhancementRepository):
    """Test retrieving non-existent enhancement."""
    enhancement = await repository.get_enhancement("test_project", "999")
    assert enhancement is None


@pytest.mark.asyncio
async def test_update_nonexistent_project(repository: MongoEnhancementRepository):
    """Test updating non-existent project."""
    success = await repository.update_project("nonexistent", {"name": "Updated"})
    assert success is False


@pytest.mark.asyncio
async def test_delete_nonexistent_enhancement(repository: MongoEnhancementRepository):
    """Test deleting non-existent enhancement."""
    success = await repository.delete_enhancement("test_project", "999")
    assert success is False


@pytest.mark.asyncio
async def test_empty_search_results(
    repository: MongoEnhancementRepository,
    sample_project: Project
):
    """Test search with no results."""
    results = await repository.search_enhancements(
        project_tag="test_project",
        search_term="nonexistent_keyword_xyz"
    )

    assert len(results) == 0


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_bulk_enhancement_creation(
    repository: MongoEnhancementRepository,
    sample_project: Project
):
    """Test creating multiple enhancements efficiently."""
    import time

    start_time = time.time()

    # Create 50 enhancements
    for i in range(50):
        enhancement = Enhancement(
            project_tag="test_project",
            enhancement_number=f"{i+100:03d}",
            title=f"Enhancement {i+100}",
            category="Feature",
            priority="medium",
            status="Pending",
            phase=1,
            description=f"Bulk test enhancement {i+100}",
            estimated_hours=5.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await repository.create_enhancement(enhancement)

    elapsed_time = time.time() - start_time

    # Should complete in reasonable time (< 10 seconds)
    assert elapsed_time < 10.0

    # Verify all were created
    enhancements = await repository.get_enhancements(project_tag="test_project")
    assert len(enhancements) >= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
