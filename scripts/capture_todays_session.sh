#!/bin/bash
#
# Capture today's session and create growth reflection
#

API_URL="http://localhost:8000"

echo "================================================================================"
echo "Capturing Today's Session (November 2, 2025)"
echo "Enhancement 012 Phase 2: Enhancement Tracking Database"
echo "================================================================================"

curl -X POST "${API_URL}/api/growth/sessions/auto-capture" \
  -H "Content-Type: application/json" \
  -d '{
    "enhancement_id": "012",
    "enhancement_title": "State Management & Persistence Layer - Phase 2",
    "accomplishments": [
      "Created MongoDB schema validation with 5 collections (projects, enhancements, dependencies, completion_reports, progress_snapshots)",
      "Implemented repository pattern with BaseEnhancementRepository interface and MongoEnhancementRepository (25 methods, 506 lines)",
      "Built production-ready migration script with dry-run, rollback, and validation (600+ lines)",
      "Migrated 18 enhancements, 22 dependencies, and 5 completion reports from YAML to MongoDB successfully",
      "Developed comprehensive REST API with 15+ endpoints for enhancement CRUD operations",
      "Fixed Pydantic v2 compatibility issues across all schemas",
      "Implemented automatic session tracking system with growth reflection generation",
      "Created comprehensive documentation (88-page ENHANCEMENT_TRACKING_DATABASE.md)"
    ],
    "topics": [
      "MongoDB schema validation with JSON Schema",
      "Motor async MongoDB driver for Python",
      "Pydantic v2 data validation and serialization",
      "Repository pattern for clean architecture",
      "Database migration strategies (dry-run, rollback, validation)",
      "FastAPI router organization and endpoint design",
      "Automatic session tracking and growth reflection generation",
      "YAML to NoSQL database migration",
      "Structured logging with structlog",
      "Progress snapshot and velocity metrics calculation"
    ],
    "technologies": [
      "MongoDB",
      "Motor (AsyncIO MongoDB driver)",
      "Pydantic v2",
      "FastAPI",
      "Python asyncio",
      "structlog",
      "PyYAML",
      "MongoDB aggregation pipelines"
    ],
    "blockers": [],
    "duration_hours": 3.5,
    "integration_tag": "architecture_enhancements",
    "goal_title": "AI Orchestrator Architecture Enhancements"
  }' | jq '.'

echo ""
echo "================================================================================"
echo "Session captured successfully!"
echo "================================================================================"
