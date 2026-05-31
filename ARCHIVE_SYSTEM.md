# Archive System Documentation

**Enhancement ID**: 014
**Status**: ✅ Complete
**Version**: 1.0.0
**Date**: 2025-12-29

## Overview

The Archive System provides comprehensive long-term storage and retrieval capabilities for conversations, work sessions, and project snapshots. Built on MongoDB with full-text search, the system enables:

- **Conversation Archival**: Store completed conversations with full message history
- **Session Tracking**: Record work sessions with accomplishments and metrics
- **Project Snapshots**: Create milestone snapshots with git integration
- **Full-Text Search**: Search across all archives
- **Data Export**: Export archives in JSON or CSV format
- **Restoration**: Restore archived conversations back to active state

## Architecture

```
┌─────────────────────────────────────────────────┐
│         MongoDB (ai_orchestrator database)      │
├─────────────────────────────────────────────────┤
│                                                 │
│  Active Collections:                            │
│  ├── conversations (active chats)               │
│  ├── messages (current messages)                │
│  └── enhancements (in-progress work)            │
│                                                 │
│  Archive Collections:                           │
│  ├── archived_conversations                     │
│  │   ├── Full conversation history              │
│  │   ├── All messages embedded                  │
│  │   └── Full-text search enabled               │
│  │                                               │
│  ├── archived_sessions                          │
│  │   ├── Session metadata                       │
│  │   ├── Enhancements completed                 │
│  │   └── Files created/modified                 │
│  │                                               │
│  └── project_archives                           │
│      ├── Project snapshots                      │
│      ├── Git commit tracking                    │
│      └── Metrics snapshots                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Database Schema

### 1. archived_conversations

Stores archived conversations with complete message history.

**Fields:**
```javascript
{
  _id: ObjectId,
  original_id: ObjectId,  // Reference to original conversation
  user_id: string?,
  title: string?,
  provider_used: string,
  routing_decision: object,
  messages: [  // Embedded messages
    {
      role: "user" | "assistant" | "system",
      content: string,
      provider: string?,
      model: string?,
      token_count: int?,
      cost_usd: double?,
      created_at: datetime
    }
  ],
  metrics: {
    message_count: int,
    total_tokens: int,
    total_cost_usd: double,
    execution_time_ms: int
  },
  archived_at: datetime,
  archive_reason: "manual" | "auto_retention" | "project_complete",
  tags: [string],
  notes: string?,
  created_at: datetime,
  updated_at: datetime
}
```

**Indexes:**
- `idx_original_id` (unique)
- `idx_user_id`
- `idx_archived_at` (descending)
- `idx_provider`
- `idx_tags`
- `idx_fulltext` (text index on title, notes)

### 2. archived_sessions

Records work sessions with accomplishments and metrics.

**Fields:**
```javascript
{
  _id: ObjectId,
  session_date: datetime,
  session_duration_hours: double,
  projects: ["ai-orchestrator" | "ecommerce-microservices" | "sre-analytics" | "monitoring-hub"],
  accomplishments: [string],
  enhancements_completed: [
    {
      enhancement_id: string,
      project: string,
      title: string,
      actual_hours: double
    }
  ],
  files_created: [string],
  files_modified: [string],
  lines_of_code: int,
  blockers: [string],
  next_priorities: [string],
  notes: string?,
  conversation_ids: [ObjectId],
  created_at: datetime
}
```

**Indexes:**
- `idx_session_date` (descending)
- `idx_projects`
- `idx_enhancements` (on enhancement_id)
- `idx_fulltext` (text index on accomplishments, notes)

### 3. project_archives

Project milestone snapshots with git integration.

**Fields:**
```javascript
{
  _id: ObjectId,
  project_name: "ai-orchestrator" | "ecommerce-microservices" | "sre-analytics" | "monitoring-hub",
  archive_type: "milestone" | "release" | "backup" | "experiment",
  snapshot_date: datetime,
  version: string?,
  description: string,
  enhancements_snapshot: [object],  // Full enhancement data
  metrics_snapshot: {
    total_enhancements: int,
    completed_enhancements: int,
    completion_percentage: double,
    total_hours: double,
    total_lines_of_code: int
  },
  git_commit: string?,
  git_branch: string?,
  files_snapshot: [
    {
      path: string,
      size: int,
      last_modified: datetime,
      checksum: string?
    }
  ],
  tags: [string],
  notes: string?,
  created_at: datetime
}
```

**Indexes:**
- `idx_project`
- `idx_snapshot_date` (descending)
- `idx_archive_type`
- `idx_version`
- `idx_tags`
- `idx_git_commit`
- `idx_fulltext` (text index on description, notes)

## API Endpoints

Base URL: `http://localhost:8000/api/archives`

### Archive Operations

#### 1. Archive Conversation

**POST** `/conversations/{conversation_id}`

Archives a conversation with all messages.

**Request Body:**
```json
{
  "archive_reason": "manual" | "auto_retention" | "project_complete",
  "tags": ["important", "customer-support"],
  "notes": "Conversation about feature X implementation"
}
```

**Response:**
```json
{
  "archive_id": "507f1f77bcf86cd799439011",
  "original_id": "507f191e810c19729de860ea",
  "archived_at": "2025-12-29T10:30:00Z",
  "message": "Conversation archived successfully (manual)"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/archives/conversations/507f191e810c19729de860ea \
  -H "Content-Type: application/json" \
  -d '{
    "archive_reason": "project_complete",
    "tags": ["enhancement-014", "archive-system"],
    "notes": "Completed implementation of archive system"
  }'
```

#### 2. Create Session Archive

**POST** `/sessions`

Records a work session with accomplishments.

**Request Body:**
```json
{
  "session_date": "2025-12-29T00:00:00Z",
  "session_duration_hours": 8.5,
  "projects": ["ai-orchestrator", "monitoring-hub"],
  "accomplishments": [
    "Completed Enhancement 024: Cost Dashboard",
    "Completed Enhancement 023: Developer Tools",
    "Added ClickHouse to monitoring-hub"
  ],
  "enhancements_completed": [
    {
      "enhancement_id": "024",
      "project": "ai-orchestrator",
      "title": "Real-Time Cost Tracking Dashboard",
      "actual_hours": 3.5
    }
  ],
  "files_created": [
    "frontend/src/pages/CostDashboardPage.tsx",
    "src/api/developer_tools.py"
  ],
  "files_modified": [
    "frontend/src/App.tsx",
    "src/api/main.py"
  ],
  "lines_of_code": 2500,
  "blockers": [],
  "next_priorities": [
    "Complete Enhancement 014 documentation"
  ],
  "notes": "Highly productive session with 3 major completions",
  "conversation_ids": ["507f191e810c19729de860ea"]
}
```

**Response:**
```json
{
  "archive_id": "507f1f77bcf86cd799439011",
  "session_date": "2025-12-29T00:00:00Z",
  "message": "Session archive created for 2 project(s)"
}
```

#### 3. Create Project Snapshot

**POST** `/projects`

Creates a project milestone snapshot.

**Request Body:**
```json
{
  "project_name": "ai-orchestrator",
  "archive_type": "milestone",
  "version": "1.2.0",
  "description": "Completed archive system and developer tools",
  "enhancements_snapshot": [...],  // Full enhancement data
  "metrics_snapshot": {
    "total_enhancements": 24,
    "completed_enhancements": 20,
    "completion_percentage": 83.3,
    "total_hours": 156.5,
    "total_lines_of_code": 15000
  },
  "git_commit": "a3f2c1b9e8d7f6a5b4c3d2e1f0",
  "git_branch": "main",
  "files_snapshot": [...],
  "tags": ["v1.2.0", "archive-system", "dev-tools"],
  "notes": "Major milestone with archive and debugging capabilities"
}
```

**Response:**
```json
{
  "archive_id": "507f1f77bcf86cd799439011",
  "project_name": "ai-orchestrator",
  "snapshot_date": "2025-12-29T10:30:00Z",
  "message": "Milestone snapshot created for ai-orchestrator"
}
```

### Retrieval Operations

#### 4. List Archived Conversations

**GET** `/conversations?limit=50&skip=0&archive_reason=manual&tags=important`

**Query Parameters:**
- `limit` (1-500, default: 50)
- `skip` (default: 0)
- `archive_reason` (optional filter)
- `tags` (comma-separated, optional filter)

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "original_id": "507f191e810c19729de860ea",
    "user_id": "user123",
    "title": "Feature discussion",
    "provider_used": "gemini",
    "archived_at": "2025-12-29T10:30:00Z",
    "archive_reason": "manual",
    "tags": ["important"],
    "metrics": {
      "message_count": 15,
      "total_tokens": 3500,
      "total_cost_usd": 0.15
    }
  }
]
```

#### 5. List Archived Sessions

**GET** `/sessions?limit=50&project=ai-orchestrator&start_date=2025-12-01`

**Query Parameters:**
- `limit` (1-500, default: 50)
- `skip` (default: 0)
- `project` (optional filter)
- `start_date` (ISO datetime, optional)
- `end_date` (ISO datetime, optional)

#### 6. List Project Archives

**GET** `/projects?project_name=ai-orchestrator&archive_type=milestone`

**Query Parameters:**
- `limit` (1-500, default: 50)
- `skip` (default: 0)
- `project_name` (optional filter)
- `archive_type` (optional filter)
- `tags` (comma-separated, optional filter)

### Search Operations

#### 7. Full-Text Search

**GET** `/search?q=cost+dashboard&collection=conversations&limit=20`

Searches across all archive collections using MongoDB text indexes.

**Query Parameters:**
- `q` (required, min 3 chars)
- `collection` (optional: "conversations", "sessions", "projects")
- `limit` (1-100, default: 20)

**Response:**
```json
{
  "query": "cost dashboard",
  "conversations": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "Cost Dashboard Implementation",
      "archived_at": "2025-12-29T10:30:00Z",
      "tags": ["enhancement-024"],
      "score": 1.2
    }
  ],
  "sessions": [
    {
      "id": "507f1f77bcf86cd799439012",
      "session_date": "2025-12-29T00:00:00Z",
      "projects": ["ai-orchestrator"],
      "accomplishments": ["Completed Cost Dashboard"],
      "score": 0.9
    }
  ],
  "projects": [],
  "total_results": 2
}
```

### Restore Operations

#### 8. Restore Conversation

**POST** `/restore/{archive_id}`

Restores an archived conversation back to active conversations.

**Response:**
```json
{
  "message": "Conversation restored successfully",
  "conversation_id": "507f191e810c19729de860ea",
  "messages_restored": 15
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/archives/restore/507f1f77bcf86cd799439011
```

### Export Operations

#### 9. Export Archives

**GET** `/export?collection=sessions&format=json&start_date=2025-12-01`

Exports archive data in JSON or CSV format.

**Query Parameters:**
- `collection` (required: "conversations", "sessions", "projects")
- `format` (default: "json", options: "json", "csv")
- `start_date` (ISO datetime, optional)
- `end_date` (ISO datetime, optional)

**Response (JSON):**
```json
{
  "collection": "sessions",
  "count": 15,
  "data": [...]
}
```

**Response (CSV):**
```json
{
  "collection": "sessions",
  "count": 15,
  "format": "csv",
  "data": "id,session_date,projects,accomplishments\n..."
}
```

### Statistics

#### 10. Archive Statistics

**GET** `/stats`

Returns statistics about archived data.

**Response:**
```json
{
  "total_archived_conversations": 150,
  "total_archived_sessions": 45,
  "total_project_snapshots": 12,
  "recent_conversations": [...],
  "recent_sessions": [...]
}
```

## Usage Examples

### Example 1: Archive a Completed Conversation

```python
import requests

# Archive conversation
response = requests.post(
    "http://localhost:8000/api/archives/conversations/507f191e810c19729de860ea",
    json={
        "archive_reason": "project_complete",
        "tags": ["important", "feature-x"],
        "notes": "Completed discussion about feature X"
    }
)

print(response.json())
# {
#   "archive_id": "507f1f77bcf86cd799439011",
#   "original_id": "507f191e810c19729de860ea",
#   "archived_at": "2025-12-29T10:30:00Z",
#   "message": "Conversation archived successfully (project_complete)"
# }
```

### Example 2: Record a Work Session

```python
import requests
from datetime import datetime

# Create session archive
response = requests.post(
    "http://localhost:8000/api/archives/sessions",
    json={
        "session_date": datetime.utcnow().isoformat(),
        "session_duration_hours": 8.5,
        "projects": ["ai-orchestrator"],
        "accomplishments": [
            "Completed Enhancement 024",
            "Completed Enhancement 023",
            "Started Enhancement 014"
        ],
        "enhancements_completed": [
            {
                "enhancement_id": "024",
                "project": "ai-orchestrator",
                "title": "Cost Dashboard",
                "actual_hours": 3.5
            }
        ],
        "files_created": ["frontend/src/pages/CostDashboardPage.tsx"],
        "lines_of_code": 2500
    }
)

print(response.json())
```

### Example 3: Search Archives

```python
import requests

# Search for "cost dashboard"
response = requests.get(
    "http://localhost:8000/api/archives/search",
    params={"q": "cost dashboard", "limit": 10}
)

results = response.json()
print(f"Found {results['total_results']} results:")
print(f"  - {len(results['conversations'])} conversations")
print(f"  - {len(results['sessions'])} sessions")
print(f"  - {len(results['projects'])} project snapshots")
```

### Example 4: Export Session Data

```python
import requests

# Export all December sessions as CSV
response = requests.get(
    "http://localhost:8000/api/archives/export",
    params={
        "collection": "sessions",
        "format": "csv",
        "start_date": "2025-12-01T00:00:00Z",
        "end_date": "2025-12-31T23:59:59Z"
    }
)

csv_data = response.json()["data"]
with open("sessions_december.csv", "w") as f:
    f.write(csv_data)
```

### Example 5: Create Project Snapshot

```python
import requests
import subprocess

# Get current git commit
git_commit = subprocess.check_output(
    ["git", "rev-parse", "HEAD"]
).decode().strip()

git_branch = subprocess.check_output(
    ["git", "rev-parse", "--abbrev-ref", "HEAD"]
).decode().strip()

# Create milestone snapshot
response = requests.post(
    "http://localhost:8000/api/archives/projects",
    json={
        "project_name": "ai-orchestrator",
        "archive_type": "milestone",
        "version": "1.2.0",
        "description": "Completed archive system with full search and export",
        "git_commit": git_commit,
        "git_branch": git_branch,
        "metrics_snapshot": {
            "total_enhancements": 24,
            "completed_enhancements": 20,
            "completion_percentage": 83.3
        },
        "tags": ["v1.2.0", "archive-system"]
    }
)

print(response.json())
```

## Best Practices

### 1. Archive Regularly

Archive conversations when:
- Project milestone completed
- Feature implementation finished
- Conversation exceeds 100 messages
- Monthly cleanup (auto_retention)

### 2. Tag Strategically

Use consistent tags:
- Project names: `ai-orchestrator`, `ecommerce`
- Enhancement IDs: `enhancement-024`, `enh-014`
- Categories: `bug-fix`, `feature`, `refactor`
- Priority: `critical`, `important`, `nice-to-have`

### 3. Document Sessions

Record sessions with:
- Clear accomplishments (what was done)
- Specific enhancements completed (with IDs)
- Files created/modified (for context)
- Blockers (for continuity)
- Next priorities (for planning)

### 4. Create Snapshots at Milestones

Create project snapshots when:
- Releasing a new version
- Completing major features
- Before major refactoring
- Monthly backups

### 5. Use Search Effectively

Search tips:
- Use specific keywords: "cost dashboard" not "dashboard"
- Filter by collection when you know the type
- Use date ranges for time-based searches
- Export results for analysis

## Maintenance

### Data Retention

Archives are stored indefinitely by default. To implement retention:

```javascript
// Create TTL index (30 days retention)
db.archived_conversations.createIndex(
  { "archived_at": 1 },
  { expireAfterSeconds: 2592000 }  // 30 days
)
```

### Backup Strategy

**Recommended**:
1. **Daily**: MongoDB dump of active collections
2. **Weekly**: Full archive collections export
3. **Monthly**: Project snapshots

```bash
# Export archives
curl "http://localhost:8000/api/archives/export?collection=sessions&format=json" \
  > backups/sessions_$(date +%Y%m%d).json

curl "http://localhost:8000/api/archives/export?collection=conversations&format=json" \
  > backups/conversations_$(date +%Y%m%d).json
```

### Performance Optimization

**For large archives** (>10K documents):

1. **Add indexes for common queries**:
```javascript
db.archived_conversations.createIndex(
  { "tags": 1, "archived_at": -1 }
)
```

2. **Use aggregation for complex queries**:
```javascript
db.archived_sessions.aggregate([
  { $match: { "projects": "ai-orchestrator" } },
  { $group: {
      _id: null,
      total_hours: { $sum: "$session_duration_hours" },
      total_loc: { $sum: "$lines_of_code" }
  }}
])
```

3. **Archive old data to cold storage**:
- Export archives older than 1 year
- Store in S3 or file system
- Remove from MongoDB

## Troubleshooting

### Archive Creation Fails

**Problem**: Archive creation returns 500 error

**Solution**:
1. Check MongoDB connection: `curl http://localhost:8000/health`
2. Verify conversation exists: `GET /api/conversations/{id}`
3. Check MongoDB logs: `docker logs mongodb`

### Search Returns No Results

**Problem**: Search query returns empty results

**Solution**:
1. Verify text indexes exist: `db.archived_conversations.getIndexes()`
2. Rebuild text indexes if needed
3. Try exact match queries first
4. Check if data actually exists: `GET /api/archives/stats`

### Restore Fails

**Problem**: Conversation restore fails

**Solution**:
1. Check if archive exists: `GET /api/archives/conversations`
2. Verify archive ID is valid ObjectId
3. Check for duplicate original_id conflicts

## Integration with Other Systems

### Git Integration

Archive system integrates with git for snapshots:

```bash
# Create snapshot with current git state
git_commit=$(git rev-parse HEAD)
git_branch=$(git branch --show-current)

curl -X POST http://localhost:8000/api/archives/projects \
  -d "{
    \"project_name\": \"ai-orchestrator\",
    \"archive_type\": \"release\",
    \"git_commit\": \"$git_commit\",
    \"git_branch\": \"$git_branch\"
  }"
```

### CI/CD Integration

Automate snapshots on deployment:

```yaml
# .github/workflows/deploy.yml
- name: Create Archive Snapshot
  run: |
    curl -X POST http://localhost:8000/api/archives/projects \
      -H "Content-Type: application/json" \
      -d '{
        "project_name": "ai-orchestrator",
        "archive_type": "release",
        "version": "${{ github.ref_name }}",
        "git_commit": "${{ github.sha }}",
        "git_branch": "${{ github.ref }}",
        "description": "Automated release snapshot"
      }'
```

## Future Enhancements

Potential improvements:
1. **Frontend UI**: Archive management dashboard
2. **Advanced Search**: Semantic search with embeddings
3. **Analytics**: Session analytics and trends
4. **Automation**: Auto-archiving based on rules
5. **Compression**: Compress old archives
6. **S3 Export**: Direct export to S3

---

**Enhancement 014 - Archive System: ✅ COMPLETE**
