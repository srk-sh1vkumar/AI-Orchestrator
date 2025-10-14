"""
Telemetry Logger - Structured JSON Logging

Provides structured logging capabilities for agent execution,
token usage, and system events in JSON format for easy parsing
and integration with log aggregation systems.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


class TelemetryLogger:
    """
    Telemetry logger for orchestrator events.

    Logs all significant events in structured JSON format
    to files and optionally to external systems.
    """

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize telemetry logger.

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.log_file = self.log_dir / "orchestrator.log"
        self.agent_log_file = self.log_dir / "agents.log"
        self.error_log_file = self.log_dir / "errors.log"

        # Set up file handlers
        self._setup_file_logging()

    def _setup_file_logging(self) -> None:
        """Configure file-based logging handlers."""
        # Main orchestrator log
        main_handler = logging.FileHandler(self.log_file)
        main_handler.setLevel(logging.INFO)

        # Agent-specific log
        agent_handler = logging.FileHandler(self.agent_log_file)
        agent_handler.setLevel(logging.INFO)

        # Error log
        error_handler = logging.FileHandler(self.error_log_file)
        error_handler.setLevel(logging.ERROR)

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[main_handler, error_handler],
            format='%(message)s'  # We'll use JSON format
        )

    def log_agent_execution(
        self,
        agent: str,
        phase: str,
        tokens_used: int,
        status: str = "success",
        model: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log agent execution event.

        Args:
            agent: Agent name (e.g., 'Claude Code', 'ChatGPT')
            phase: Phase name (e.g., 'Code Generated')
            tokens_used: Number of tokens consumed
            status: Execution status ('success', 'failed', 'warning')
            model: Model identifier
            metadata: Additional metadata
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "agent_execution",
            "agent": agent,
            "phase": phase,
            "tokens_used": tokens_used,
            "model": model,
            "status": status
        }

        if metadata:
            log_entry["metadata"] = metadata

        # Write to file
        self._write_json_log(self.agent_log_file, log_entry)

        # Also log with structlog
        logger.info(
            "agent_execution",
            agent=agent,
            phase=phase,
            tokens=tokens_used,
            status=status
        )

    def log_phase_transition(
        self,
        from_phase: str,
        to_phase: str,
        duration_seconds: float
    ) -> None:
        """
        Log phase transition event.

        Args:
            from_phase: Previous phase
            to_phase: Next phase
            duration_seconds: Duration of previous phase
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "phase_transition",
            "from_phase": from_phase,
            "to_phase": to_phase,
            "duration_seconds": round(duration_seconds, 3)
        }

        self._write_json_log(self.log_file, log_entry)

        logger.info(
            "phase_transition",
            from_phase=from_phase,
            to_phase=to_phase,
            duration=duration_seconds
        )

    def log_cost_calculation(
        self,
        total_cost: float,
        breakdown: Dict[str, Any]
    ) -> None:
        """
        Log cost calculation event.

        Args:
            total_cost: Total estimated cost in USD
            breakdown: Cost breakdown by agent/model
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "cost_calculation",
            "total_cost_usd": total_cost,
            "breakdown": breakdown
        }

        self._write_json_log(self.log_file, log_entry)

        logger.info(
            "cost_calculation",
            total_cost=total_cost,
            agents=len(breakdown)
        )

    def log_self_dev_update(
        self,
        learning_hours: float,
        goals_updated: int,
        reflection: Optional[str] = None
    ) -> None:
        """
        Log self-development tracking update.

        Args:
            learning_hours: Hours added
            goals_updated: Number of goals updated
            reflection: AI-generated reflection text
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "self_development_update",
            "learning_hours_added": learning_hours,
            "goals_updated": goals_updated
        }

        if reflection:
            log_entry["reflection"] = reflection[:200]  # Truncate for log

        self._write_json_log(self.log_file, log_entry)

        logger.info(
            "self_dev_update",
            hours=learning_hours,
            goals=goals_updated
        )

    def log_error(
        self,
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log error event.

        Args:
            error_type: Type/category of error
            message: Error message
            context: Additional context
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "error",
            "error_type": error_type,
            "message": message
        }

        if context:
            log_entry["context"] = context

        self._write_json_log(self.error_log_file, log_entry)

        logger.error(
            "error_logged",
            error_type=error_type,
            message=message
        )

    def _write_json_log(self, log_file: Path, entry: Dict[str, Any]) -> None:
        """
        Write JSON log entry to file.

        Args:
            log_file: Path to log file
            entry: Log entry dictionary
        """
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def get_recent_logs(
        self,
        log_type: str = "orchestrator",
        limit: int = 50
    ) -> list:
        """
        Retrieve recent log entries.

        Args:
            log_type: Type of log ('orchestrator', 'agents', 'errors')
            limit: Maximum number of entries to return

        Returns:
            List of log entries
        """
        log_file_map = {
            "orchestrator": self.log_file,
            "agents": self.agent_log_file,
            "errors": self.error_log_file
        }

        log_file = log_file_map.get(log_type, self.log_file)

        if not log_file.exists():
            return []

        logs = []
        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Get last N lines
        for line in lines[-limit:]:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

        return logs

    def clear_logs(self) -> None:
        """Clear all log files."""
        for log_file in [self.log_file, self.agent_log_file, self.error_log_file]:
            if log_file.exists():
                log_file.unlink()

        logger.info("logs_cleared")


# Global telemetry logger instance
_telemetry_logger: Optional[TelemetryLogger] = None


def get_telemetry_logger() -> TelemetryLogger:
    """Get or create global telemetry logger instance."""
    global _telemetry_logger
    if _telemetry_logger is None:
        _telemetry_logger = TelemetryLogger()
    return _telemetry_logger


def log_agent(agent: str, phase: str, tokens: int, **kwargs) -> None:
    """Convenience function for logging agent execution."""
    get_telemetry_logger().log_agent_execution(agent, phase, tokens, **kwargs)


def log_phase(from_phase: str, to_phase: str, duration: float) -> None:
    """Convenience function for logging phase transitions."""
    get_telemetry_logger().log_phase_transition(from_phase, to_phase, duration)


def log_costs(total: float, breakdown: Dict[str, Any]) -> None:
    """Convenience function for logging costs."""
    get_telemetry_logger().log_cost_calculation(total, breakdown)


if __name__ == "__main__":
    # Test telemetry logger
    print("Testing Telemetry Logger\n")

    tel = TelemetryLogger()

    # Log some sample events
    print("Logging sample agent executions...")
    tel.log_agent_execution(
        agent="Claude Code",
        phase="Code Generated",
        tokens_used=1780,
        status="success",
        model="claude-3-sonnet-20240229"
    )

    tel.log_agent_execution(
        agent="ChatGPT",
        phase="Dashboard Created",
        tokens_used=1200,
        status="success",
        model="gpt-4-turbo-preview"
    )

    tel.log_phase_transition(
        from_phase="Design",
        to_phase="Implementation",
        duration_seconds=45.3
    )

    tel.log_cost_calculation(
        total_cost=0.0523,
        breakdown={
            "claude": {"cost": 0.0312},
            "chatgpt": {"cost": 0.0211}
        }
    )

    tel.log_self_dev_update(
        learning_hours=2.5,
        goals_updated=1,
        reflection="Made progress on FinTech domain expertise"
    )

    print(f"\n✅ Logs written to {tel.log_dir}/")
    print(f"  - orchestrator.log")
    print(f"  - agents.log")
    print(f"  - errors.log")

    # Retrieve recent logs
    print("\n📋 Recent agent logs:")
    recent = tel.get_recent_logs("agents", limit=5)
    for log in recent:
        print(f"  [{log['timestamp']}] {log['agent']}: {log['phase']} ({log['tokens_used']} tokens)")
