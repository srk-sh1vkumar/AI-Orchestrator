"""Quality Checker - Automated Response Quality Validation

Enhancement 021: Enhance Current FREE Providers
Validates LLM responses for quality issues and triggers retries with different providers.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from src.models.schemas import LLMResponse, LLMProvider

logger = structlog.get_logger(__name__)


class QualityIssue(str, Enum):
    """Types of quality issues."""
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    INCOHERENT = "incoherent"
    IRRELEVANT = "irrelevant"
    INCOMPLETE = "incomplete"
    ERROR_MESSAGE = "error_message"
    LOW_CONFIDENCE = "low_confidence"
    FORMATTING_ISSUES = "formatting_issues"


@dataclass
class QualityReport:
    """Quality check report."""
    passed: bool
    score: float  # 0.0 - 1.0
    issues: List[QualityIssue]
    details: Dict[str, Any]
    should_retry: bool
    retry_reason: Optional[str] = None


class QualityChecker:
    """Automated quality validation for LLM responses."""

    def __init__(
        self,
        min_length: int = 10,
        max_length: int = 50000,
        min_quality_score: float = 0.6,
    ):
        """Initialize quality checker.

        Args:
            min_length: Minimum response length (characters)
            max_length: Maximum response length (characters)
            min_quality_score: Minimum quality score to pass (0.0-1.0)
        """
        self.min_length = min_length
        self.max_length = max_length
        self.min_quality_score = min_quality_score
        self.logger = logger.bind(component="quality_checker")

        # Error indicators
        self.error_patterns = [
            "error:",
            "exception:",
            "failed to",
            "cannot",
            "unable to",
            "i don't have",
            "i cannot",
            "i'm unable",
            "i apologize, but i",
            "sorry, i can't",
        ]

        # Incompleteness indicators
        self.incomplete_patterns = [
            "...",
            "[truncated]",
            "[continue]",
            "to be continued",
            "part 1 of",
        ]

    def check(
        self,
        response: LLMResponse,
        user_query: str,
        expected_type: Optional[str] = None,
    ) -> QualityReport:
        """Check response quality.

        Args:
            response: LLM response to validate
            user_query: Original user query
            expected_type: Expected response type (e.g., "code", "explanation")

        Returns:
            QualityReport with pass/fail and details
        """
        issues: List[QualityIssue] = []
        details: Dict[str, Any] = {}
        scores: Dict[str, float] = {}

        # Check 1: Length validation
        length_score = self._check_length(response.content, issues, details)
        scores["length"] = length_score

        # Check 2: Coherence (basic heuristics)
        coherence_score = self._check_coherence(response.content, issues, details)
        scores["coherence"] = coherence_score

        # Check 3: Relevance to query
        relevance_score = self._check_relevance(
            response.content, user_query, issues, details
        )
        scores["relevance"] = relevance_score

        # Check 4: Completeness
        completeness_score = self._check_completeness(
            response.content, issues, details
        )
        scores["completeness"] = completeness_score

        # Check 5: Error indicators
        error_score = self._check_for_errors(response.content, issues, details)
        scores["error_free"] = error_score

        # Check 6: Formatting (for code)
        if expected_type == "code":
            formatting_score = self._check_code_formatting(
                response.content, issues, details
            )
            scores["formatting"] = formatting_score

        # Calculate overall quality score (weighted average)
        weights = {
            "length": 0.15,
            "coherence": 0.25,
            "relevance": 0.30,
            "completeness": 0.20,
            "error_free": 0.10,
        }

        if expected_type == "code":
            weights["formatting"] = 0.15
            # Rebalance other weights
            for key in weights:
                if key != "formatting":
                    weights[key] *= 0.85

        overall_score = sum(scores[k] * weights.get(k, 0) for k in scores)

        # Determine pass/fail
        passed = overall_score >= self.min_quality_score and not any(
            issue in [QualityIssue.ERROR_MESSAGE, QualityIssue.INCOMPLETE]
            for issue in issues
        )

        # Determine if retry should be attempted
        should_retry = not passed and overall_score < 0.8

        retry_reason = None
        if should_retry:
            if QualityIssue.ERROR_MESSAGE in issues:
                retry_reason = "Response contains error message"
            elif QualityIssue.INCOMPLETE in issues:
                retry_reason = "Response appears incomplete"
            elif QualityIssue.TOO_SHORT in issues:
                retry_reason = "Response too short"
            elif QualityIssue.IRRELEVANT in issues:
                retry_reason = "Response not relevant to query"
            elif overall_score < self.min_quality_score:
                retry_reason = f"Quality score too low: {overall_score:.2f}"

        self.logger.info(
            "quality_check_complete",
            provider=response.provider.value,
            passed=passed,
            score=f"{overall_score:.3f}",
            issues=len(issues),
            should_retry=should_retry,
        )

        return QualityReport(
            passed=passed,
            score=overall_score,
            issues=issues,
            details={**details, "scores": scores},
            should_retry=should_retry,
            retry_reason=retry_reason,
        )

    def _check_length(
        self, content: str, issues: List[QualityIssue], details: Dict[str, Any]
    ) -> float:
        """Check response length."""
        length = len(content)
        details["length"] = length

        if length < self.min_length:
            issues.append(QualityIssue.TOO_SHORT)
            return 0.0
        elif length > self.max_length:
            issues.append(QualityIssue.TOO_LONG)
            return 0.7  # Not fatal, but penalized

        # Score based on reasonable length (100-5000 is optimal)
        if 100 <= length <= 5000:
            return 1.0
        elif length < 100:
            return length / 100
        else:
            # Gradual penalty for very long responses
            return max(0.7, 1.0 - (length - 5000) / 50000)

    def _check_coherence(
        self, content: str, issues: List[QualityIssue], details: Dict[str, Any]
    ) -> float:
        """Check basic coherence using heuristics."""
        # Simple heuristics for coherence
        score = 1.0

        # Check for excessive repetition
        words = content.lower().split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            details["unique_word_ratio"] = unique_ratio

            if unique_ratio < 0.3:
                # Too repetitive
                issues.append(QualityIssue.INCOHERENT)
                score *= 0.5

        # Check sentence structure (basic)
        sentences = content.split(". ")
        if len(sentences) > 0:
            avg_sentence_length = len(content) / len(sentences)
            details["avg_sentence_length"] = avg_sentence_length

            if avg_sentence_length < 5:
                # Very short sentences might indicate issues
                score *= 0.8
            elif avg_sentence_length > 500:
                # Very long "sentences" likely indicate poor structure
                score *= 0.7

        # Check for complete gibberish (high ratio of non-words)
        alphanumeric_ratio = sum(c.isalnum() or c.isspace() for c in content) / len(
            content
        )
        details["alphanumeric_ratio"] = alphanumeric_ratio

        if alphanumeric_ratio < 0.5:
            issues.append(QualityIssue.INCOHERENT)
            score *= 0.3

        return max(0.0, min(1.0, score))

    def _check_relevance(
        self,
        content: str,
        user_query: str,
        issues: List[QualityIssue],
        details: Dict[str, Any],
    ) -> float:
        """Check if response is relevant to user query."""
        # Simple keyword overlap check
        query_keywords = set(user_query.lower().split())
        response_words = set(content.lower().split())

        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "and",
            "or",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
        }
        query_keywords -= stop_words
        response_words -= stop_words

        if not query_keywords:
            # Can't check relevance without keywords
            return 0.8

        # Calculate keyword overlap
        overlap = len(query_keywords & response_words)
        overlap_ratio = overlap / len(query_keywords) if query_keywords else 0

        details["keyword_overlap_ratio"] = overlap_ratio

        if overlap_ratio < 0.1:
            # Very low overlap might indicate irrelevant response
            issues.append(QualityIssue.IRRELEVANT)
            return 0.3
        elif overlap_ratio < 0.3:
            return 0.6
        else:
            return min(1.0, 0.5 + overlap_ratio)

    def _check_completeness(
        self, content: str, issues: List[QualityIssue], details: Dict[str, Any]
    ) -> float:
        """Check if response appears complete."""
        content_lower = content.lower()

        # Check for incompleteness indicators
        for pattern in self.incomplete_patterns:
            if pattern in content_lower:
                issues.append(QualityIssue.INCOMPLETE)
                details["incomplete_pattern"] = pattern
                return 0.2

        # Check if response ends abruptly (no proper ending punctuation)
        if content and content[-1] not in [".", "!", "?", ")", "]", "}", "`", '"', "'"]:
            # Might be incomplete
            return 0.8

        return 1.0

    def _check_for_errors(
        self, content: str, issues: List[QualityIssue], details: Dict[str, Any]
    ) -> float:
        """Check if response contains error indicators."""
        content_lower = content.lower()

        for pattern in self.error_patterns:
            if pattern in content_lower:
                issues.append(QualityIssue.ERROR_MESSAGE)
                details["error_pattern"] = pattern
                return 0.0  # Critical failure

        return 1.0

    def _check_code_formatting(
        self, content: str, issues: List[QualityIssue], details: Dict[str, Any]
    ) -> float:
        """Check code formatting quality."""
        # Check for code blocks
        has_code_block = "```" in content
        details["has_code_block"] = has_code_block

        if not has_code_block:
            # Expected code but no code block
            issues.append(QualityIssue.FORMATTING_ISSUES)
            return 0.5

        # Check for properly closed code blocks
        code_block_count = content.count("```")
        if code_block_count % 2 != 0:
            issues.append(QualityIssue.FORMATTING_ISSUES)
            details["unclosed_code_block"] = True
            return 0.3

        # Check for language tags in code blocks
        has_language_tag = any(
            f"```{lang}" in content
            for lang in ["python", "javascript", "java", "go", "rust", "sql", "bash"]
        )
        details["has_language_tag"] = has_language_tag

        if not has_language_tag:
            return 0.8  # Minor penalty

        return 1.0


# Singleton instance
_quality_checker: Optional[QualityChecker] = None


def get_quality_checker() -> QualityChecker:
    """Get or create the global QualityChecker instance."""
    global _quality_checker
    if _quality_checker is None:
        _quality_checker = QualityChecker()
    return _quality_checker
