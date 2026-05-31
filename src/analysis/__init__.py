"""Cross-project analysis and duplication detection.

Enhancement 015: AI-powered code analysis system.
"""

from src.analysis.code_analyzer import CodeAnalyzer, CodeSignature
from src.analysis.similarity_engine import SimilarityEngine, SimilarityMatch
from src.analysis.pattern_matcher import PatternMatcher, DuplicationReport

__all__ = [
    "CodeAnalyzer",
    "CodeSignature",
    "SimilarityEngine",
    "SimilarityMatch",
    "PatternMatcher",
    "DuplicationReport",
]
