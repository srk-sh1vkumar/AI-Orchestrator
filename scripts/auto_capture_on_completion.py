#!/usr/bin/env python3
"""
Auto-capture script triggered when Claude Code marks todos as complete.

This script is designed to be called automatically (e.g., via git hooks or
IDE automation) whenever significant work is completed.

Usage:
    # Manually trigger after completing work
    python scripts/auto_capture_on_completion.py

    # Or with specific context
    python scripts/auto_capture_on_completion.py --enhancement-id 012 --title "Enhancement Tracking DB"
"""

import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.session_tracker import get_session_tracker
from src.api.growth import load_json_data, save_json_data, generate_id, Reflection


async def auto_capture(
    enhancement_id: str = None,
    enhancement_title: str = None,
    force: bool = False
):
    """Auto-capture current session.

    Args:
        enhancement_id: Optional enhancement ID
        enhancement_title: Optional enhancement title
        force: Force capture even if session is short
    """
    tracker = get_session_tracker()

    # Get current session summary
    summary = tracker.get_current_session_summary()

    # Check if session is meaningful
    duration = summary.get("duration_hours", 0)
    accomplishments_count = len(summary.get("accomplishments", []))

    print(f"📊 Current Session Status")
    print(f"   Duration: {duration:.1f} hours")
    print(f"   Accomplishments: {accomplishments_count}")
    print(f"   Files Modified: {summary.get('files', {}).get('total', 0)}")
    print(f"   Topics: {len(summary.get('topics', []))}")
    print()

    # Decide if we should capture
    if not force and duration < 0.5:
        print("⏱️  Session too short (< 30 min), skipping auto-capture")
        print("   Use --force to override")
        return

    if accomplishments_count == 0:
        print("⚠️  No accomplishments tracked, skipping auto-capture")
        print("   Accomplishments are typically added via TodoWrite tool")
        return

    # Load configuration
    config_file = project_root / "config" / "auto_capture_config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "integration_tag": "architecture_enhancements",
            "goal_title": "AI Orchestrator Architecture Enhancements"
        }

    # Track enhancement if provided
    if enhancement_id:
        tracker.track_enhancement_work(
            enhancement_id,
            enhancement_title or f"Enhancement {enhancement_id}",
            "Session work completed"
        )

    # Generate reflection
    print("🔄 Generating growth reflection...")
    reflection_data = tracker.generate_growth_reflection(
        integration_tag=config.get("integration_tag", "architecture_enhancements"),
        goal_title=config.get("goal_title", "AI Orchestrator Architecture Enhancements")
    )

    # Save reflection (check for existing reflection for this week)
    reflections = load_json_data("reflections")

    week_of = reflection_data.get("week_of")
    integration_tag = reflection_data.get("integration_tag")

    # Find existing reflection for this week
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
        print(f"📝 Found existing reflection for week {week_of}, merging...")

        # Merge accomplishments (avoid duplicates)
        existing_accomplishments = set(existing_reflection.get("accomplishments", []))
        new_accomplishments = reflection_data.get("accomplishments", [])
        merged_accomplishments = list(existing_accomplishments.union(new_accomplishments))

        # Merge topics
        existing_topics = set(existing_reflection.get("topics", []))
        new_topics = reflection_data.get("topics", [])
        merged_topics = list(existing_topics.union(new_topics))

        # Add learning hours
        existing_hours = existing_reflection.get("learning_hours", 0.0)
        new_hours = reflection_data.get("learning_hours", 0.0)
        merged_hours = existing_hours + new_hours

        # Update existing reflection
        existing_reflection["accomplishments"] = merged_accomplishments
        existing_reflection["topics"] = merged_topics
        existing_reflection["learning_hours"] = merged_hours

        # Update progress delta (use the higher value)
        existing_delta = existing_reflection.get("progress_delta", 0)
        new_delta = reflection_data.get("progress_delta", 0)
        existing_reflection["progress_delta"] = max(existing_delta, new_delta)

        reflections[existing_index] = existing_reflection

        print(f"✅ Growth reflection updated: {existing_reflection.get('id')}")
        reflection_id = existing_reflection.get("id")
        reflection_learning_hours = merged_hours
        reflection_progress_delta = existing_reflection["progress_delta"]
    else:
        # Create new reflection
        reflection = Reflection(**reflection_data)
        reflection.id = generate_id("refl")
        reflections.append(reflection.model_dump())

        print(f"✅ Growth reflection created: {reflection.id}")
        reflection_id = reflection.id
        reflection_learning_hours = reflection.learning_hours
        reflection_progress_delta = reflection.progress_delta

    save_json_data("reflections", reflections)
    print(f"   Week of: {week_of}")
    print(f"   Learning hours: {reflection_learning_hours:.1f}")
    print(f"   Progress delta: {reflection_progress_delta}%")
    print()

    # Save markdown summary
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary_file = project_root / "session_data" / "summaries" / f"SESSION_SUMMARY_{date}.md"
    summary_file.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# Session Summary: {date}

## Overview
- **Duration:** {duration:.1f} hours
- **Activities:** {summary.get('activities', {}).get('total', 0)}
- **Files Modified:** {summary.get('files', {}).get('total', 0)}
- **Enhancements:** {summary.get('enhancements', {}).get('count', 0)}

## Accomplishments
{_format_list(reflection_data.get('accomplishments', []))}

## Topics Covered
{_format_list(reflection_data.get('topics', []))}

## Technologies Used
{_format_list(summary.get('technologies', []))}

## Blockers
{_format_list(reflection_data.get('blockers', [])) if reflection_data.get('blockers') else '_No blockers_'}

## Insights
{reflection_data.get('insights', 'No insights generated.')}

## Next Week Focus
{_format_list(reflection_data.get('next_week_focus', []))}

---
_Auto-generated by AI Orchestrator Session Tracker_
"""

    with open(summary_file, 'w') as f:
        f.write(content)

    print(f"📝 Session summary saved: {summary_file}")
    print()

    # End session
    tracker.end_session()

    print("✨ Session captured successfully!")
    print(f"   Reflection ID: {reflection_id}")
    print(f"   Summary: {summary_file}")


def _format_list(items):
    """Format list as markdown."""
    if not items:
        return "_None_"
    return "\n".join(f"- {item}" for item in items)


def main():
    parser = argparse.ArgumentParser(description="Auto-capture session on completion")
    parser.add_argument(
        "--enhancement-id",
        help="Enhancement ID worked on (e.g., 012)"
    )
    parser.add_argument(
        "--title",
        help="Enhancement title"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force capture even if session is short"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Auto-Capture Session on Completion")
    print("=" * 80)
    print()

    asyncio.run(auto_capture(
        enhancement_id=args.enhancement_id,
        enhancement_title=args.title,
        force=args.force
    ))


if __name__ == "__main__":
    main()
