# Documentation Governance Rules

**Effective Date:** 2025-10-21
**Purpose:** Prevent documentation duplication and maintain single source of truth
**Status:** **MANDATORY** - All project contributors must follow these rules

---

## 🎯 Core Principle

**ONE TOPIC = ONE LOCATION = ONE FILE**

Never duplicate documentation. Always update the canonical source.

---

## 📁 Documentation Structure (Single Source of Truth)

### 1. Project Tracking

| Topic | Canonical Location | Update Frequency | Owner |
|-------|-------------------|------------------|-------|
| **Enhancement Roadmap** | `PROJECT_ENHANCEMENT_TRACKER_DB.yaml` | Per enhancement completion | Tech Lead |
| **Tactical Planning** | `NEXT_STEPS_ROADMAP.md` | Weekly | Tech Lead |
| **Enhancement Reports** | `docs/enhancements/ENHANCEMENT_00X_COMPLETE.md` | Once (at completion) | Developer |

**Rules:**
- ❌ Never create alternative tracker files
- ❌ Never copy enhancement specs to other files
- ✅ Always reference the YAML for enhancement details
- ✅ Link to completion reports, don't duplicate content

---

### 2. Setup & Configuration

| Topic | Canonical Location | Update Frequency | Owner |
|-------|-------------------|------------------|-------|
| **Initial Setup** | `docs/setup/SETUP_GUIDE.md` | When setup changes | Tech Lead |
| **Python Migration** | `docs/setup/PYTHON_3.13_MIGRATION.md` | Frozen (historical) | N/A |
| **Quick Reference** | `docs/QUICK_REFERENCE.md` | When commands change | All developers |

**Rules:**
- ❌ Don't create `INSTALL.md`, `GETTING_STARTED.md`, etc.
- ❌ Don't duplicate setup instructions in README
- ✅ Link README to `docs/setup/SETUP_GUIDE.md`
- ✅ Update QUICK_REFERENCE when adding new commands

---

### 3. Architecture & Design

| Topic | Canonical Location | Update Frequency | Owner |
|-------|-------------------|------------------|-------|
| **System Architecture** | `docs/ARCHITECTURE.md` | When architecture changes | Architect |
| **Database Schema** | `docs/DATABASE_SCHEMA.md` | When schema changes | DBA/Architect |
| **API Reference** | `docs/api-reference.md` | When API changes | Backend Lead |
| **Routing Patterns** | `docs/routing-patterns.md` | When routing changes | ML Engineer |

**Rules:**
- ❌ Don't create `DESIGN.md`, `SYSTEM_DESIGN.md`, etc.
- ❌ Don't duplicate architecture diagrams
- ✅ Use Mermaid diagrams in canonical files
- ✅ Reference architecture docs from completion reports

---

### 4. Development Guides

| Topic | Canonical Location | Update Frequency | Owner |
|-------|-------------------|------------------|-------|
| **IDE Configuration** | `.vscode/settings.json` | When IDE setup changes | All developers |
| **CI/CD Pipeline** | `.github/workflows/python-ci.yml` | When pipeline changes | DevOps |
| **Code Style** | `pyproject.toml` | Rarely | Tech Lead |

**Rules:**
- ❌ Don't create separate IDE setup docs
- ❌ Don't duplicate CI/CD instructions
- ✅ Comment configuration files well
- ✅ Link to official docs for tools

---

## 🚫 Forbidden Actions

### Never Do This:

1. **Create duplicate trackers**
   ```bash
   ❌ touch PROJECT_TRACKER_V2.yaml
   ❌ touch ENHANCEMENT_LIST.md
   ❌ touch TODO.md
   ```

2. **Copy documentation to multiple places**
   ```bash
   ❌ cp docs/SETUP_GUIDE.md INSTALL.md
   ❌ cp docs/API_REFERENCE.md README_API.md
   ```

3. **Create alternative documentation structures**
   ```bash
   ❌ mkdir documentation/  # We use docs/
   ❌ mkdir guides/         # We use docs/
   ```

4. **Duplicate enhancement details**
   ```yaml
   ❌ Copy enhancement spec to completion report
   ✅ Reference enhancement ID and link to YAML
   ```

---

## ✅ Required Actions

### When Creating Documentation:

1. **Check if canonical location exists**
   ```bash
   # Search existing docs first
   grep -r "topic name" docs/
   ```

2. **If exists: Update canonical file**
   ```bash
   # Edit the existing file
   nano docs/setup/SETUP_GUIDE.md
   ```

3. **If doesn't exist: Create in correct location**
   ```bash
   # Follow the structure
   touch docs/{category}/{DESCRIPTIVE_NAME}.md
   ```

4. **Update documentation index**
   ```bash
   # Add to docs/README.md
   nano docs/README.md
   ```

---

## 📋 Documentation Lifecycle

### Stage 1: Creation

**Before creating any documentation:**

1. Check: Does this topic already exist?
   ```bash
   find docs/ -name "*.md" -exec grep -l "topic" {} \;
   ```

2. Determine category:
   - Setup/Config → `docs/setup/`
   - Enhancement → `docs/enhancements/`
   - Architecture → `docs/architecture/`
   - Development → `docs/development/`
   - API/Reference → `docs/`

3. Create in canonical location only

4. Update `docs/README.md` index

### Stage 2: Maintenance

**When updating documentation:**

1. Find canonical source:
   ```bash
   grep -r "topic" docs/README.md  # Check index
   ```

2. Update ONLY the canonical file

3. Update "Last Updated" date

4. Commit with clear message:
   ```bash
   git commit -m "docs(setup): update Python version to 3.13"
   ```

### Stage 3: Deprecation

**When documentation becomes outdated:**

1. Move to `archive/`:
   ```bash
   mkdir -p archive/docs-YYYY-MM-DD
   mv docs/old-file.md archive/docs-2025-10-21/
   ```

2. Update index to remove reference

3. Add redirect/note if needed

---

## 🔍 Documentation Audit Process

### Weekly Audit (Every Monday)

```bash
# 1. Find potential duplicates
find . -name "*.md" -o -name "*.yaml" | grep -i "track\|todo\|roadmap" | grep -v node_modules | grep -v venv

# 2. Check for orphaned docs
find docs/ -name "*.md" ! -path "*/node_modules/*" -exec basename {} \; | while read file; do
  grep -q "$file" docs/README.md || echo "Orphaned: $file"
done

# 3. Verify index is complete
ls docs/**/*.md | while read file; do
  basename=$(basename "$file")
  grep -q "$basename" docs/README.md || echo "Not indexed: $file"
done
```

### Monthly Audit (First of Month)

1. Review all documentation for accuracy
2. Update "Last Updated" dates
3. Archive obsolete docs
4. Update documentation map
5. Check cross-references

---

## 📊 File Naming Convention

### Standard Format:
```
{CATEGORY}_{DESCRIPTIVE_NAME}.md
```

### Examples:
- ✅ `SETUP_GUIDE.md`
- ✅ `ENHANCEMENT_001_COMPLETE.md`
- ✅ `PYTHON_3.13_MIGRATION.md`
- ❌ `setup.md` (too generic)
- ❌ `guide.md` (too vague)
- ❌ `001.md` (not descriptive)

### File Organization:
```
docs/
├── {CATEGORY}/
│   └── {DESCRIPTIVE_FILE}.md
└── {REFERENCE_FILE}.md
```

---

## 🎯 Enforcement

### Pre-commit Checks

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Check for duplicate tracker files
TRACKERS=$(find . -maxdepth 2 -name "*tracker*.yaml" ! -name "PROJECT_ENHANCEMENT_TRACKER_DB.yaml" | wc -l)
if [ $TRACKERS -gt 0 ]; then
  echo "❌ Found duplicate tracker files. Only PROJECT_ENHANCEMENT_TRACKER_DB.yaml should exist."
  exit 1
fi

# Check for documentation in wrong location
if ls *.md 2>/dev/null | grep -q "SETUP\|INSTALL\|GUIDE"; then
  echo "❌ Setup/guide docs should be in docs/setup/, not root"
  exit 1
fi

echo "✅ Documentation governance checks passed"
```

### Code Review Checklist

When reviewing PRs with documentation changes:

- [ ] Is this updating the canonical file (not creating duplicate)?
- [ ] Is the file in the correct `docs/` subdirectory?
- [ ] Is `docs/README.md` updated to reference new doc?
- [ ] Is "Last Updated" date current?
- [ ] Are cross-references still valid?

---

## 📚 Migration Plan (For Existing Project)

### Phase 1: Audit (Completed 2025-10-21)

- [x] Identify all tracking files
- [x] Identify duplicate documentation
- [x] Create governance rules

### Phase 2: Cleanup (Next)

```bash
# 1. Create archive
mkdir -p archive/legacy-trackers-2025-10-21

# 2. Move duplicates
mv PROJECT_ENHANCEMENT_TRACKER.yaml archive/legacy-trackers-2025-10-21/
mv docs/project_enhancement_tracker.md archive/legacy-trackers-2025-10-21/

# 3. Investigate and clean
cat personal_tracker_data.json  # Check if needed
# If not needed:
mv personal_tracker_data.json archive/legacy-trackers-2025-10-21/

# 4. Update .gitignore
echo "archive/" >> .gitignore

# 5. Commit cleanup
git add .
git commit -m "chore(docs): consolidate tracking to single source of truth

- Archive duplicate PROJECT_ENHANCEMENT_TRACKER.yaml
- Archive legacy project_enhancement_tracker.md
- Establish documentation governance rules
- Update .gitignore for archive directory

See DOCUMENTATION_GOVERNANCE.md for new rules."
```

### Phase 3: Prevention (Ongoing)

- [ ] Add pre-commit hooks
- [ ] Weekly audits
- [ ] Monthly reviews
- [ ] Team training on governance rules

---

## 🎓 Training & Onboarding

### For New Contributors:

**Required Reading:**
1. `DOCUMENTATION_GOVERNANCE.md` (this file)
2. `docs/README.md` (documentation index)
3. `docs/DOCUMENTATION_MAP.md` (visual guide)

**Key Takeaways:**
- One topic = one file
- Check `docs/README.md` before creating docs
- Update canonical source only
- Archive, don't delete

---

## 🔧 Tools & Automation

### Documentation Linter (Future)

```python
# scripts/lint_docs.py
def check_duplicates():
    """Check for duplicate documentation files."""
    # Implementation

def check_index():
    """Verify all docs are indexed in README."""
    # Implementation

def check_structure():
    """Ensure docs are in correct directories."""
    # Implementation
```

### Documentation Generator (Future)

```bash
# scripts/new_doc.sh
./scripts/new_doc.sh --category setup --name "Docker Setup"
# Creates: docs/setup/DOCKER_SETUP.md
# Updates: docs/README.md
# Commits: "docs(setup): add Docker setup guide"
```

---

## ✅ Success Criteria

Documentation governance is successful when:

- ✅ Zero duplicate tracker files
- ✅ Zero duplicate documentation
- ✅ All docs indexed in `docs/README.md`
- ✅ All docs in correct `docs/` subdirectory
- ✅ All docs have "Last Updated" date
- ✅ All docs cross-referenced correctly
- ✅ Weekly audits show no issues

---

## 📞 Questions?

If unsure about where documentation belongs:

1. Check `docs/README.md` index
2. Check `docs/DOCUMENTATION_MAP.md`
3. Check `TRACKING_FILES_AUDIT.md`
4. Ask in team chat / create issue

**When in doubt: Don't duplicate. Ask first.**

---

**Approved by:** Tech Lead
**Effective Date:** 2025-10-21
**Review Date:** Monthly
**Version:** 1.0
