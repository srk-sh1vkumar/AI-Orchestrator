# Shared Modules Analysis

Analysis of AI Orchestrator modules that could be extracted into shared packages for use across multiple projects (e-commerce, SRE analytics, etc.).

---

## 🎯 Highly Reusable Modules (Extract First)

### 1. **Rate Limiting & Circuit Breaking** ⭐⭐⭐⭐⭐
**File**: `src/core/rate_limiter.py` (11 KB)

**What it does**:
- Token bucket rate limiting algorithm
- Per-provider rate limiting
- Automatic backoff and retry logic
- Quota management

**Why share**:
- ✅ Zero dependencies on AI orchestrator logic
- ✅ Useful for ANY API-based system
- ✅ Can be used in e-commerce (API rate limiting), SRE analytics (data source throttling)
- ✅ Well-tested pattern

**Extraction effort**: LOW (1-2 hours)

**Shared package name**: `ai-common-ratelimit` or `py-ratelimiter`

**Usage in other projects**:
```python
# E-commerce microservices
from ai_common.ratelimit import RateLimiter
limiter = RateLimiter(requests_per_second=100)

# SRE analytics
limiter = RateLimiter(provider="prometheus", requests_per_minute=60)
```

---

### 2. **MongoDB Infrastructure** ⭐⭐⭐⭐⭐
**Files**:
- `src/database/mongodb.py` (21 KB) - Connection manager
- `src/database/repositories.py` (26 KB) - Repository pattern base classes
- `src/database/models.py` (9 KB) - Base Pydantic models

**What it does**:
- MongoDB connection management with pooling
- Automatic collection initialization
- Schema validation setup
- Repository base classes with CRUD operations
- Connection health checks

**Why share**:
- ✅ Generic MongoDB patterns useful everywhere
- ✅ Battle-tested connection management
- ✅ Repository pattern is industry standard
- ✅ Could be used in e-commerce for order tracking, user management
- ✅ Could be used in SRE analytics for storing metrics history

**Extraction effort**: MEDIUM (3-4 hours)

**Shared package name**: `ai-common-mongodb` or `py-mongo-toolkit`

**What to extract**:
```python
# Core connection manager
class MongoDBManager:
    - Connection pooling
    - Health checks
    - Collection initialization
    - Schema validation setup

# Base repository pattern
class BaseRepository:
    - create()
    - find_by_id()
    - find_all()
    - update()
    - delete()
    - find_with_pagination()
```

---

### 3. **Cost Tracking & Budget Management** ⭐⭐⭐⭐
**Files**:
- `src/core/budget_manager.py` (14 KB)
- `src/cost_estimator.py` (small)
- `src/api/costs.py` (11 KB)

**What it does**:
- API call cost estimation
- Budget tracking and alerts
- Cost aggregation and reporting
- Multi-provider cost tracking

**Why share**:
- ✅ Useful for any system using paid APIs (OpenAI, cloud services)
- ✅ E-commerce could use for payment gateway cost tracking
- ✅ SRE analytics could use for cloud monitoring service costs
- ✅ Generic pattern: track usage → calculate cost → alert on budget

**Extraction effort**: MEDIUM (4-5 hours)

**Shared package name**: `ai-common-cost-tracker` or `py-api-budgets`

**Configuration-driven**:
```yaml
# cost_config.yaml
providers:
  - name: openai_gpt4
    cost_per_1k_tokens: 0.03
  - name: claude_sonnet
    cost_per_1k_tokens: 0.015
  - name: payment_gateway
    cost_per_transaction: 0.30

budgets:
  - name: monthly_ai
    limit: 500
    alert_threshold: 0.8
```

---

### 4. **Session Tracking & Growth Reflection** ⭐⭐⭐⭐
**Files**:
- `src/core/session_tracker.py` (14 KB)
- `src/core/auto_session_capture.py` (15 KB)
- `src/api/growth.py` (18 KB)

**What it does**:
- Track development session activities
- Automatic growth reflection generation
- Weekly learning summaries
- Accomplishment tracking

**Why share**:
- ✅ Useful for team productivity tracking
- ✅ Could be used across multiple projects to track developer progress
- ✅ Generic concept: track work → generate insights → show progress
- ✅ Helps with performance reviews and retrospectives

**Extraction effort**: HIGH (5-6 hours - need to make generic)

**Shared package name**: `ai-common-session-tracker` or `dev-productivity-tracker`

**Generic version**:
```python
from ai_common.session import SessionTracker

tracker = SessionTracker(
    integration_tag="backend_development",
    storage_backend="mongodb"  # or "json", "postgres"
)

tracker.track_activity("code_review", "Reviewed 5 PRs")
tracker.track_file_change("src/api/users.py", "update")
tracker.generate_weekly_summary()
```

---

### 5. **Semantic Cache** ⭐⭐⭐⭐
**File**: `src/core/semantic_cache.py` (16 KB)

**What it does**:
- Embeddings-based semantic similarity caching
- Reduces duplicate LLM calls for similar queries
- TTL-based cache expiration
- Vector similarity search

**Why share**:
- ✅ Useful for any LLM-based application
- ✅ Saves money on API calls
- ✅ E-commerce could use for product search caching
- ✅ SRE analytics could use for query caching

**Extraction effort**: MEDIUM (3-4 hours)

**Shared package name**: `ai-common-semantic-cache` or `py-llm-cache`

**Dependencies**:
- Embeddings provider (OpenAI, sentence-transformers)
- Vector storage (FAISS, numpy)

---

### 6. **Generic Tools (Docker, K8s, GitHub)** ⭐⭐⭐
**Files**:
- `src/tools/docker_tool.py` (3.8 KB)
- `src/tools/kubernetes_tool.py` (4.2 KB)
- `src/tools/github_tool.py` (4.4 KB)
- `src/tools/file_system_tool.py` (2.6 KB)
- `src/tools/terminal_tool.py` (2.4 KB)

**What they do**:
- Programmatic Docker operations
- K8s resource management
- GitHub API operations
- File system operations
- Terminal command execution

**Why share**:
- ✅ DevOps tools useful in any project
- ✅ E-commerce could use for deployment automation
- ✅ SRE analytics could use for infrastructure queries
- ✅ Generic abstractions over common APIs

**Extraction effort**: LOW (2-3 hours)

**Shared package name**: `ai-common-devops-tools` or `py-devops-toolkit`

---

## 🔧 Moderately Reusable Modules

### 7. **Monitoring & Telemetry** ⭐⭐⭐
**Files**:
- `src/monitor.py` (small)
- `src/telemetry_logger.py` (small)
- `src/api/monitoring.py` (9.7 KB)

**What it does**:
- Health check endpoints
- Metrics collection
- Log aggregation
- Performance monitoring

**Why share**: Generic monitoring patterns

**Extraction effort**: MEDIUM (3-4 hours)

---

### 8. **Context Management** ⭐⭐⭐
**File**: `src/core/context_manager.py` (12 KB)

**What it does**:
- Conversation context tracking
- Token usage optimization
- Context window management

**Why share**: Useful for chatbot/LLM applications

**Extraction effort**: MEDIUM (needs abstraction)

---

### 9. **Validation Framework** ⭐⭐⭐
**File**: `src/tools/validator.py` (12 KB)

**What it does**:
- Input validation
- Schema validation
- Data sanitization

**Why share**: Generic validation useful everywhere

**Extraction effort**: LOW

---

## 🎨 AI Orchestrator Specific (Don't Share)

### 10. **Intent Classification** ❌
**File**: `src/core/intent_classifier.py` (16 KB)
- Too specific to AI orchestrator routing logic
- Not generic enough

### 11. **Routing Logic** ❌
**File**: `src/core/routing.py` (17 KB)
- Specific to multi-LLM orchestration
- Coupled to provider implementations

### 12. **Collaboration Manager** ❌
**File**: `src/core/collaboration_manager.py` (26 KB)
- Multi-agent coordination logic
- Too domain-specific

### 13. **Orchestrator Core** ❌
**File**: `src/core/orchestrator.py` (33 KB)
- Main orchestration logic
- Highly coupled to the AI orchestrator use case

---

## 📦 Recommended Shared Packages Structure

### Package 1: `ai-common-infrastructure`
```
ai-common-infrastructure/
├── mongodb/
│   ├── connection.py      # MongoDBManager
│   ├── repository.py      # BaseRepository
│   └── models.py          # Base Pydantic models
├── ratelimit/
│   ├── token_bucket.py    # Rate limiter
│   └── circuit_breaker.py # Circuit breaker
└── cache/
    └── semantic_cache.py  # Semantic caching
```

### Package 2: `ai-common-cost-tracking`
```
ai-common-cost-tracking/
├── estimator.py           # Cost estimation
├── budget_manager.py      # Budget tracking
├── alerts.py              # Alert system
└── reporting.py           # Cost reports
```

### Package 3: `ai-common-devops`
```
ai-common-devops/
├── docker/
│   └── docker_ops.py      # Docker operations
├── kubernetes/
│   └── k8s_ops.py         # K8s operations
├── github/
│   └── github_ops.py      # GitHub operations
└── monitoring/
    └── health_checks.py   # Health monitoring
```

### Package 4: `ai-common-session-tracking`
```
ai-common-session-tracking/
├── tracker.py             # Session tracking
├── growth_reflection.py   # Growth insights
└── reporting.py           # Weekly summaries
```

---

## 🎯 Extraction Priority

### Phase 1 (High Value, Low Effort) - 1 week
1. ✅ Rate Limiter (1-2 hours)
2. ✅ DevOps Tools (2-3 hours)
3. ✅ Validation Framework (1 hour)

### Phase 2 (High Value, Medium Effort) - 2 weeks
4. ✅ MongoDB Infrastructure (3-4 hours)
5. ✅ Semantic Cache (3-4 hours)
6. ✅ Cost Tracking (4-5 hours)

### Phase 3 (Medium Value, High Effort) - 3 weeks
7. ✅ Session Tracking (5-6 hours)
8. ✅ Monitoring & Telemetry (3-4 hours)

---

## 🏗️ Extraction Process

For each module:

### 1. Create Standalone Package
```bash
mkdir -p shared-packages/ai-common-ratelimit
cd shared-packages/ai-common-ratelimit
poetry init
```

### 2. Extract Code
- Copy module files
- Remove project-specific dependencies
- Make configuration-driven
- Add comprehensive docstrings

### 3. Add Tests
- Unit tests (pytest)
- Integration tests
- Example usage

### 4. Documentation
- README with usage examples
- API documentation
- Configuration guide

### 5. Publish
```bash
# Private PyPI or Git repository
poetry build
poetry publish
```

### 6. Update Projects
```bash
# In ai-orchestrator
pip install ai-common-ratelimit

# In e-commerce
pip install ai-common-ratelimit

# In sre-analytics
pip install ai-common-ratelimit
```

---

## 📊 Benefits

### Development Efficiency
- ✅ Write once, use everywhere
- ✅ Consistent patterns across projects
- ✅ Reduced code duplication

### Maintenance
- ✅ Single source of truth
- ✅ Bug fixes benefit all projects
- ✅ Easier to improve and optimize

### Collaboration
- ✅ Clear module boundaries
- ✅ Reusable across teams
- ✅ Better documentation incentive

### Testing
- ✅ Shared test suites
- ✅ Higher test coverage
- ✅ More battle-tested code

---

## 🎬 Next Steps

1. **Review this analysis** and prioritize modules
2. **Start with Phase 1** (rate limiter, devops tools, validation)
3. **Create `shared-packages/` directory** in Projects folder
4. **Extract first module** with full tests and docs
5. **Update ai-orchestrator** to use shared package
6. **Test in other projects** (e-commerce, sre-analytics)
7. **Document learnings** and refine process
8. **Continue with Phase 2 and 3**

---

## 🤔 Decision Points

**Question 1**: Should shared packages be:
- Private PyPI server?
- Git submodules?
- Monorepo with Nx/Lerna?

**Question 2**: Versioning strategy:
- Semantic versioning?
- Breaking changes policy?
- Deprecation timeline?

**Question 3**: Ownership:
- Single maintainer?
- Shared ownership?
- Contribution guidelines?

---

**Created**: 2025-11-03
**Status**: Proposal - Awaiting Review
**Estimated Effort**: Phase 1 (1 week), Phase 2 (2 weeks), Phase 3 (3 weeks)
