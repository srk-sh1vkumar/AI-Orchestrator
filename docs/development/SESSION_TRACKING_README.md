# Automatic Session Tracking & Growth Reflections

## Overview

The AI Orchestrator now includes an automatic session tracking system that captures development work in real-time and generates growth reflections automatically at the end of each session.

This eliminates the manual overhead of creating growth reflections while ensuring consistent tracking of learning and accomplishments.

## How It Works

### 1. Automatic Tracking

The `SessionTracker` class automatically tracks:
- **Activities** - Code writing, debugging, documentation, etc.
- **File Modifications** - Create, edit, delete operations
- **Enhancements** - Work done on specific enhancements
- **Topics** - Technologies and concepts learned
- **Accomplishments** - What was achieved
- **Blockers** - Challenges encountered
- **Technologies** - Tools and frameworks used

### 2. Session Management

Sessions are automatically:
- **Started** - On first activity
- **Tracked** - Throughout the work session
- **Summarized** - At any time without ending
- **Ended** - When work is complete
- **Archived** - Stored in history (last 100 sessions)

### 3. Growth Reflection Generation

At session end, the system:
- Calculates duration and learning hours
- Analyzes activities and generates insights
- Estimates progress delta based on accomplishments
- Creates next-week focus items from blockers
- Generates comprehensive growth reflection
- Saves to growth tracking system

## Usage

### Method 1: Manual Tracking (Throughout Session)

Track activities as you work:

```bash
# Track an activity
curl -X POST http://localhost:8000/api/growth/sessions/track-activity \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "code",
    "description": "Implemented MongoDB repository pattern"
  }'

# Track file modification
curl -X POST http://localhost:8000/api/growth/sessions/track-file \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/db/repositories/mongo_enhancement_repository.py",
    "operation": "create"
  }'

# Track enhancement work
curl -X POST http://localhost:8000/api/growth/sessions/track-enhancement \
  -H "Content-Type: application/json" \
  -d '{
    "enhancement_id": "012",
    "title": "State Management & Persistence Layer",
    "work_description": "Implemented Phase 2: Enhancement Tracking Database"
  }'

# Add topic learned
curl -X POST http://localhost:8000/api/growth/sessions/add-topic \
  -H "Content-Type: application/json" \
  -d '{"topic": "MongoDB aggregation pipelines"}'

# Add accomplishment
curl -X POST http://localhost:8000/api/growth/sessions/add-accomplishment \
  -H "Content-Type: application/json" \
  -d '{"accomplishment": "Successfully migrated 18 enhancements to MongoDB"}'

# Add blocker
curl -X POST http://localhost:8000/api/growth/sessions/add-blocker \
  -H "Content-Type: application/json" \
  -d '{"blocker": "Pydantic v2 compatibility issues with ObjectId"}'

# Add technology
curl -X POST http://localhost:8000/api/growth/sessions/add-technology \
  -H "Content-Type: application/json" \
  -d '{"technology": "Motor (AsyncIO MongoDB driver)"}'
```

Get current session summary:

```bash
curl http://localhost:8000/api/growth/sessions/current | jq '.'
```

End session and create reflection:

```bash
curl -X POST http://localhost:8000/api/growth/sessions/end \
  -H "Content-Type: application/json" \
  -d '{
    "create_reflection": true,
    "integration_tag": "architecture_enhancements",
    "goal_title": "AI Orchestrator Architecture Enhancements"
  }' | jq '.'
```

### Method 2: Auto-Capture (End of Session)

Capture entire session at once:

```bash
curl -X POST http://localhost:8000/api/growth/sessions/auto-capture \
  -H "Content-Type: application/json" \
  -d '{
    "enhancement_id": "012",
    "enhancement_title": "State Management & Persistence Layer - Phase 2",
    "accomplishments": [
      "Created MongoDB schema validation with 5 collections",
      "Implemented repository pattern with 25 methods",
      "Built migration script with dry-run and rollback",
      "Developed REST API with 15+ endpoints"
    ],
    "topics": [
      "MongoDB schema validation",
      "Motor async driver",
      "Pydantic v2",
      "Repository pattern"
    ],
    "technologies": [
      "MongoDB",
      "Motor",
      "Pydantic v2",
      "FastAPI"
    ],
    "blockers": [],
    "duration_hours": 3.5,
    "integration_tag": "architecture_enhancements",
    "goal_title": "AI Orchestrator Architecture Enhancements"
  }' | jq '.'
```

### Method 3: Shell Script (Easiest)

Use the convenience script:

```bash
./scripts/capture_todays_session.sh
```

Edit the script to customize accomplishments, topics, etc.

## Session Data Structure

### Current Session File
Location: `session_data/current_session.json`

```json
{
  "session_id": "session_1730604000000",
  "start_time": "2025-11-02T18:00:00Z",
  "end_time": null,
  "duration_minutes": 0,
  "activities": [
    {
      "timestamp": "2025-11-02T18:15:00Z",
      "type": "code",
      "description": "Implemented repository pattern",
      "metadata": {}
    }
  ],
  "files_modified": [
    {
      "path": "src/db/repositories/mongo_enhancement_repository.py",
      "operation": "create",
      "timestamp": "2025-11-02T18:20:00Z"
    }
  ],
  "enhancements_worked_on": [
    {
      "id": "012",
      "title": "State Management & Persistence Layer",
      "work_items": [
        {
          "timestamp": "2025-11-02T18:00:00Z",
          "description": "Implemented Phase 2"
        }
      ]
    }
  ],
  "topics_covered": ["MongoDB", "Pydantic v2"],
  "accomplishments": ["Successfully migrated data"],
  "blockers": [],
  "technologies_used": ["MongoDB", "Motor", "FastAPI"],
  "learning_hours": 0.0
}
```

### Session History
Location: `session_data/sessions_history.json`

Stores last 100 completed sessions.

## Growth Reflection Format

Generated reflections include:

```json
{
  "id": "refl_1730604000000",
  "integration_tag": "architecture_enhancements",
  "week_of": "2025-10-28",
  "learning_hours": 3.5,
  "topics": ["MongoDB", "Pydantic v2", "Repository pattern"],
  "goal_title": "AI Orchestrator Architecture Enhancements",
  "progress_delta": 15,
  "accomplishments": [
    "Created MongoDB schema validation",
    "Implemented repository pattern",
    "Built migration script"
  ],
  "blockers": [],
  "insights": "Productive 3.5-hour session focused on 1 enhancement(s). Key achievements: Created MongoDB schema validation; Implemented repository pattern; Built migration script. Gained hands-on experience with MongoDB, Pydantic v2, Repository pattern. Created 7 new file(s), modified 4 existing file(s).",
  "next_week_focus": [
    "Continue work on State Management & Persistence Layer",
    "Review and test completed implementations",
    "Document architectural decisions"
  ],
  "created_at": "2025-11-02T21:30:00Z"
}
```

## Configuration

### Default Settings

- **Minimum session duration for reflection:** 30 minutes
- **Session history limit:** 100 sessions
- **Default integration_tag:** "architecture_enhancements"
- **Default goal_title:** "AI Orchestrator Architecture Enhancements"

### Progress Delta Calculation

Progress delta is estimated based on:
- Number of accomplishments × 5%
- Capped at 30% per session
- Can be overridden manually

## Benefits

### 1. **Automatic Tracking**
- No manual effort to create reflections
- Real-time capture of work
- Never forget what you accomplished

### 2. **Consistent Documentation**
- Standard format for all reflections
- Complete history of learning journey
- Easy to review past progress

### 3. **Insights Generation**
- Automatic analysis of session work
- Suggested next steps from blockers
- Progress estimation

### 4. **Integration with Goals**
- Links sessions to specific goals
- Tracks progress toward mastery objectives
- Provides weekly summaries

## Examples

### Example 1: Full Day Session

```bash
# Start of day - track first activity
curl -X POST http://localhost:8000/api/growth/sessions/track-enhancement \
  -d '{"enhancement_id": "012", "title": "Enhancement Tracking DB", "work_description": "Starting Phase 2"}'

# Throughout the day - track accomplishments
curl -X POST http://localhost:8000/api/growth/sessions/add-accomplishment \
  -d '{"accomplishment": "Created MongoDB schemas"}'

curl -X POST http://localhost:8000/api/growth/sessions/add-accomplishment \
  -d '{"accomplishment": "Implemented repository pattern"}'

# End of day - end session and create reflection
curl -X POST http://localhost:8000/api/growth/sessions/end
```

### Example 2: Quick Capture

```bash
# End of day - capture everything at once
./scripts/capture_todays_session.sh
```

## Troubleshooting

### Session Not Starting

Check if session file exists:
```bash
ls -la session_data/current_session.json
```

Manually trigger new session:
```bash
curl -X POST http://localhost:8000/api/growth/sessions/track-activity \
  -d '{"activity_type": "session_start", "description": "Manual session start"}'
```

### Reflection Not Created

Ensure session duration >= 30 minutes:
```bash
curl http://localhost:8000/api/growth/sessions/current | jq '.duration_hours'
```

Override duration if needed:
```bash
# Use auto-capture with explicit duration
curl -X POST http://localhost:8000/api/growth/sessions/auto-capture \
  -d '{"duration_hours": 2.0, ...}'
```

### View All Reflections

```bash
curl http://localhost:8000/api/growth/reflections | jq '.'
```

## Future Enhancements

- [ ] GitHub integration (auto-track commits)
- [ ] IDE plugin for real-time tracking
- [ ] Weekly/monthly summary reports
- [ ] Machine learning insights
- [ ] Integration with project management tools
- [ ] Slack notifications for milestones
- [ ] Dashboard visualization

## Related Documentation

- [Growth Tracking API](src/api/growth.py)
- [Session Tracker](src/core/session_tracker.py)
- [Enhancement Tracking Database](docs/ENHANCEMENT_TRACKING_DATABASE.md)
- [Session Summary Example](SESSION_SUMMARY_2025-11-02.md)
