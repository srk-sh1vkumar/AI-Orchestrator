# AI Orchestrator - Database Schema Design

**Date Created**: 2025-10-20
**Version**: 1.0
**Purpose**: Comprehensive backend schema for Project Enhancement Tracker

---

## Overview

This schema supports the AI Orchestrator's Project Enhancement Tracker by providing:
1. **Detailed Enhancement Storage**: Full context beyond concise YAML board
2. **Audit Trail**: Complete history of status changes and decisions
3. **Code Traceability**: Links to commits, PRs, and branches
4. **Success Validation**: Quantifiable metrics and testing steps
5. **Dependency Management**: Roadmap logic and prerequisite tracking

---

## Backend Schema (PostgreSQL)

### Table: `enhancement_details`

**Purpose**: Store comprehensive enhancement data with full history and context

```sql
CREATE TABLE enhancement_details (
    -- Primary Keys
    enhancement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    yaml_id VARCHAR(10) UNIQUE NOT NULL,  -- "001", "002", etc.

    -- Project Metadata
    project_tag VARCHAR(50) NOT NULL,  -- "ai_orchestrator", "recipe_tracker"
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,  -- "High", "Medium", "Low"
    status VARCHAR(50) NOT NULL,  -- "Ideation", "Definition", "Design", etc.

    -- Core Content
    long_description TEXT NOT NULL,  -- Full problem statement and solution
    technical_breakdown JSONB NOT NULL,  -- Step-by-step implementation plan
    success_metrics JSONB NOT NULL,  -- Quantifiable validation steps
    impact TEXT NOT NULL,  -- Quantifiable benefit statement

    -- Dependencies & Relationships
    dependencies JSONB DEFAULT '[]'::jsonb,  -- Array of enhancement IDs
    related_agent VARCHAR(100),  -- Relevant orchestration agent
    blocks JSONB DEFAULT '[]'::jsonb,  -- Enhancements blocked by this one
    blocked_by JSONB DEFAULT '[]'::jsonb,  -- Enhancements blocking this one

    -- Audit Trail
    log_history JSONB DEFAULT '[]'::jsonb,  -- Status changes, reflections
    code_references JSONB DEFAULT '[]'::jsonb,  -- Commits, PRs, branches

    -- Estimation & Tracking
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    completion_percentage INTEGER DEFAULT 0,  -- 0-100

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_priority CHECK (priority IN ('High', 'Medium', 'Low')),
    CONSTRAINT valid_status CHECK (status IN (
        'Ideation', 'Definition', 'Design', 'Implementation',
        'Reflection', 'Integration', 'Complete'
    )),
    CONSTRAINT valid_percentage CHECK (completion_percentage BETWEEN 0 AND 100)
);

-- Indexes for performance
CREATE INDEX idx_enhancement_yaml_id ON enhancement_details(yaml_id);
CREATE INDEX idx_enhancement_project ON enhancement_details(project_tag);
CREATE INDEX idx_enhancement_status ON enhancement_details(status);
CREATE INDEX idx_enhancement_priority ON enhancement_details(priority);
CREATE INDEX idx_enhancement_created ON enhancement_details(created_at DESC);
```

---

## JSONB Field Structures

### `technical_breakdown` Structure

```json
{
  "phases": [
    {
      "phase_number": 1,
      "name": "Database Migration",
      "description": "Set up PostgreSQL schema and migrate existing data",
      "steps": [
        "Install SQLAlchemy and Alembic",
        "Create migration scripts",
        "Test migration on dev environment",
        "Deploy to production"
      ],
      "estimated_hours": 2.0,
      "status": "Complete"
    },
    {
      "phase_number": 2,
      "name": "API Refactoring",
      "description": "Update API endpoints to use database",
      "steps": [
        "Create CRUD operations",
        "Update orchestrator integration",
        "Add error handling"
      ],
      "estimated_hours": 3.0,
      "status": "In Progress"
    }
  ],
  "architecture_notes": "Using SQLAlchemy ORM with async support (asyncpg driver)",
  "alternative_approaches": [
    "Considered MongoDB for flexible schema, chose PostgreSQL for ACID guarantees"
  ]
}
```

### `success_metrics` Structure

```json
{
  "quantitative": [
    {
      "metric": "Response cache hit rate",
      "target": ">60%",
      "measurement_method": "Prometheus metrics over 7 days",
      "baseline": "0% (no caching)",
      "actual": "73%"
    },
    {
      "metric": "Average response latency",
      "target": "<500ms for cached requests",
      "measurement_method": "Prometheus histogram p95",
      "baseline": "2500ms",
      "actual": "350ms"
    }
  ],
  "qualitative": [
    {
      "metric": "Developer experience",
      "target": "Simplified API usage",
      "validation": "Code review feedback, reduced support tickets"
    }
  ],
  "test_cases": [
    {
      "name": "Cache invalidation on update",
      "status": "Passed",
      "notes": "Tested with 1000 concurrent requests"
    },
    {
      "name": "Fallback to database on cache miss",
      "status": "Passed",
      "notes": "Redis failure simulation"
    }
  ]
}
```

### `dependencies` Structure

```json
{
  "required_enhancements": [
    {
      "enhancement_id": "db-uuid-002",
      "yaml_id": "002",
      "title": "Rate Limiting & Circuit Breaker",
      "reason": "Rate limiting state must be persisted for semantic caching"
    }
  ],
  "optional_enhancements": [
    {
      "enhancement_id": "db-uuid-005",
      "yaml_id": "005",
      "title": "OpenTelemetry Tracing",
      "reason": "Enhanced observability for cache performance"
    }
  ],
  "external_dependencies": [
    {
      "name": "Redis",
      "version": ">=7.0",
      "reason": "Primary caching layer"
    },
    {
      "name": "PostgreSQL",
      "version": ">=14.0",
      "reason": "Persistent storage"
    }
  ]
}
```

### `log_history` Structure

```json
[
  {
    "timestamp": "2025-01-15T10:30:00Z",
    "event_type": "status_change",
    "from_status": "Definition",
    "to_status": "Design",
    "author": "Claude Code",
    "notes": "Completed API design review with team"
  },
  {
    "timestamp": "2025-01-16T14:20:00Z",
    "event_type": "reflection",
    "author": "Developer",
    "notes": "Decided to use Redis over Memcached for better data structure support"
  },
  {
    "timestamp": "2025-01-18T09:00:00Z",
    "event_type": "blocker_identified",
    "blocker": "Redis cluster configuration unclear",
    "resolution_plan": "Schedule architecture review meeting"
  },
  {
    "timestamp": "2025-01-20T16:45:00Z",
    "event_type": "milestone_achieved",
    "milestone": "Phase 1: Database migration complete",
    "actual_hours": 2.5,
    "estimated_hours": 2.0
  }
]
```

### `code_references` Structure

```json
{
  "branches": [
    {
      "name": "feature/semantic-caching",
      "created_at": "2025-01-15T10:00:00Z",
      "merged_at": "2025-01-25T15:30:00Z",
      "status": "Merged"
    }
  ],
  "pull_requests": [
    {
      "number": 42,
      "title": "Add Redis-based semantic caching layer",
      "url": "https://github.com/user/ai-orchestrator/pull/42",
      "status": "Merged",
      "merged_at": "2025-01-25T15:30:00Z",
      "reviewers": ["user1", "user2"],
      "commits": 15
    }
  ],
  "commits": [
    {
      "sha": "a1b2c3d4",
      "message": "feat(cache): implement semantic similarity scoring",
      "author": "Developer",
      "timestamp": "2025-01-20T11:15:00Z",
      "files_changed": 5
    }
  ],
  "related_issues": [
    {
      "number": 38,
      "title": "High latency on repeated queries",
      "url": "https://github.com/user/ai-orchestrator/issues/38",
      "status": "Closed"
    }
  ],
  "documentation": [
    {
      "type": "completion_report",
      "path": "ENHANCEMENT_004_COMPLETE.md",
      "url": "https://github.com/user/ai-orchestrator/blob/main/ENHANCEMENT_004_COMPLETE.md"
    }
  ]
}
```

---

## Table: `conversations`

**Purpose**: Store conversation history for context management

```sql
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),  -- Future: multi-tenancy support

    -- Conversation Metadata
    title VARCHAR(200),
    provider_used VARCHAR(50) NOT NULL,
    routing_decision JSONB NOT NULL,  -- Full routing decision object

    -- Metrics
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0,
    execution_time_ms INTEGER,

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- "active", "archived", "deleted"

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('active', 'archived', 'deleted'))
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_conversations_provider ON conversations(provider_used);
```

---

## Table: `messages`

**Purpose**: Store individual messages within conversations

```sql
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Message Content
    role VARCHAR(20) NOT NULL,  -- "user", "assistant", "system"
    content TEXT NOT NULL,

    -- Provider Info
    provider VARCHAR(50),
    model VARCHAR(100),

    -- Metrics
    token_count INTEGER,
    cost_usd DECIMAL(10,6),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant', 'system'))
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_messages_role ON messages(role);
```

---

## Table: `tool_executions`

**Purpose**: Store tool execution history

```sql
CREATE TABLE tool_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    message_id UUID REFERENCES messages(message_id) ON DELETE SET NULL,

    -- Tool Info
    tool_type VARCHAR(50) NOT NULL,  -- "github", "docker", "kubernetes"
    operation VARCHAR(100) NOT NULL,  -- "create_issue", "list_containers"

    -- Execution Details
    parameters JSONB NOT NULL,
    result JSONB,
    error TEXT,

    -- Status
    success BOOLEAN NOT NULL,
    execution_time_ms INTEGER,

    -- Validation (from Enhancement 013)
    validation_status VARCHAR(20),  -- "valid", "invalid", "skipped"
    validation_errors JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tool_executions_conversation ON tool_executions(conversation_id);
CREATE INDEX idx_tool_executions_tool_type ON tool_executions(tool_type);
CREATE INDEX idx_tool_executions_success ON tool_executions(success);
CREATE INDEX idx_tool_executions_created ON tool_executions(created_at DESC);
```

---

## Table: `context_events`

**Purpose**: Track context window management events (Enhancement 003)

```sql
CREATE TABLE context_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Context Status
    provider VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- "ok", "warning", "overflow", "truncated"

    -- Metrics
    token_count INTEGER NOT NULL,
    token_limit INTEGER NOT NULL,
    utilization_percent DECIMAL(5,2) NOT NULL,

    -- Truncation Details
    was_truncated BOOLEAN DEFAULT FALSE,
    truncation_strategy VARCHAR(50),  -- "sliding_window", "summarize", "hybrid"
    messages_before INTEGER,
    messages_after INTEGER,
    tokens_removed INTEGER,

    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('ok', 'warning', 'overflow', 'truncated'))
);

CREATE INDEX idx_context_events_conversation ON context_events(conversation_id);
CREATE INDEX idx_context_events_provider ON context_events(provider);
CREATE INDEX idx_context_events_status ON context_events(status);
CREATE INDEX idx_context_events_timestamp ON context_events(timestamp DESC);
```

---

## Table: `provider_metrics`

**Purpose**: Aggregate provider performance metrics

```sql
CREATE TABLE provider_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Provider Info
    provider VARCHAR(50) NOT NULL,
    category VARCHAR(50),  -- Task category

    -- Time Window
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Request Metrics
    request_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    fallback_count INTEGER DEFAULT 0,

    -- Performance Metrics
    avg_latency_ms DECIMAL(10,2),
    p50_latency_ms INTEGER,
    p95_latency_ms INTEGER,
    p99_latency_ms INTEGER,

    -- Token & Cost Metrics
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0,

    -- Quality Metrics
    avg_quality_score DECIMAL(5,2),  -- 0-100
    quality_check_failures INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_provider_metrics_provider ON provider_metrics(provider);
CREATE INDEX idx_provider_metrics_window ON provider_metrics(window_start DESC);
CREATE UNIQUE INDEX idx_provider_metrics_unique ON provider_metrics(provider, category, window_start);
```

---

## Table: `cache_entries` (Redis Alternative for Semantic Caching)

**Purpose**: PostgreSQL-based semantic cache (if not using Redis)

```sql
CREATE TABLE cache_entries (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Cache Key
    cache_key VARCHAR(64) UNIQUE NOT NULL,  -- Hash of normalized query
    query_text TEXT NOT NULL,
    query_embedding VECTOR(1536),  -- pgvector extension for semantic search

    -- Cached Response
    response_text TEXT NOT NULL,
    provider VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Cache Metrics
    hit_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMP WITH TIME ZONE,

    -- TTL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Similarity Threshold Used
    similarity_threshold DECIMAL(5,2) DEFAULT 0.85
);

CREATE INDEX idx_cache_entries_key ON cache_entries(cache_key);
CREATE INDEX idx_cache_entries_expires ON cache_entries(expires_at);
-- Requires pgvector extension:
-- CREATE INDEX idx_cache_entries_embedding ON cache_entries USING ivfflat (query_embedding vector_cosine_ops);
```

---

## Database Relationships

```
enhancement_details (1) ──< (M) code_references
                     │
                     └──< (M) log_history

conversations (1) ──< (M) messages
              │
              ├──< (M) tool_executions
              │
              └──< (M) context_events

messages (1) ──< (M) tool_executions

provider_metrics (standalone aggregates)

cache_entries (standalone cache storage)
```

---

## Migration Strategy

### Phase 1: Core Schema (Enhancement 012)
1. Create `enhancement_details` table
2. Create `conversations`, `messages` tables
3. Migrate existing manifest data

### Phase 2: Tool & Context Tracking
1. Create `tool_executions` table
2. Create `context_events` table
3. Integrate with existing managers

### Phase 3: Metrics & Caching
1. Create `provider_metrics` table
2. Create `cache_entries` table (if not using Redis)
3. Set up aggregation jobs

---

## Database Technology Recommendations

### Primary: **PostgreSQL 14+**

**Rationale**:
- ✅ ACID compliance for audit trail integrity
- ✅ JSONB support for flexible metadata
- ✅ pgvector extension for semantic caching
- ✅ Excellent async support (asyncpg)
- ✅ Strong typing and constraints
- ✅ Battle-tested for production workloads

**Extensions Required**:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgvector";   -- Vector similarity (semantic cache)
```

### Cache Layer: **Redis 7+**

**Rationale**:
- ✅ In-memory performance for hot data
- ✅ Native TTL support
- ✅ Pub/Sub for real-time updates
- ✅ Already in dependencies

**Use Cases**:
- Session management
- Rate limiting token buckets
- Response caching (short TTL)
- Provider health status

---

## ORM & Migration Tools

### SQLAlchemy 2.0 (Async)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Engine setup
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/ai_orchestrator",
    echo=True,
    future=True
)

# Session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

### Alembic for Migrations

```bash
# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create enhancement_details table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Performance Considerations

### Partitioning Strategy

```sql
-- Partition messages by month for better query performance
CREATE TABLE messages_2025_01 PARTITION OF messages
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE messages_2025_02 PARTITION OF messages
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

### Archival Strategy

```sql
-- Move old conversations to archive table
CREATE TABLE conversations_archive (LIKE conversations INCLUDING ALL);

-- Archive conversations older than 6 months
INSERT INTO conversations_archive
SELECT * FROM conversations
WHERE updated_at < NOW() - INTERVAL '6 months'
  AND status = 'active';

UPDATE conversations
SET status = 'archived'
WHERE updated_at < NOW() - INTERVAL '6 months';
```

---

## Security & Access Control

### Row-Level Security (Future: Multi-tenancy)

```sql
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversations_user_policy ON conversations
    FOR ALL
    TO authenticated_user
    USING (user_id = current_user_id());
```

### Sensitive Data Handling

```sql
-- Never store API keys or secrets in database
-- Use environment variables or secret managers
-- Encrypt PII if storing user data
```

---

## Monitoring & Maintenance

### Database Metrics to Track

1. **Query Performance**:
   - Slow query log (>500ms)
   - Index usage statistics
   - Table bloat

2. **Connection Pool**:
   - Active connections
   - Connection wait time
   - Pool exhaustion events

3. **Storage**:
   - Table sizes
   - Index sizes
   - WAL size

4. **Replication** (if applicable):
   - Replication lag
   - Replica health

---

## Next Steps

1. **Enhancement 012**: Implement core schema (conversations, messages)
2. **Enhancement 004**: Add semantic caching with pgvector or Redis
3. **Enhancement 007**: Add cost tracking with provider_metrics table
4. **Enhancement 010**: Add A/B testing experiment tables

---

**Schema Version**: 1.0
**Last Updated**: 2025-10-20
**Status**: Design Complete, Ready for Implementation
