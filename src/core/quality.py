"""Quality checking for LLM responses."""

from src.models.schemas import QualityCheck, LLMResponse
from src.core.config import settings
import structlog

logger = structlog.get_logger()


class QualityChecker:
    """Checks quality of LLM responses."""

    def __init__(self) -> None:
        """Initialize quality checker."""
        self.logger = logger.bind(component="quality_checker")
        self.min_length = settings.quality_check_min_length
        self.confidence_threshold = settings.quality_check_confidence_threshold

    def check(self, response: LLMResponse) -> QualityCheck:
        """Check quality of an LLM response.

        Args:
            response: LLM response to check

        Returns:
            QualityCheck result
        """
        issues: list[str] = []
        score = 1.0

        # Check minimum length
        if len(response.content.strip()) < self.min_length:
            issues.append(f"Response too short (< {self.min_length} chars)")
            score -= 0.3

        # Check for common failure patterns
        failure_patterns = [
            ("error", 0.2),
            ("i apologize", 0.1),
            ("i cannot", 0.2),
            ("i'm unable", 0.2),
            ("i don't have access", 0.15),
        ]

        content_lower = response.content.lower()
        for pattern, penalty in failure_patterns:
            if pattern in content_lower:
                issues.append(f"Contains failure pattern: '{pattern}'")
                score -= penalty

        # Check for empty or placeholder content
        if not response.content.strip() or response.content.strip() in ["", "None", "N/A"]:
            issues.append("Empty or placeholder response")
            score = 0.0

        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))

        passed = score >= self.confidence_threshold and len(issues) == 0

        self.logger.info(
            "quality_check_performed",
            score=score,
            passed=passed,
            issues_count=len(issues),
        )

        return QualityCheck(
            passed=passed,
            score=score,
            issues=issues,
            metadata={
                "provider": response.provider.value,
                "content_length": len(response.content),
                "execution_time": response.execution_time,
            },
        )
