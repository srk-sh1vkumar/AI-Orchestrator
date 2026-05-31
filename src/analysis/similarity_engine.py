"""Similarity engine for code duplication detection.

Enhancement 015: ML-based similarity matching using embeddings.
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import structlog

from src.analysis.code_analyzer import CodeSignature

logger = structlog.get_logger()


@dataclass
class SimilarityMatch:
    """A match between two code signatures."""

    signature_a: CodeSignature
    signature_b: CodeSignature
    similarity_score: float
    match_type: str  # exact, high, medium, low
    matched_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signature_a": {
                "name": self.signature_a.name,
                "file": self.signature_a.file_path,
                "project": self.signature_a.project,
                "line": self.signature_a.line_number,
            },
            "signature_b": {
                "name": self.signature_b.name,
                "file": self.signature_b.file_path,
                "project": self.signature_b.project,
                "line": self.signature_b.line_number,
            },
            "similarity_score": self.similarity_score,
            "match_type": self.match_type,
            "matched_at": self.matched_at.isoformat(),
        }


class SimilarityEngine:
    """Finds similar code signatures using embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize similarity engine.

        Args:
            model_name: Sentence transformer model to use
        """
        self.logger = logger.bind(component="similarity_engine")
        self.model_name = model_name

        self.logger.info("loading_embedding_model", model=model_name)
        self.model = SentenceTransformer(model_name)
        self.logger.info("embedding_model_loaded")

        self._embeddings: Dict[str, np.ndarray] = {}
        self._signatures: List[CodeSignature] = []

    def build_index(self, signatures: List[CodeSignature]) -> None:
        """Build embedding index for signatures.

        Args:
            signatures: List of code signatures to index
        """
        self._signatures = signatures

        # Create text representations for embedding
        texts = []
        for sig in signatures:
            text = self._signature_to_text(sig)
            texts.append(text)

        # Generate embeddings
        self.logger.info("generating_embeddings", count=len(texts))
        embeddings = self.model.encode(texts, show_progress_bar=False)

        # Store embeddings with signature index
        for i, sig in enumerate(signatures):
            key = f"{sig.project}:{sig.file_path}:{sig.name}:{sig.line_number}"
            self._embeddings[key] = embeddings[i]

        self.logger.info("index_built", signatures=len(signatures))

    def find_similar(
        self,
        signature: CodeSignature,
        threshold: float = 0.7,
        top_k: int = 10,
        cross_project_only: bool = False,
    ) -> List[SimilarityMatch]:
        """Find similar signatures for a given signature.

        Args:
            signature: Signature to find matches for
            threshold: Minimum similarity threshold (0-1)
            top_k: Maximum number of matches to return
            cross_project_only: Only return matches from different projects

        Returns:
            List of similarity matches
        """
        # Get embedding for query signature
        query_text = self._signature_to_text(signature)
        query_embedding = self.model.encode([query_text])[0]

        matches: List[SimilarityMatch] = []

        # Compare with all indexed signatures
        for i, sig in enumerate(self._signatures):
            # Skip self
            if (sig.file_path == signature.file_path and
                sig.name == signature.name and
                sig.line_number == signature.line_number):
                continue

            # Skip same project if cross_project_only
            if cross_project_only and sig.project == signature.project:
                continue

            # Get embedding
            key = f"{sig.project}:{sig.file_path}:{sig.name}:{sig.line_number}"
            if key not in self._embeddings:
                continue

            sig_embedding = self._embeddings[key]

            # Calculate similarity
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                sig_embedding.reshape(1, -1)
            )[0][0]

            if similarity >= threshold:
                match_type = self._classify_match(similarity, signature, sig)
                matches.append(SimilarityMatch(
                    signature_a=signature,
                    signature_b=sig,
                    similarity_score=float(similarity),
                    match_type=match_type,
                ))

        # Sort by similarity and limit
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return matches[:top_k]

    def find_all_duplicates(
        self,
        threshold: float = 0.8,
        cross_project_only: bool = True,
    ) -> List[SimilarityMatch]:
        """Find all duplicate code across signatures.

        Args:
            threshold: Minimum similarity threshold
            cross_project_only: Only match across different projects

        Returns:
            List of all similarity matches
        """
        all_matches: List[SimilarityMatch] = []
        seen_pairs: set = set()

        self.logger.info(
            "finding_duplicates",
            signatures=len(self._signatures),
            threshold=threshold,
        )

        for sig in self._signatures:
            matches = self.find_similar(
                sig,
                threshold=threshold,
                cross_project_only=cross_project_only,
            )

            for match in matches:
                # Create canonical pair key to avoid duplicates
                pair_key = tuple(sorted([
                    f"{match.signature_a.project}:{match.signature_a.name}",
                    f"{match.signature_b.project}:{match.signature_b.name}",
                ]))

                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    all_matches.append(match)

        # Sort by similarity
        all_matches.sort(key=lambda m: m.similarity_score, reverse=True)

        self.logger.info("duplicates_found", count=len(all_matches))

        return all_matches

    def find_exact_duplicates(self) -> List[SimilarityMatch]:
        """Find exact code duplicates by body hash.

        Returns:
            List of exact matches
        """
        # Group by body hash
        hash_groups: Dict[str, List[CodeSignature]] = {}

        for sig in self._signatures:
            if sig.body_hash not in hash_groups:
                hash_groups[sig.body_hash] = []
            hash_groups[sig.body_hash].append(sig)

        # Find groups with multiple signatures
        exact_matches: List[SimilarityMatch] = []

        for body_hash, sigs in hash_groups.items():
            if len(sigs) > 1:
                # Create matches for all pairs
                for i in range(len(sigs)):
                    for j in range(i + 1, len(sigs)):
                        # Skip same file
                        if sigs[i].file_path == sigs[j].file_path:
                            continue

                        exact_matches.append(SimilarityMatch(
                            signature_a=sigs[i],
                            signature_b=sigs[j],
                            similarity_score=1.0,
                            match_type="exact",
                        ))

        self.logger.info("exact_duplicates_found", count=len(exact_matches))

        return exact_matches

    def _signature_to_text(self, sig: CodeSignature) -> str:
        """Convert signature to text for embedding."""
        parts = [
            f"{sig.signature_type} {sig.name}",
            f"parameters: {', '.join(sig.parameters)}",
        ]

        if sig.return_type:
            parts.append(f"returns: {sig.return_type}")

        if sig.docstring:
            # Use first 200 chars of docstring
            parts.append(f"description: {sig.docstring[:200]}")

        if sig.decorators:
            parts.append(f"decorators: {', '.join(sig.decorators)}")

        return " | ".join(parts)

    def _classify_match(
        self,
        similarity: float,
        sig_a: CodeSignature,
        sig_b: CodeSignature,
    ) -> str:
        """Classify match type based on similarity and features."""

        # Exact match by hash
        if sig_a.body_hash == sig_b.body_hash:
            return "exact"

        # High similarity
        if similarity >= 0.95:
            return "high"

        # Medium similarity
        if similarity >= 0.85:
            return "medium"

        return "low"
