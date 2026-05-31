"""Pattern matching and refactoring suggestions.

Enhancement 015: Generate actionable suggestions from duplications.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import structlog

from src.analysis.code_analyzer import CodeSignature, CodeAnalyzer
from src.analysis.similarity_engine import SimilarityEngine, SimilarityMatch

logger = structlog.get_logger()


@dataclass
class RefactoringSuggestion:
    """A suggested refactoring action."""

    suggestion_id: str
    suggestion_type: str  # extract_function, create_utility, merge_classes
    title: str
    description: str
    affected_signatures: List[CodeSignature]
    estimated_lines_saved: int
    priority: str  # high, medium, low
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suggestion_id": self.suggestion_id,
            "suggestion_type": self.suggestion_type,
            "title": self.title,
            "description": self.description,
            "affected_files": [
                {
                    "name": sig.name,
                    "file": sig.file_path,
                    "project": sig.project,
                    "line": sig.line_number,
                }
                for sig in self.affected_signatures
            ],
            "estimated_lines_saved": self.estimated_lines_saved,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DuplicationReport:
    """Complete duplication analysis report."""

    total_signatures: int
    exact_duplicates: int
    similar_code: int
    suggestions: List[RefactoringSuggestion]
    matches: List[SimilarityMatch]
    projects_analyzed: List[str]
    analysis_time_seconds: float
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": {
                "total_signatures": self.total_signatures,
                "exact_duplicates": self.exact_duplicates,
                "similar_code": self.similar_code,
                "projects_analyzed": self.projects_analyzed,
                "analysis_time_seconds": self.analysis_time_seconds,
            },
            "suggestions": [s.to_dict() for s in self.suggestions],
            "matches": [m.to_dict() for m in self.matches[:50]],  # Limit matches
            "created_at": self.created_at.isoformat(),
        }


class PatternMatcher:
    """Matches patterns and generates refactoring suggestions."""

    def __init__(self) -> None:
        """Initialize pattern matcher."""
        self.logger = logger.bind(component="pattern_matcher")
        self.analyzer = CodeAnalyzer()
        self.similarity_engine = SimilarityEngine()

    def analyze_projects(
        self,
        projects: Dict[str, Path],
        similarity_threshold: float = 0.8,
    ) -> DuplicationReport:
        """Analyze multiple projects for duplications.

        Args:
            projects: Dict of project_name -> project_path
            similarity_threshold: Minimum similarity for matches

        Returns:
            Complete duplication report
        """
        import time
        start_time = time.time()

        self.logger.info("starting_analysis", projects=list(projects.keys()))

        # Analyze all projects
        all_signatures = self.analyzer.analyze_multiple_projects(projects)

        # Build similarity index
        self.similarity_engine.build_index(all_signatures)

        # Find exact duplicates
        exact_matches = self.similarity_engine.find_exact_duplicates()

        # Find similar code
        similar_matches = self.similarity_engine.find_all_duplicates(
            threshold=similarity_threshold,
            cross_project_only=True,
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(exact_matches, similar_matches)

        analysis_time = time.time() - start_time

        report = DuplicationReport(
            total_signatures=len(all_signatures),
            exact_duplicates=len(exact_matches),
            similar_code=len(similar_matches),
            suggestions=suggestions,
            matches=exact_matches + similar_matches,
            projects_analyzed=list(projects.keys()),
            analysis_time_seconds=analysis_time,
        )

        self.logger.info(
            "analysis_complete",
            signatures=len(all_signatures),
            exact=len(exact_matches),
            similar=len(similar_matches),
            suggestions=len(suggestions),
            time_seconds=f"{analysis_time:.2f}",
        )

        return report

    def _generate_suggestions(
        self,
        exact_matches: List[SimilarityMatch],
        similar_matches: List[SimilarityMatch],
    ) -> List[RefactoringSuggestion]:
        """Generate refactoring suggestions from matches."""
        suggestions: List[RefactoringSuggestion] = []
        suggestion_counter = 0

        # Group exact matches by function name pattern
        exact_groups: Dict[str, List[SimilarityMatch]] = {}
        for match in exact_matches:
            key = match.signature_a.name.split(".")[-1]  # Base function name
            if key not in exact_groups:
                exact_groups[key] = []
            exact_groups[key].append(match)

        # Generate suggestions for exact duplicates
        for name, matches in exact_groups.items():
            if len(matches) >= 1:
                suggestion_counter += 1
                affected = []
                for match in matches:
                    if match.signature_a not in affected:
                        affected.append(match.signature_a)
                    if match.signature_b not in affected:
                        affected.append(match.signature_b)

                # Estimate lines saved
                avg_complexity = sum(s.complexity for s in affected) / len(affected)
                lines_saved = int(avg_complexity * 10 * (len(affected) - 1))

                suggestions.append(RefactoringSuggestion(
                    suggestion_id=f"SUG-{suggestion_counter:03d}",
                    suggestion_type="extract_to_shared",
                    title=f"Extract '{name}' to shared utility",
                    description=f"Function '{name}' is duplicated {len(affected)} times across projects. "
                               f"Consider extracting to a shared library.",
                    affected_signatures=affected,
                    estimated_lines_saved=lines_saved,
                    priority="high" if len(affected) > 2 else "medium",
                ))

        # Generate suggestions for similar code
        similar_groups: Dict[str, List[SimilarityMatch]] = {}
        for match in similar_matches:
            if match.match_type in ["high", "medium"]:
                key = match.signature_a.name.split(".")[-1]
                if key not in similar_groups:
                    similar_groups[key] = []
                similar_groups[key].append(match)

        for name, matches in similar_groups.items():
            if len(matches) >= 1:
                # Only suggest if not already exact match
                if name in exact_groups:
                    continue

                suggestion_counter += 1
                affected = []
                for match in matches:
                    if match.signature_a not in affected:
                        affected.append(match.signature_a)
                    if match.signature_b not in affected:
                        affected.append(match.signature_b)

                avg_similarity = sum(m.similarity_score for m in matches) / len(matches)

                suggestions.append(RefactoringSuggestion(
                    suggestion_id=f"SUG-{suggestion_counter:03d}",
                    suggestion_type="consolidate_similar",
                    title=f"Consolidate similar '{name}' implementations",
                    description=f"Found {len(affected)} similar implementations of '{name}' "
                               f"with {avg_similarity:.0%} average similarity. "
                               f"Consider creating a parameterized shared function.",
                    affected_signatures=affected,
                    estimated_lines_saved=int(len(affected) * 15),
                    priority="medium" if avg_similarity > 0.9 else "low",
                ))

        # Sort by priority and lines saved
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: (priority_order[s.priority], -s.estimated_lines_saved))

        return suggestions

    def get_project_summary(self, report: DuplicationReport) -> Dict[str, Any]:
        """Get summary statistics per project."""
        project_stats: Dict[str, Dict[str, int]] = {}

        for match in report.matches:
            for sig in [match.signature_a, match.signature_b]:
                if sig.project not in project_stats:
                    project_stats[sig.project] = {
                        "duplicates": 0,
                        "affected_files": set(),
                    }
                project_stats[sig.project]["duplicates"] += 1
                project_stats[sig.project]["affected_files"].add(sig.file_path)

        # Convert sets to counts
        return {
            project: {
                "duplicates": stats["duplicates"],
                "affected_files": len(stats["affected_files"]),
            }
            for project, stats in project_stats.items()
        }
