# Automatic Session Capture - Integration Guide

## Overview

The automatic session capture system is now fully implemented and ready to use. It automatically creates growth reflections when you complete work, without requiring any manual endpoint calls.

## How It Works

### 1. Event-Driven Architecture

When you mark a todo as **completed**, the system automatically:
1. Tracks the accomplishment
2. Checks if conditions are met for auto-capture
3. Generates a growth reflection
4. Saves it to the growth tracking system
5. Creates a markdown summary

### 2. Auto-Capture Conditions

The system will automatically capture when:
- ✅ At least **1 todo** is completed
- ✅ Session duration is at least **30 minutes**
- ✅ Either:
  - All todos are marked as completed (end of session), OR
  - 3 or more todos have been completed

### 3. Configuration

Edit `config/auto_capture_config.json` to customize behavior:

```json
{
  "enabled": true,                          // Turn auto-capture on/off
  "min_completed_todos": 1,                 // Minimum todos to trigger
  "min_session_hours": 0.5,                 // Minimum duration (30 min)
  "integration_tag": "architecture_enhancements",
  "goal_title": "AI Orchestrator Architecture Enhancements",
  "auto_save_summary": true,                // Save markdown summary
  "capture_on_completion": true,            // Capture when todos complete
  "auto_detect_enhancement": true,          // Auto-detect enhancement from todo
  "inactivity_threshold_minutes": 30        // Session timeout
}
```

## Integration Methods

### Method 1: Programmatic Hook (Recommended for Claude Code)

The `on_todo_completed()` function is exposed as a public API:

```python
from src.core.auto_session_capture import on_todo_completed

# When a todo is marked as completed
on_todo_completed(
    todo_content="Implement automatic session capture",
    all_todos=[
        {"content": "Task 1", "status": "completed"},
        {"content": "Task 2", "status": "completed"},
        {"content": "Task 3", "status": "pending"}
    ],
    enhancement_context={
        "id": "012",
        "title": "State Management & Persistence"
    }
)
```

**Integration Point for Claude Code:**
- This function should be called by Claude Code's internal todo management system
- Whenever `TodoWrite` is called with a todo marked as `status: "completed"`
- The function handles everything else automatically

### Method 2: Standalone Script (Manual Trigger)

Run the script manually after completing work:

```bash
# Basic usage (auto-detects enhancement from session)
python scripts/auto_capture_on_completion.py

# With specific enhancement context
python scripts/auto_capture_on_completion.py \
  --enhancement-id 012 \
  --title "State Management & Persistence"

# Force capture even if session is short
python scripts/auto_capture_on_completion.py --force
```

### Method 3: Git Hooks (Automatic on Commit)

Add to `.git/hooks/post-commit`:

```bash
#!/bin/bash
# Auto-capture session on git commit
cd /Users/shiva/Projects/ai-orchestrator
./venv/bin/python scripts/auto_capture_on_completion.py --force
```

Make it executable:
```bash
chmod +x .git/hooks/post-commit
```

### Method 4: IDE Automation

Configure your IDE to run the script when saving files or on other triggers.

## What Gets Captured

### Session Data
- **Duration**: Total time spent on the session
- **Activities**: All tracked activities (file edits, commands, etc.)
- **Files Modified**: List of files changed during session
- **Enhancements**: Which enhancements were worked on
- **Accomplishments**: All completed todos
- **Topics**: Technologies and concepts covered
- **Blockers**: Any issues encountered
- **Technologies**: Tools and frameworks used

### Growth Reflection
Automatically generated with:
- **Accomplishments**: Derived from completed todos
- **Topics**: Extracted from session activities
- **Technologies**: Detected from file types and activities
- **Insights**: AI-generated summary of learnings
- **Blockers**: Any challenges faced
- **Next Week Focus**: Suggested priorities
- **Progress Delta**: Estimated progress percentage
- **Learning Hours**: Time spent on session

### Outputs Created
1. **Growth Reflection**: Added to `growth_data/reflections.json`
2. **Markdown Summary**: Saved to `session_data/summaries/SESSION_SUMMARY_YYYY-MM-DD.md`
3. **Session Archive**: Session data saved to `session_data/sessions/`

## Example Workflow

### Scenario: Working on Enhancement 012

1. **Start working** - Session tracker starts automatically
2. **Complete tasks** - Mark todos as completed:
   ```
   ✅ Create MongoDB schema
   ✅ Implement repositories
   ✅ Create migration script
   ```
3. **Auto-capture triggers** - When all 3 todos are completed:
   - Detects Enhancement 012 from todo content
   - Captures 2.5 hours of work
   - Generates growth reflection
   - Saves summary to `session_data/summaries/SESSION_SUMMARY_2025-11-02.md`

4. **View results** - Open growth tracking web UI:
   ```bash
   # View the reflection in the UI
   open http://localhost:5173
   ```

## Verification

### Check if auto-capture is enabled:
```bash
cat config/auto_capture_config.json | grep enabled
```

### View recent session summaries:
```bash
ls -lh session_data/summaries/
```

### View growth reflections:
```bash
cat growth_data/reflections.json | jq '.[] | select(.week_of >= "2025-11-02")'
```

### Test manual capture:
```bash
python scripts/auto_capture_on_completion.py --force
```

## Troubleshooting

### Auto-capture not triggering?

1. **Check configuration**:
   ```bash
   cat config/auto_capture_config.json
   ```
   Ensure `enabled: true` and `capture_on_completion: true`

2. **Check session duration**:
   - Must be at least 30 minutes (0.5 hours)
   - Use `--force` to override: `python scripts/auto_capture_on_completion.py --force`

3. **Check completed todos**:
   - Must have at least 1 completed todo
   - Accomplishments are tracked via `add_accomplishment()`

4. **Check logs**:
   ```bash
   grep auto_capture session_data/logs/*.log
   ```

### Session not tracking activities?

The session tracker automatically tracks:
- File modifications (when files are saved)
- Enhancement work (when enhancement IDs mentioned in todos)
- Accomplishments (when todos marked completed)

Ensure you're using the TodoWrite tool to mark todos as completed.

### Growth reflection not appearing in UI?

1. **Verify reflection was saved**:
   ```bash
   cat growth_data/reflections.json | jq '.[-1]'
   ```

2. **Check reflection format**:
   ```bash
   cat growth_data/reflections.json | jq '.[-1] | keys'
   ```

3. **Restart frontend** to refresh data:
   ```bash
   cd frontend
   npm run dev
   ```

## Benefits

✅ **No Manual Work**: Reflections created automatically when you complete tasks
✅ **Accurate Tracking**: Captures real-time session data
✅ **Consistent Format**: All reflections follow same structure
✅ **Enhancement Linking**: Automatically links work to enhancements
✅ **Progress Visibility**: See your progress without manual tracking
✅ **Historical Record**: Markdown summaries preserve session details

## Next Steps

1. **Test the system**: Complete a few todos and verify auto-capture works
2. **Customize config**: Adjust thresholds in `config/auto_capture_config.json`
3. **Review summaries**: Check `session_data/summaries/` for generated reports
4. **Monitor growth**: View growth tracking page to see reflections

## Integration with Claude Code

**For Claude Code developers**: The ideal integration point is to call `on_todo_completed()` from within Claude Code's `TodoWrite` tool implementation:

```python
# Inside TodoWrite tool implementation
from src.core.auto_session_capture import on_todo_completed

def todo_write(todos: List[Dict]):
    # ... existing todo write logic ...

    # Detect completed todos
    for todo in todos:
        if todo.get("status") == "completed":
            on_todo_completed(
                todo_content=todo["content"],
                all_todos=todos,
                enhancement_context=_extract_enhancement_context(todos)
            )
```

This ensures automatic capture happens seamlessly whenever work is completed.

---

**Status**: ✅ Automatic session capture is fully implemented and ready to use!

**Last Updated**: 2025-11-02
