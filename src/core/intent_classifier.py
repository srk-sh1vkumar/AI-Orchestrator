"""ML-based intent classification for intelligent routing."""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import structlog
from src.models.schemas import LLMProvider, TaskCategory

logger = structlog.get_logger()


@dataclass
class IntentExample:
    """Training example for intent classification."""

    text: str
    provider: LLMProvider
    category: TaskCategory
    confidence: float = 1.0


class IntentClassifier:
    """ML-based intent classifier using sentence embeddings."""

    # Pre-defined training examples for each provider
    TRAINING_EXAMPLES = {
        LLMProvider.CLAUDE_CODE: [
            IntentExample(
                "Build a REST API for user authentication with JWT tokens",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.CODE_GENERATION,
            ),
            IntentExample(
                "Implement a Docker deployment pipeline with GitHub Actions",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.DEPLOYMENT,
            ),
            IntentExample(
                "Debug the memory leak in the Python service",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.DEBUGGING,
            ),
            IntentExample(
                "Create unit tests for the authentication module",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.CODE_GENERATION,
            ),
            IntentExample(
                "Refactor the database connection pooling code",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.CODE_IMPLEMENTATION,
            ),
            IntentExample(
                "Set up Kubernetes deployment manifests for microservices",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.DEPLOYMENT,
            ),
            IntentExample(
                "Fix the race condition in concurrent file writes",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.DEBUGGING,
            ),
            IntentExample(
                "Write a bash script to automate database backups",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.CODE_GENERATION,
            ),
            IntentExample(
                "Implement circuit breaker pattern for external API calls",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.CODE_IMPLEMENTATION,
            ),
            IntentExample(
                "Create a CI/CD pipeline with automated testing and deployment",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.DEPLOYMENT,
            ),
            IntentExample(
                "Write a Python function to sort a list of numbers",
                LLMProvider.CLAUDE_CODE,
                TaskCategory.CODE_GENERATION,
            ),
        ],
        LLMProvider.CHATGPT: [
            IntentExample(
                "Design a modern dashboard UI with charts and graphs",
                LLMProvider.CHATGPT,
                TaskCategory.UI_GENERATION,
            ),
            IntentExample(
                "Create a user-friendly onboarding wizard interface",
                LLMProvider.CHATGPT,
                TaskCategory.UI_GENERATION,
            ),
            IntentExample(
                "Build a responsive navigation menu with dropdown items",
                LLMProvider.CHATGPT,
                TaskCategory.UI_GENERATION,
            ),
            IntentExample(
                "Generate a workflow automation for customer support tickets",
                LLMProvider.CHATGPT,
                TaskCategory.WORKFLOW_AUTOMATION,
            ),
            IntentExample(
                "Design a mobile-first landing page with animations",
                LLMProvider.CHATGPT,
                TaskCategory.UI_GENERATION,
            ),
            IntentExample(
                "Create an admin panel with user management features",
                LLMProvider.CHATGPT,
                TaskCategory.UI_GENERATION,
            ),
            IntentExample(
                "Build a drag-and-drop form builder interface",
                LLMProvider.CHATGPT,
                TaskCategory.UI_GENERATION,
            ),
            IntentExample(
                "Automate the monthly reporting workflow with email notifications",
                LLMProvider.CHATGPT,
                TaskCategory.WORKFLOW_AUTOMATION,
            ),
            IntentExample(
                "Design a data visualization dashboard with interactive filters",
                LLMProvider.CHATGPT,
                TaskCategory.UI_GENERATION,
            ),
            IntentExample(
                "Create a customer feedback collection and analysis workflow",
                LLMProvider.CHATGPT,
                TaskCategory.WORKFLOW_AUTOMATION,
            ),
        ],
        LLMProvider.GEMINI: [
            IntentExample(
                "Optimize this prompt to get better results from the LLM",
                LLMProvider.GEMINI,
                TaskCategory.PROMPT_OPTIMIZATION,
            ),
            IntentExample(
                "Improve the instruction clarity for code generation tasks",
                LLMProvider.GEMINI,
                TaskCategory.PROMPT_OPTIMIZATION,
            ),
            IntentExample(
                "Refine this prompt template for better consistency",
                LLMProvider.GEMINI,
                TaskCategory.PROMPT_OPTIMIZATION,
            ),
            IntentExample(
                "Create a meta-prompt for generating system prompts",
                LLMProvider.GEMINI,
                TaskCategory.PROMPT_OPTIMIZATION,
            ),
            IntentExample(
                "Enhance the prompt engineering approach for this use case",
                LLMProvider.GEMINI,
                TaskCategory.PROMPT_OPTIMIZATION,
            ),
            IntentExample(
                "Design a prompt framework for multi-step reasoning tasks",
                LLMProvider.GEMINI,
                TaskCategory.PROMPT_OPTIMIZATION,
            ),
            IntentExample(
                "Optimize the system message for better agent behavior",
                LLMProvider.GEMINI,
                TaskCategory.PROMPT_OPTIMIZATION,
            ),
            IntentExample(
                "Improve few-shot examples in the instruction template",
                LLMProvider.GEMINI,
                TaskCategory.PROMPT_OPTIMIZATION,
            ),
        ],
        LLMProvider.LOCAL: [
            IntentExample(
                "Analyze this production incident and identify root cause",
                LLMProvider.LOCAL,
                TaskCategory.INCIDENT_ANALYSIS,
            ),
            IntentExample(
                "Investigate the service outage from last night's logs",
                LLMProvider.LOCAL,
                TaskCategory.LOG_ANALYSIS,
            ),
            IntentExample(
                "Examine these error logs to find the failure pattern",
                LLMProvider.LOCAL,
                TaskCategory.LOG_ANALYSIS,
            ),
            IntentExample(
                "Triage this security incident and assess the impact",
                LLMProvider.LOCAL,
                TaskCategory.INCIDENT_ANALYSIS,
            ),
            IntentExample(
                "Parse the application logs for performance degradation signals",
                LLMProvider.LOCAL,
                TaskCategory.LOG_ANALYSIS,
            ),
            IntentExample(
                "Create a postmortem analysis for the database failure",
                LLMProvider.LOCAL,
                TaskCategory.INCIDENT_ANALYSIS,
            ),
            IntentExample(
                "Analyze why the system experienced high latency",
                LLMProvider.LOCAL,
                TaskCategory.INCIDENT_ANALYSIS,
            ),
            IntentExample(
                "Review these access logs for suspicious activity",
                LLMProvider.LOCAL,
                TaskCategory.LOG_ANALYSIS,
            ),
            IntentExample(
                "Investigate the memory leak causing OOM errors",
                LLMProvider.LOCAL,
                TaskCategory.INCIDENT_ANALYSIS,
            ),
            IntentExample(
                "Examine the monitoring data for anomalies before the crash",
                LLMProvider.LOCAL,
                TaskCategory.TECHNICAL_ANALYSIS,
            ),
        ],
        LLMProvider.CLAUDE: [
            IntentExample(
                "Explain the architecture of this microservices system",
                LLMProvider.CLAUDE,
                TaskCategory.DOCUMENTATION,
            ),
            IntentExample(
                "Write comprehensive documentation for this API",
                LLMProvider.CLAUDE,
                TaskCategory.DOCUMENTATION,
            ),
            IntentExample(
                "Analyze the code quality and suggest improvements",
                LLMProvider.CLAUDE,
                TaskCategory.TECHNICAL_ANALYSIS,
            ),
            IntentExample(
                "Review the system design for scalability issues",
                LLMProvider.CLAUDE,
                TaskCategory.TECHNICAL_ANALYSIS,
            ),
            IntentExample(
                "Create a detailed technical specification document",
                LLMProvider.CLAUDE,
                TaskCategory.DOCUMENTATION,
            ),
            IntentExample(
                "Evaluate the security posture of this application",
                LLMProvider.CLAUDE,
                TaskCategory.TECHNICAL_ANALYSIS,
            ),
        ],
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the intent classifier.

        Args:
            model_name: Name of the sentence transformer model to use
                       Default: all-MiniLM-L6-v2 (fast, 384 dimensions)
                       Alternative: all-mpnet-base-v2 (better quality, 768 dimensions)
        """
        self.logger = logger.bind(component="intent_classifier")
        self.model_name = model_name

        try:
            self.logger.info("loading_embedding_model", model=model_name)
            self.model = SentenceTransformer(model_name)
            self.logger.info("embedding_model_loaded", model=model_name)
        except Exception as e:
            self.logger.error("embedding_model_load_failed", model=model_name, error=str(e))
            raise

        # Build training corpus
        self._build_training_corpus()

    def _build_training_corpus(self) -> None:
        """Build and encode the training corpus."""
        self.logger.info("building_training_corpus")

        # Collect all training examples
        self.examples: List[IntentExample] = []
        for provider_examples in self.TRAINING_EXAMPLES.values():
            self.examples.extend(provider_examples)

        # Extract texts for encoding
        texts = [example.text for example in self.examples]

        # Encode all examples
        self.logger.info("encoding_examples", count=len(texts))
        self.example_embeddings = self.model.encode(
            texts, convert_to_numpy=True, show_progress_bar=False
        )

        self.logger.info(
            "training_corpus_built",
            total_examples=len(self.examples),
            embedding_dim=self.example_embeddings.shape[1],
        )

    def classify(
        self, query: str, top_k: int = 5, threshold: float = 0.3
    ) -> Tuple[LLMProvider, TaskCategory, float]:
        """Classify a query using semantic similarity.

        Args:
            query: User query to classify
            top_k: Number of top similar examples to consider
            threshold: Minimum similarity threshold (0-1, default 0.3)

        Returns:
            Tuple of (provider, category, confidence)
        """
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        # Calculate cosine similarity with all examples
        similarities = cosine_similarity(
            [query_embedding], self.example_embeddings
        )[0]

        # Get top-k most similar examples
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        top_similarities = similarities[top_indices]

        # Log top matches for debugging
        for idx, sim in zip(top_indices[:3], top_similarities[:3]):
            example = self.examples[idx]
            self.logger.debug(
                "top_match",
                similarity=f"{sim:.3f}",
                provider=example.provider.value,
                example_text=example.text[:50],
            )

        # Vote among top-k examples weighted by similarity
        provider_scores: Dict[LLMProvider, float] = {}
        category_scores: Dict[TaskCategory, float] = {}

        for idx, similarity in zip(top_indices, top_similarities):
            if similarity < threshold:
                continue

            example = self.examples[idx]

            # Accumulate weighted scores
            provider_scores[example.provider] = (
                provider_scores.get(example.provider, 0.0) + similarity
            )
            category_scores[example.category] = (
                category_scores.get(example.category, 0.0) + similarity
            )

        # If no matches above threshold, return default
        if not provider_scores:
            self.logger.warning(
                "no_matches_above_threshold",
                threshold=threshold,
                max_similarity=top_similarities[0],
            )
            return (
                LLMProvider.CLAUDE_CODE,
                TaskCategory.GENERAL,
                top_similarities[0],
            )

        # Select provider with highest score
        selected_provider = max(provider_scores.items(), key=lambda x: x[1])
        provider, provider_score = selected_provider

        # Select category with highest score
        selected_category = max(category_scores.items(), key=lambda x: x[1])
        category, category_score = selected_category

        # Calculate confidence as normalized provider score
        # This represents how much of the total similarity mass is in the selected provider
        total_score = sum(provider_scores.values())
        confidence = provider_score / total_score if total_score > 0 else 0.0

        self.logger.info(
            "intent_classified",
            provider=provider.value,
            category=category.value,
            confidence=f"{confidence:.3f}",
            top_similarity=f"{top_similarities[0]:.3f}",
        )

        return provider, category, confidence

    def add_training_example(
        self,
        text: str,
        provider: LLMProvider,
        category: TaskCategory,
        confidence: float = 1.0,
    ) -> None:
        """Add a new training example (for online learning).

        Args:
            text: Example text
            provider: Target provider
            category: Task category
            confidence: Confidence in this example (0-1)
        """
        example = IntentExample(text, provider, category, confidence)

        # Add to examples
        self.examples.append(example)

        # Encode and add to embeddings
        new_embedding = self.model.encode([text], convert_to_numpy=True)
        self.example_embeddings = np.vstack([self.example_embeddings, new_embedding])

        self.logger.info(
            "training_example_added",
            provider=provider.value,
            category=category.value,
            total_examples=len(self.examples),
        )

    def get_provider_examples_count(self) -> Dict[str, int]:
        """Get count of training examples per provider.

        Returns:
            Dict mapping provider names to example counts
        """
        counts: Dict[str, int] = {}
        for example in self.examples:
            provider = example.provider.value
            counts[provider] = counts.get(provider, 0) + 1
        return counts


# Global instance
_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier(model_name: str = "all-MiniLM-L6-v2") -> IntentClassifier:
    """Get global intent classifier instance (singleton).

    Args:
        model_name: Sentence transformer model name

    Returns:
        IntentClassifier instance
    """
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier(model_name)
    return _intent_classifier
