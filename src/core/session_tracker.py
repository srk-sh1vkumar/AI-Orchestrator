"""
Automatic session tracking and growth reflection generation.

Tracks development sessions and automatically generates growth reflections
at the end of each meaningful session.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import structlog
from collections import defaultdict

logger = structlog.get_logger(__name__)

# Session data directory
SESSION_DATA_DIR = Path("session_data")
SESSION_DATA_DIR.mkdir(exist_ok=True)


class SessionTracker:
    """Tracks development sessions and generates insights."""

    def __init__(self):
        self.session_file = SESSION_DATA_DIR / "current_session.json"
        self.sessions_history = SESSION_DATA_DIR / "sessions_history.json"
        self.current_session: Optional[Dict[str, Any]] = None
        self._load_current_session()

    def _load_current_session(self):
        """Load current session from disk."""
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                self.current_session = json.load(f)
                logger.info("session_loaded", session_id=self.current_session.get("session_id"))
        else:
            self._start_new_session()

    def _save_current_session(self):
        """Save current session to disk."""
        if self.current_session:
            with open(self.session_file, 'w') as f:
                json.dump(self.current_session, f, indent=2, default=str)

    def _start_new_session(self):
        """Start a new session."""
        session_id = f"session_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        self.current_session = {
            "session_id": session_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,
            "duration_minutes": 0,
            "activities": [],
            "files_modified": [],
            "enhancements_worked_on": [],
            "topics_covered": [],
            "accomplishments": [],
            "blockers": [],
            "technologies_used": [],
            "learning_hours": 0.0,
        }
        self._save_current_session()
        logger.info("new_session_started", session_id=session_id)

    def track_activity(
        self,
        activity_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track an activity in the current session.

        Args:
            activity_type: Type of activity (code, documentation, debugging, etc.)
            description: Description of the activity
            metadata: Additional metadata
        """
        if not self.current_session:
            self._start_new_session()

        activity = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": activity_type,
            "description": description,
            "metadata": metadata or {}
        }

        self.current_session["activities"].append(activity)
        self._save_current_session()
        logger.info("activity_tracked", type=activity_type, description=description)

    def track_file_modification(self, file_path: str, operation: str):
        """Track file modification.

        Args:
            file_path: Path to the file
            operation: Operation type (create, edit, delete)
        """
        if not self.current_session:
            self._start_new_session()

        file_entry = {
            "path": file_path,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.current_session["files_modified"].append(file_entry)
        self._save_current_session()

    def track_enhancement_work(
        self,
        enhancement_id: str,
        title: str,
        work_description: str
    ):
        """Track work on an enhancement.

        Args:
            enhancement_id: Enhancement ID (e.g., "012")
            title: Enhancement title
            work_description: Description of work done
        """
        if not self.current_session:
            self._start_new_session()

        # Check if enhancement already tracked
        existing = next(
            (e for e in self.current_session["enhancements_worked_on"]
             if e["id"] == enhancement_id),
            None
        )

        if existing:
            existing["work_items"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "description": work_description
            })
        else:
            self.current_session["enhancements_worked_on"].append({
                "id": enhancement_id,
                "title": title,
                "work_items": [{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "description": work_description
                }]
            })

        self._save_current_session()

    def add_topic(self, topic: str):
        """Add a topic covered in this session.

        Args:
            topic: Topic or technology learned
        """
        if not self.current_session:
            self._start_new_session()

        if topic not in self.current_session["topics_covered"]:
            self.current_session["topics_covered"].append(topic)
            self._save_current_session()

    def add_accomplishment(self, accomplishment: str):
        """Add an accomplishment for this session.

        Args:
            accomplishment: What was accomplished
        """
        if not self.current_session:
            self._start_new_session()

        self.current_session["accomplishments"].append(accomplishment)
        self._save_current_session()

    def add_blocker(self, blocker: str):
        """Add a blocker encountered in this session.

        Args:
            blocker: Description of the blocker
        """
        if not self.current_session:
            self._start_new_session()

        self.current_session["blockers"].append(blocker)
        self._save_current_session()

    def add_technology(self, technology: str):
        """Add a technology used in this session.

        Args:
            technology: Technology or tool used
        """
        if not self.current_session:
            self._start_new_session()

        if technology not in self.current_session["technologies_used"]:
            self.current_session["technologies_used"].append(technology)
            self._save_current_session()

    def end_session(self) -> Dict[str, Any]:
        """End the current session and calculate metrics.

        Returns:
            Session summary
        """
        if not self.current_session:
            logger.warning("no_active_session")
            return {}

        # Calculate duration
        start_time = datetime.fromisoformat(self.current_session["start_time"])
        end_time = datetime.now(timezone.utc)
        duration = end_time - start_time

        self.current_session["end_time"] = end_time.isoformat()
        self.current_session["duration_minutes"] = int(duration.total_seconds() / 60)
        self.current_session["learning_hours"] = round(duration.total_seconds() / 3600, 1)

        # Save to history
        self._save_to_history()

        # Generate session summary
        summary = self._generate_session_summary()

        # Archive current session
        self._save_current_session()
        logger.info(
            "session_ended",
            session_id=self.current_session["session_id"],
            duration_minutes=self.current_session["duration_minutes"]
        )

        return summary

    def _save_to_history(self):
        """Save current session to history."""
        history = []
        if self.sessions_history.exists():
            with open(self.sessions_history, 'r') as f:
                history = json.load(f)

        history.append(self.current_session)

        # Keep only last 100 sessions
        if len(history) > 100:
            history = history[-100:]

        with open(self.sessions_history, 'w') as f:
            json.dump(history, f, indent=2, default=str)

    def _generate_session_summary(self) -> Dict[str, Any]:
        """Generate a summary of the session.

        Returns:
            Session summary with insights
        """
        session = self.current_session

        # Group activities by type
        activities_by_type = defaultdict(int)
        for activity in session["activities"]:
            activities_by_type[activity["type"]] += 1

        # Count unique files modified
        files_created = sum(1 for f in session["files_modified"] if f["operation"] == "create")
        files_edited = sum(1 for f in session["files_modified"] if f["operation"] == "edit")

        summary = {
            "session_id": session["session_id"],
            "date": session["start_time"][:10],  # YYYY-MM-DD
            "duration_hours": session["learning_hours"],
            "activities": {
                "total": len(session["activities"]),
                "by_type": dict(activities_by_type)
            },
            "files": {
                "created": files_created,
                "edited": files_edited,
                "total": len(session["files_modified"])
            },
            "enhancements": {
                "count": len(session["enhancements_worked_on"]),
                "details": session["enhancements_worked_on"]
            },
            "topics": session["topics_covered"],
            "accomplishments": session["accomplishments"],
            "blockers": session["blockers"],
            "technologies": session["technologies_used"]
        }

        return summary

    def generate_growth_reflection(
        self,
        integration_tag: str,
        goal_title: str,
        week_of: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a growth reflection from the current session.

        Args:
            integration_tag: Tag linking to a goal
            goal_title: Title of the goal
            week_of: Week start date (defaults to current week Monday)

        Returns:
            Growth reflection data
        """
        if not self.current_session:
            logger.warning("no_active_session_for_reflection")
            return {}

        # Determine week_of (Monday of current week)
        if not week_of:
            now = datetime.now(timezone.utc)
            days_since_monday = now.weekday()
            monday = now - timedelta(days=days_since_monday)
            week_of = monday.strftime("%Y-%m-%d")

        summary = self._generate_session_summary()

        # Estimate progress delta based on accomplishments
        progress_delta = min(len(summary["accomplishments"]) * 5, 30)

        # Generate insights
        insights = self._generate_insights(summary)

        # Generate next week focus
        next_week_focus = self._generate_next_week_focus(summary)

        reflection = {
            "integration_tag": integration_tag,
            "week_of": week_of,
            "learning_hours": summary["duration_hours"],
            "topics": summary["topics"],
            "goal_title": goal_title,
            "progress_delta": progress_delta,
            "accomplishments": summary["accomplishments"],
            "blockers": summary["blockers"],
            "insights": insights,
            "next_week_focus": next_week_focus
        }

        logger.info(
            "growth_reflection_generated",
            integration_tag=integration_tag,
            week_of=week_of,
            progress_delta=progress_delta
        )

        return reflection

    def _generate_insights(self, summary: Dict[str, Any]) -> str:
        """Generate insights from session summary.

        Args:
            summary: Session summary

        Returns:
            Insights text
        """
        insights_parts = []

        # Session overview
        if summary["duration_hours"] >= 2:
            insights_parts.append(
                f"Productive {summary['duration_hours']:.1f}-hour session "
                f"focused on {len(summary['enhancements']['count'])} enhancement(s)."
            )

        # Key accomplishments
        if summary["accomplishments"]:
            top_accomplishments = summary["accomplishments"][:3]
            insights_parts.append(
                "Key achievements: " + "; ".join(top_accomplishments) + "."
            )

        # Technologies learned
        if summary["technologies"]:
            insights_parts.append(
                f"Gained hands-on experience with {', '.join(summary['technologies'][:5])}."
            )

        # Blockers
        if summary["blockers"]:
            insights_parts.append(
                f"Encountered {len(summary['blockers'])} challenge(s) "
                "that need resolution."
            )

        # Code activity
        if summary["files"]["created"] > 0:
            insights_parts.append(
                f"Created {summary['files']['created']} new file(s), "
                f"modified {summary['files']['edited']} existing file(s)."
            )

        return " ".join(insights_parts) if insights_parts else "Session completed successfully."

    def _generate_next_week_focus(self, summary: Dict[str, Any]) -> List[str]:
        """Generate next week focus items from blockers and incomplete work.

        Args:
            summary: Session summary

        Returns:
            List of focus items
        """
        focus_items = []

        # Add unresolved blockers
        for blocker in summary["blockers"]:
            focus_items.append(f"Resolve: {blocker}")

        # Add continuation of incomplete work
        for enh in summary["enhancements"]["details"]:
            focus_items.append(f"Continue work on {enh['title']}")

        # Default items if none generated
        if not focus_items:
            focus_items = [
                "Review and test completed implementations",
                "Document architectural decisions",
                "Plan next enhancements"
            ]

        return focus_items[:5]  # Limit to 5 items

    def get_current_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session without ending it.

        Returns:
            Current session summary
        """
        if not self.current_session:
            return {}

        return self._generate_session_summary()


# Global session tracker instance
_session_tracker: Optional[SessionTracker] = None


def get_session_tracker() -> SessionTracker:
    """Get or create global session tracker instance."""
    global _session_tracker
    if _session_tracker is None:
        _session_tracker = SessionTracker()
    return _session_tracker
