"""
Automatic session capture triggered by todo completion events.

This module monitors todo state changes and automatically captures sessions
when meaningful work is completed, updating growth reflections without
any manual intervention.
"""

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Optional, List, Dict, Any
import structlog

from src.core.session_tracker import get_session_tracker

logger = structlog.get_logger(__name__)

# Configuration
AUTO_CAPTURE_CONFIG_FILE = Path("config/auto_capture_config.json")
LAST_CAPTURE_FILE = Path("session_data/last_auto_capture.json")


class AutoSessionCapture:
    """Automatically captures sessions when todos are completed."""

    def __init__(self):
        self.config = self._load_config()
        self.last_capture = self._load_last_capture()
        self.session_tracker = get_session_tracker()

    def _load_config(self) -> Dict[str, Any]:
        """Load auto-capture configuration."""
        default_config = {
            "enabled": True,
            "min_completed_todos": 1,  # Minimum todos to trigger capture
            "min_session_hours": 0.5,  # Minimum session duration (30 min)
            "integration_tag": "architecture_enhancements",
            "goal_title": "AI Orchestrator Architecture Enhancements",
            "auto_save_summary": True,  # Save markdown summary
            "capture_on_completion": True  # Capture when todos marked complete
        }

        if AUTO_CAPTURE_CONFIG_FILE.exists():
            with open(AUTO_CAPTURE_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}

        # Create default config
        AUTO_CAPTURE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUTO_CAPTURE_CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def _load_last_capture(self) -> Dict[str, Any]:
        """Load last capture timestamp."""
        if LAST_CAPTURE_FILE.exists():
            with open(LAST_CAPTURE_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_last_capture(self, capture_data: Dict[str, Any]):
        """Save last capture metadata."""
        LAST_CAPTURE_FILE.parent.mkdir(parents=True, exist_ok=True)
        capture_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(LAST_CAPTURE_FILE, 'w') as f:
            json.dump(capture_data, f, indent=2)

    def on_todo_completed(
        self,
        todo_content: str,
        all_todos: List[Dict[str, Any]],
        enhancement_context: Optional[Dict[str, Any]] = None
    ):
        """Triggered when a todo is marked as completed.

        Args:
            todo_content: Content of the completed todo
            all_todos: List of all todos with their states
            enhancement_context: Optional enhancement metadata
        """
        if not self.config["enabled"]:
            logger.info("auto_capture_disabled")
            return

        # Track the accomplishment
        self.session_tracker.add_accomplishment(todo_content)

        # Count completed todos since last capture
        completed_todos = [t for t in all_todos if t.get("status") == "completed"]
        completed_count = len(completed_todos)

        logger.info(
            "todo_completed",
            todo=todo_content,
            completed_count=completed_count,
            total=len(all_todos)
        )

        # Check if we should trigger auto-capture
        should_capture = self._should_auto_capture(completed_todos, all_todos)

        if should_capture:
            logger.info("triggering_auto_capture", reason="todos_completed")
            self.auto_capture(completed_todos, enhancement_context)

    def _should_auto_capture(
        self,
        completed_todos: List[Dict[str, Any]],
        all_todos: List[Dict[str, Any]]
    ) -> bool:
        """Determine if we should auto-capture.

        Args:
            completed_todos: List of completed todos
            all_todos: All todos

        Returns:
            True if should capture
        """
        # Check if enough todos completed
        if len(completed_todos) < self.config["min_completed_todos"]:
            return False

        # Check session duration
        current_session = self.session_tracker.get_current_session_summary()
        duration = current_session.get("duration_hours", 0)

        if duration < self.config["min_session_hours"]:
            logger.info(
                "session_too_short",
                duration_hours=duration,
                min_required=self.config["min_session_hours"]
            )
            return False

        # Check if all todos are completed (end of session)
        all_completed = all(t.get("status") == "completed" for t in all_todos)

        return all_completed or len(completed_todos) >= 3

    def auto_capture(
        self,
        completed_todos: List[Dict[str, Any]],
        enhancement_context: Optional[Dict[str, Any]] = None
    ):
        """Automatically capture session and create growth reflection.

        Args:
            completed_todos: List of completed todos
            enhancement_context: Optional enhancement metadata
        """
        try:
            # Get current session summary
            summary = self.session_tracker.get_current_session_summary()

            # Extract accomplishments from todos
            accomplishments = [t.get("content", "Unknown task") for t in completed_todos]

            # Add accomplishments to session
            for acc in accomplishments:
                if acc not in summary.get("accomplishments", []):
                    self.session_tracker.add_accomplishment(acc)

            # Detect enhancement context from todos
            enhancement_id = None
            enhancement_title = None

            if enhancement_context:
                enhancement_id = enhancement_context.get("id")
                enhancement_title = enhancement_context.get("title")
            else:
                # Try to infer from todo content
                enhancement_id, enhancement_title = self._infer_enhancement_from_todos(completed_todos)

            if enhancement_id:
                self.session_tracker.track_enhancement_work(
                    enhancement_id,
                    enhancement_title or f"Enhancement {enhancement_id}",
                    f"Completed {len(accomplishments)} tasks"
                )

            # Generate and save growth reflection
            reflection_data = self.session_tracker.generate_growth_reflection(
                integration_tag=self.config["integration_tag"],
                goal_title=self.config["goal_title"]
            )

            # Save reflection to growth system
            self._save_reflection(reflection_data)

            # Save markdown summary if enabled
            if self.config["auto_save_summary"]:
                self._save_markdown_summary(summary, reflection_data)

            # End session
            self.session_tracker.end_session()

            # Record this capture
            self._save_last_capture({
                "accomplishments_count": len(accomplishments),
                "duration_hours": summary.get("duration_hours", 0),
                "enhancement_id": enhancement_id,
                "reflection_week": reflection_data.get("week_of")
            })

            logger.info(
                "auto_capture_completed",
                accomplishments_count=len(accomplishments),
                duration_hours=summary.get("duration_hours", 0),
                reflection_created=True
            )

        except Exception as e:
            logger.error("auto_capture_failed", error=str(e))

    def _infer_enhancement_from_todos(
        self,
        todos: List[Dict[str, Any]]
    ) -> tuple[Optional[str], Optional[str]]:
        """Infer enhancement ID from todo content.

        Args:
            todos: List of todos

        Returns:
            (enhancement_id, enhancement_title) or (None, None)
        """
        import re

        for todo in todos:
            content = todo.get("content", "")

            # Look for "Enhancement XXX" pattern
            match = re.search(r'Enhancement\s+(\d+)', content, re.IGNORECASE)
            if match:
                enh_id = match.group(1).zfill(3)
                return enh_id, content

            # Look for "ENH-XXX" pattern
            match = re.search(r'ENH[_-](\d+)', content, re.IGNORECASE)
            if match:
                enh_id = match.group(1).zfill(3)
                return enh_id, content

            # Look for standalone number like "012"
            match = re.search(r'\b(\d{3})\b', content)
            if match:
                return match.group(1), content

        return None, None

    def _save_reflection(self, reflection_data: Dict[str, Any]):
        """Save reflection to growth tracking system.

        Args:
            reflection_data: Reflection data
        """
        from src.api.growth import load_json_data, save_json_data, generate_id, Reflection

        # Load existing reflections
        reflections = load_json_data("reflections")

        # Check if reflection already exists for this week and integration_tag
        week_of = reflection_data.get("week_of")
        integration_tag = reflection_data.get("integration_tag")

        existing_reflection = None
        existing_index = None

        for idx, refl in enumerate(reflections):
            if (refl.get("week_of") == week_of and
                refl.get("integration_tag") == integration_tag):
                existing_reflection = refl
                existing_index = idx
                break

        if existing_reflection:
            # Merge with existing reflection
            logger.info(
                "merging_with_existing_reflection",
                existing_id=existing_reflection.get("id"),
                week_of=week_of
            )

            # Merge accomplishments (avoid duplicates)
            existing_accomplishments = set(existing_reflection.get("accomplishments", []))
            new_accomplishments = reflection_data.get("accomplishments", [])
            merged_accomplishments = list(existing_accomplishments.union(new_accomplishments))

            # Merge topics (avoid duplicates)
            existing_topics = set(existing_reflection.get("topics", []))
            new_topics = reflection_data.get("topics", [])
            merged_topics = list(existing_topics.union(new_topics))

            # Merge blockers (avoid duplicates)
            existing_blockers = set(existing_reflection.get("blockers", []))
            new_blockers = reflection_data.get("blockers", [])
            merged_blockers = list(existing_blockers.union(new_blockers))

            # Add learning hours
            existing_hours = existing_reflection.get("learning_hours", 0.0)
            new_hours = reflection_data.get("learning_hours", 0.0)
            merged_hours = existing_hours + new_hours

            # Update the existing reflection
            existing_reflection["accomplishments"] = merged_accomplishments
            existing_reflection["topics"] = merged_topics
            existing_reflection["blockers"] = merged_blockers
            existing_reflection["learning_hours"] = merged_hours

            # Update insights (append new insights)
            existing_insights = existing_reflection.get("insights", "")
            new_insights = reflection_data.get("insights", "")
            if new_insights and new_insights not in existing_insights:
                existing_reflection["insights"] = f"{existing_insights}\n\n{new_insights}".strip()

            # Update next_week_focus (merge unique items)
            existing_focus = set(existing_reflection.get("next_week_focus", []))
            new_focus = reflection_data.get("next_week_focus", [])
            merged_focus = list(existing_focus.union(new_focus))
            existing_reflection["next_week_focus"] = merged_focus

            # Update progress delta (use the higher value)
            existing_delta = existing_reflection.get("progress_delta", 0)
            new_delta = reflection_data.get("progress_delta", 0)
            existing_reflection["progress_delta"] = max(existing_delta, new_delta)

            reflections[existing_index] = existing_reflection

            logger.info(
                "reflection_updated",
                reflection_id=existing_reflection.get("id"),
                week_of=week_of,
                total_accomplishments=len(merged_accomplishments),
                total_hours=merged_hours
            )
        else:
            # Create new reflection
            reflection = Reflection(**reflection_data)
            reflection.id = generate_id("refl")
            reflections.append(reflection.model_dump())

            logger.info("reflection_saved", reflection_id=reflection.id, week_of=reflection.week_of)

        save_json_data("reflections", reflections)

    def _save_markdown_summary(
        self,
        session_summary: Dict[str, Any],
        reflection_data: Dict[str, Any]
    ):
        """Save session summary as markdown file.

        Args:
            session_summary: Session summary data
            reflection_data: Reflection data
        """
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        summary_file = Path(f"session_data/summaries/SESSION_SUMMARY_{date}.md")
        summary_file.parent.mkdir(parents=True, exist_ok=True)

        content = f"""# Session Summary: {date}

## Overview
- **Duration:** {session_summary.get('duration_hours', 0):.1f} hours
- **Activities:** {session_summary.get('activities', {}).get('total', 0)}
- **Files Modified:** {session_summary.get('files', {}).get('total', 0)}
- **Enhancements:** {session_summary.get('enhancements', {}).get('count', 0)}

## Accomplishments
{self._format_list(reflection_data.get('accomplishments', []))}

## Topics Covered
{self._format_list(reflection_data.get('topics', []))}

## Technologies Used
{self._format_list(session_summary.get('technologies', []))}

## Blockers
{self._format_list(reflection_data.get('blockers', [])) if reflection_data.get('blockers') else '_No blockers_'}

## Insights
{reflection_data.get('insights', 'No insights generated.')}

## Next Week Focus
{self._format_list(reflection_data.get('next_week_focus', []))}

---
_Auto-generated by AI Orchestrator Session Tracker_
"""

        with open(summary_file, 'w') as f:
            f.write(content)

        logger.info("summary_saved", file=str(summary_file))

    def _format_list(self, items: List[str]) -> str:
        """Format list as markdown.

        Args:
            items: List of items

        Returns:
            Markdown formatted list
        """
        if not items:
            return "_None_"
        return "\n".join(f"- {item}" for item in items)


# Global instance
_auto_capture: Optional[AutoSessionCapture] = None


def get_auto_capture() -> AutoSessionCapture:
    """Get or create global auto-capture instance."""
    global _auto_capture
    if _auto_capture is None:
        _auto_capture = AutoSessionCapture()
    return _auto_capture


def on_todo_completed(
    todo_content: str,
    all_todos: List[Dict[str, Any]],
    enhancement_context: Optional[Dict[str, Any]] = None
):
    """Hook called when a todo is completed.

    This is the main entry point for automatic session capture.

    Args:
        todo_content: Content of completed todo
        all_todos: All todos with their states
        enhancement_context: Optional enhancement metadata
    """
    auto_capture = get_auto_capture()
    auto_capture.on_todo_completed(todo_content, all_todos, enhancement_context)
