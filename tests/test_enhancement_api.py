"""
Integration tests for enhancement tracking API endpoints.

Tests the REST API endpoints for projects, enhancements, and related operations.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

from src.api.main import app


# Test configuration
TEST_DATABASE_NAME = "ai_orchestrator_test"
TEST_MONGODB_URL = "mongodb://localhost:27017"


@pytest.fixture
async def test_client():
    """Create test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
async def setup_teardown_db():
    """Setup and teardown test database."""
    # Setup: Create test database
    client = AsyncIOMotorClient(TEST_MONGODB_URL)

    yield

    # Teardown: Drop test database
    await client.drop_database(TEST_DATABASE_NAME)
    client.close()


# ============================================================================
# Project API Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_project_api(test_client: AsyncClient):
    """Test POST /api/v1/enhancements/projects endpoint."""
    project_data = {
        "project_tag": "test_api_project",
        "name": "Test API Project",
        "description": "Project created via API test"
    }

    response = await test_client.post(
        "/api/v1/enhancements/projects",
        json=project_data
    )

    assert response.status_code == 201
    data = response.json()
    assert "project_id" in data
    assert data["project_tag"] == "test_api_project"


@pytest.mark.asyncio
async def test_get_all_projects_api(test_client: AsyncClient):
    """Test GET /api/v1/enhancements/projects endpoint."""
    # Create a project first
    project_data = {
        "project_tag": "project1",
        "name": "Project 1",
        "description": "First project"
    }
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    # Get all projects
    response = await test_client.get("/api/v1/enhancements/projects")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(p["project_tag"] == "project1" for p in data)


@pytest.mark.asyncio
async def test_get_project_by_tag_api(test_client: AsyncClient):
    """Test GET /api/v1/enhancements/projects/{project_tag} endpoint."""
    # Create a project
    project_data = {
        "project_tag": "specific_project",
        "name": "Specific Project",
        "description": "Test get by tag"
    }
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    # Get specific project
    response = await test_client.get("/api/v1/enhancements/projects/specific_project")

    assert response.status_code == 200
    data = response.json()
    assert data["project_tag"] == "specific_project"
    assert data["name"] == "Specific Project"


@pytest.mark.asyncio
async def test_update_project_api(test_client: AsyncClient):
    """Test PUT /api/v1/enhancements/projects/{project_tag} endpoint."""
    # Create a project
    project_data = {
        "project_tag": "update_project",
        "name": "Original Name",
        "description": "Original description"
    }
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    # Update project
    updates = {
        "name": "Updated Name",
        "description": "Updated description"
    }
    response = await test_client.put(
        "/api/v1/enhancements/projects/update_project",
        json=updates
    )

    assert response.status_code == 200

    # Verify update
    get_response = await test_client.get("/api/v1/enhancements/projects/update_project")
    data = get_response.json()
    assert data["name"] == "Updated Name"


# ============================================================================
# Enhancement API Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_enhancement_api(test_client: AsyncClient):
    """Test POST /api/v1/enhancements/projects/{project_tag}/enhancements endpoint."""
    # Create project first
    project_data = {"project_tag": "test_proj", "name": "Test Project"}
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    # Create enhancement
    enhancement_data = {
        "enhancement_number": "001",
        "title": "Test Enhancement",
        "category": "Feature",
        "priority": "high",
        "status": "Pending",
        "phase": 1,
        "description": "Test enhancement via API",
        "estimated_hours": 10.0
    }

    response = await test_client.post(
        "/api/v1/enhancements/projects/test_proj/enhancements",
        json=enhancement_data
    )

    assert response.status_code == 201
    data = response.json()
    assert "enhancement_id" in data
    assert data["enhancement_number"] == "001"


@pytest.mark.asyncio
async def test_get_enhancements_with_filters_api(test_client: AsyncClient):
    """Test GET /api/v1/enhancements/projects/{project_tag}/enhancements with filters."""
    # Setup: Create project and multiple enhancements
    project_data = {"project_tag": "filter_proj", "name": "Filter Test Project"}
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    enhancements = [
        {"enhancement_number": "001", "title": "Enh 1", "status": "In Progress", "priority": "high", "phase": 1},
        {"enhancement_number": "002", "title": "Enh 2", "status": "Complete", "priority": "medium", "phase": 1},
        {"enhancement_number": "003", "title": "Enh 3", "status": "In Progress", "priority": "high", "phase": 2},
    ]

    for enh in enhancements:
        enh.update({"category": "Feature", "description": "Test", "estimated_hours": 5.0})
        await test_client.post(
            "/api/v1/enhancements/projects/filter_proj/enhancements",
            json=enh
        )

    # Test filtering by status
    response = await test_client.get(
        "/api/v1/enhancements/projects/filter_proj/enhancements?status=In%20Progress"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test filtering by priority
    response = await test_client.get(
        "/api/v1/enhancements/projects/filter_proj/enhancements?priority=high"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test filtering by phase
    response = await test_client.get(
        "/api/v1/enhancements/projects/filter_proj/enhancements?phase=2"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_enhancement_by_number_api(test_client: AsyncClient):
    """Test GET /api/v1/enhancements/projects/{project_tag}/enhancements/{enhancement_number}."""
    # Setup
    project_data = {"project_tag": "get_proj", "name": "Get Test Project"}
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    enhancement_data = {
        "enhancement_number": "123",
        "title": "Specific Enhancement",
        "category": "Feature",
        "priority": "high",
        "status": "Pending",
        "phase": 1,
        "description": "Test get by number",
        "estimated_hours": 10.0
    }
    await test_client.post(
        "/api/v1/enhancements/projects/get_proj/enhancements",
        json=enhancement_data
    )

    # Get specific enhancement
    response = await test_client.get(
        "/api/v1/enhancements/projects/get_proj/enhancements/123"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["enhancement_number"] == "123"
    assert data["title"] == "Specific Enhancement"


@pytest.mark.asyncio
async def test_update_enhancement_api(test_client: AsyncClient):
    """Test PUT /api/v1/enhancements/projects/{project_tag}/enhancements/{enhancement_number}."""
    # Setup
    project_data = {"project_tag": "update_proj", "name": "Update Test Project"}
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    enhancement_data = {
        "enhancement_number": "456",
        "title": "Original Title",
        "category": "Feature",
        "priority": "medium",
        "status": "Pending",
        "phase": 1,
        "description": "Original description",
        "estimated_hours": 10.0
    }
    await test_client.post(
        "/api/v1/enhancements/projects/update_proj/enhancements",
        json=enhancement_data
    )

    # Update enhancement
    updates = {
        "status": "In Progress",
        "completion_percentage": 50,
        "actual_hours": 5.0
    }
    response = await test_client.put(
        "/api/v1/enhancements/projects/update_proj/enhancements/456",
        json=updates
    )

    assert response.status_code == 200

    # Verify update
    get_response = await test_client.get(
        "/api/v1/enhancements/projects/update_proj/enhancements/456"
    )
    data = get_response.json()
    assert data["status"] == "In Progress"
    assert data["completion_percentage"] == 50


# ============================================================================
# Progress API Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_progress_api(test_client: AsyncClient):
    """Test GET /api/v1/enhancements/projects/{project_tag}/progress endpoint."""
    # Setup: Create project and enhancements
    project_data = {"project_tag": "progress_proj", "name": "Progress Test Project"}
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    enhancements = [
        {"enhancement_number": "001", "title": "Enh 1", "status": "Complete", "completion_percentage": 100},
        {"enhancement_number": "002", "title": "Enh 2", "status": "In Progress", "completion_percentage": 50},
    ]

    for enh in enhancements:
        enh.update({
            "category": "Feature",
            "priority": "medium",
            "phase": 1,
            "description": "Test",
            "estimated_hours": 10.0
        })
        await test_client.post(
            "/api/v1/enhancements/projects/progress_proj/enhancements",
            json=enh
        )

    # Get progress
    response = await test_client.get(
        "/api/v1/enhancements/projects/progress_proj/progress"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["project_tag"] == "progress_proj"
    assert data["total_enhancements"] == 2
    assert data["completed_enhancements"] == 1
    assert data["in_progress_enhancements"] == 1
    assert data["overall_progress"] == 75.0  # (100 + 50) / 2


# ============================================================================
# Search API Tests
# ============================================================================

@pytest.mark.asyncio
async def test_search_enhancements_api(test_client: AsyncClient):
    """Test GET /api/v1/enhancements/projects/{project_tag}/search endpoint."""
    # Setup
    project_data = {"project_tag": "search_proj", "name": "Search Test Project"}
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    enhancements = [
        {"enhancement_number": "001", "title": "Database Optimization", "description": "Optimize database queries"},
        {"enhancement_number": "002", "title": "API Rate Limiting", "description": "Add rate limiting to API"},
    ]

    for enh in enhancements:
        enh.update({
            "category": "Feature",
            "priority": "medium",
            "status": "Pending",
            "phase": 1,
            "estimated_hours": 10.0
        })
        await test_client.post(
            "/api/v1/enhancements/projects/search_proj/enhancements",
            json=enh
        )

    # Search for "database"
    response = await test_client.get(
        "/api/v1/enhancements/projects/search_proj/search?q=database"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Database" in e["title"] for e in data)


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_nonexistent_project_api(test_client: AsyncClient):
    """Test getting non-existent project returns 404."""
    response = await test_client.get("/api/v1/enhancements/projects/nonexistent")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_enhancement_without_project_api(test_client: AsyncClient):
    """Test creating enhancement for non-existent project."""
    enhancement_data = {
        "enhancement_number": "001",
        "title": "Test Enhancement",
        "category": "Feature",
        "priority": "high",
        "status": "Pending",
        "phase": 1,
        "description": "Test",
        "estimated_hours": 10.0
    }

    response = await test_client.post(
        "/api/v1/enhancements/projects/nonexistent/enhancements",
        json=enhancement_data
    )

    # Should fail or create project automatically depending on implementation
    assert response.status_code in [201, 400, 404]


@pytest.mark.asyncio
async def test_invalid_enhancement_data_api(test_client: AsyncClient):
    """Test creating enhancement with invalid data."""
    # Create project first
    project_data = {"project_tag": "valid_proj", "name": "Valid Project"}
    await test_client.post("/api/v1/enhancements/projects", json=project_data)

    # Try to create enhancement with missing required fields
    invalid_data = {
        "enhancement_number": "001"
        # Missing required fields
    }

    response = await test_client.post(
        "/api/v1/enhancements/projects/valid_proj/enhancements",
        json=invalid_data
    )

    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
