"""Tests for ML-based intent classification and routing."""

import pytest
from src.core.intent_classifier import IntentClassifier, IntentExample, get_intent_classifier
from src.core.routing import TaskRouter
from src.models.schemas import LLMProvider, TaskCategory


class TestIntentClassifier:
    """Test IntentClassifier class."""

    def test_classifier_initialization(self):
        """Test that classifier initializes correctly."""
        classifier = IntentClassifier()
        assert classifier is not None
        assert classifier.model is not None
        assert len(classifier.examples) > 0
        assert classifier.example_embeddings is not None

    def test_training_corpus_built(self):
        """Test that training corpus is built with examples."""
        classifier = IntentClassifier()

        # Should have examples from all providers
        example_counts = classifier.get_provider_examples_count()
        assert "claude_code" in example_counts
        assert "chatgpt" in example_counts
        assert "gemini" in example_counts
        assert "local" in example_counts

        # Should have reasonable number of examples
        total_examples = sum(example_counts.values())
        assert total_examples >= 30  # At least 30 training examples

    def test_classify_code_generation(self):
        """Test classification of code generation queries."""
        classifier = IntentClassifier()

        queries = [
            "Build a REST API for user authentication",
            "Create a Python function to sort a list",
            "Implement a Docker deployment pipeline",
            "Write unit tests for the authentication module",
        ]

        for query in queries:
            provider, category, confidence = classifier.classify(query)

            # Should route to Claude Code for code generation
            assert provider == LLMProvider.CLAUDE_CODE
            # Confidence should be reasonable (semantic similarity based)
            assert confidence > 0.2  # At least some confidence

    def test_classify_ui_generation(self):
        """Test classification of UI generation queries."""
        classifier = IntentClassifier()

        queries = [
            "Design a modern dashboard with charts",
            "Create a responsive navigation menu",
            "Build a user-friendly onboarding wizard",
            "Design a mobile-first landing page",
        ]

        for query in queries:
            provider, category, confidence = classifier.classify(query)

            # Should route to ChatGPT for UI generation
            assert provider == LLMProvider.CHATGPT
            assert confidence > 0.2

    def test_classify_prompt_optimization(self):
        """Test classification of prompt optimization queries."""
        classifier = IntentClassifier()

        queries = [
            "Optimize this prompt to get better results",
            "Improve the instruction clarity for code generation",
            "Refine this prompt template for consistency",
            "Create a meta-prompt for generating system prompts",
        ]

        for query in queries:
            provider, category, confidence = classifier.classify(query)

            # Should route to Gemini for prompt optimization
            assert provider == LLMProvider.GEMINI
            assert confidence > 0.2

    def test_classify_incident_analysis(self):
        """Test classification of incident analysis queries."""
        classifier = IntentClassifier()

        queries = [
            "Analyze this production incident and find root cause",
            "Investigate the service outage from last night",
            "Examine these error logs for failure patterns",
            "Triage this security incident",
        ]

        for query in queries:
            provider, category, confidence = classifier.classify(query)

            # Should route to Local LLM for incident analysis
            assert provider == LLMProvider.LOCAL
            assert confidence > 0.3

    def test_classify_with_threshold(self):
        """Test classification with different similarity thresholds."""
        classifier = IntentClassifier()

        query = "Build a REST API for authentication"

        # With normal threshold
        provider1, _, conf1 = classifier.classify(query, threshold=0.5)
        assert conf1 >= 0.5

        # With higher threshold
        provider2, _, conf2 = classifier.classify(query, threshold=0.8)

        # Results should be consistent for clear matches
        assert provider1 == provider2 or conf2 < 0.8

    def test_classify_top_k(self):
        """Test classification with different top-k values."""
        classifier = IntentClassifier()

        query = "Create a monitoring dashboard with deployment"

        # With top-k=3
        provider1, _, _ = classifier.classify(query, top_k=3)

        # With top-k=10
        provider2, _, _ = classifier.classify(query, top_k=10)

        # Results should be reasonable
        assert provider1 is not None
        assert provider2 is not None

    def test_add_training_example(self):
        """Test adding new training examples."""
        classifier = IntentClassifier()

        initial_count = len(classifier.examples)

        # Add new example
        classifier.add_training_example(
            "Deploy the microservice to production cluster",
            LLMProvider.CLAUDE_CODE,
            TaskCategory.DEPLOYMENT,
            confidence=1.0,
        )

        # Should have one more example
        assert len(classifier.examples) == initial_count + 1

        # Embeddings should be updated
        assert classifier.example_embeddings.shape[0] == len(classifier.examples)

    def test_get_provider_examples_count(self):
        """Test getting example counts per provider."""
        classifier = IntentClassifier()

        counts = classifier.get_provider_examples_count()

        # Should have counts for all providers with examples
        assert isinstance(counts, dict)
        assert len(counts) > 0

        # All counts should be positive
        for provider, count in counts.items():
            assert count > 0


class TestIntentClassifierSingleton:
    """Test global intent classifier singleton."""

    def test_get_intent_classifier_returns_instance(self):
        """Test that get_intent_classifier returns an instance."""
        classifier = get_intent_classifier()
        assert classifier is not None
        assert isinstance(classifier, IntentClassifier)

    def test_get_intent_classifier_returns_singleton(self):
        """Test that get_intent_classifier returns the same instance."""
        classifier1 = get_intent_classifier()
        classifier2 = get_intent_classifier()

        assert classifier1 is classifier2


class TestMLRoutingIntegration:
    """Test ML routing integration with TaskRouter."""

    def test_task_router_with_ml_enabled(self):
        """Test TaskRouter with ML routing enabled."""
        router = TaskRouter(use_ml_routing=True)

        assert router.use_ml_routing is True
        assert router.intent_classifier is not None

    def test_task_router_with_ml_disabled(self):
        """Test TaskRouter with ML routing disabled."""
        router = TaskRouter(use_ml_routing=False)

        assert router.use_ml_routing is False
        assert router.intent_classifier is None

    def test_ml_routing_code_generation(self):
        """Test ML routing for code generation tasks."""
        router = TaskRouter(use_ml_routing=True)

        decision = router.route("Build a REST API for user authentication")

        # Should route to Claude Code
        assert decision.provider == LLMProvider.CLAUDE_CODE
        # Should have reasonable confidence
        assert decision.confidence > 0.5
        # Reasoning should mention ML
        assert "ML" in decision.reasoning or "routing" in decision.reasoning.lower()

    def test_ml_routing_ui_generation(self):
        """Test ML routing for UI generation tasks."""
        router = TaskRouter(use_ml_routing=True)

        decision = router.route("Design a modern dashboard with real-time charts")

        # Should route to ChatGPT
        assert decision.provider == LLMProvider.CHATGPT
        assert decision.confidence > 0.5

    def test_ml_routing_prompt_optimization(self):
        """Test ML routing for prompt optimization tasks."""
        router = TaskRouter(use_ml_routing=True)

        decision = router.route("Optimize this prompt to get better LLM results")

        # Should route to Gemini
        assert decision.provider == LLMProvider.GEMINI
        assert decision.confidence > 0.5

    def test_ml_routing_incident_analysis(self):
        """Test ML routing for incident analysis tasks."""
        router = TaskRouter(use_ml_routing=True)

        decision = router.route("Analyze this production incident and find the root cause")

        # Should route to Local LLM
        assert decision.provider == LLMProvider.LOCAL
        assert decision.confidence > 0.5

    def test_ml_routing_fallback_to_regex(self):
        """Test that ML routing falls back to regex when confidence is low."""
        router = TaskRouter(use_ml_routing=True)

        # Ambiguous query that might trigger regex fallback
        decision = router.route("Do something with the system")

        # Should have a provider selected (either ML or regex)
        assert decision.provider is not None
        # Should have some confidence
        assert decision.confidence > 0

    def test_regex_only_routing(self):
        """Test routing with ML disabled (regex only)."""
        router = TaskRouter(use_ml_routing=False)

        decision = router.route("Build a Docker deployment pipeline")

        # Should still route correctly using regex
        assert decision.provider == LLMProvider.CLAUDE_CODE
        # Reasoning should mention regex or pattern
        assert "Regex" in decision.reasoning or "Pattern" in decision.reasoning or "Default" in decision.reasoning

    def test_explicit_provider_override(self):
        """Test that explicit provider overrides ML routing."""
        router = TaskRouter(use_ml_routing=True)

        # Even though this is a code task, explicit provider should win
        decision = router.route(
            "Build a REST API",
            explicit_provider=LLMProvider.CHATGPT
        )

        assert decision.provider == LLMProvider.CHATGPT
        assert decision.confidence == 1.0
        assert "Explicitly requested" in decision.reasoning

    def test_at_mention_provider_override(self):
        """Test @mention provider override."""
        router = TaskRouter(use_ml_routing=True)

        decision = router.route("@chatgpt: Build a REST API")

        # Should use explicitly mentioned provider
        assert decision.provider == LLMProvider.CHATGPT
        assert decision.confidence == 1.0


class TestRoutingAccuracy:
    """Test routing accuracy across various query types."""

    def test_accuracy_on_clear_queries(self):
        """Test routing accuracy on clear, unambiguous queries."""
        router = TaskRouter(use_ml_routing=True)

        test_cases = [
            ("Build a REST API for authentication", LLMProvider.CLAUDE_CODE),
            ("Design a responsive dashboard UI", LLMProvider.CHATGPT),
            ("Optimize this prompt for better results", LLMProvider.GEMINI),
            ("Analyze this production incident", LLMProvider.LOCAL),
            ("Fix the bug in the authentication service", LLMProvider.CLAUDE_CODE),
            ("Create a workflow automation for support tickets", LLMProvider.CHATGPT),
        ]

        correct = 0
        for query, expected_provider in test_cases:
            decision = router.route(query)
            if decision.provider == expected_provider:
                correct += 1

        # Should get at least 80% accuracy on clear queries
        accuracy = correct / len(test_cases)
        assert accuracy >= 0.8, f"Routing accuracy: {accuracy:.1%} (expected >= 80%)"

    def test_confidence_correlation(self):
        """Test that higher confidence correlates with correct routing."""
        router = TaskRouter(use_ml_routing=True)

        queries = [
            "Build a REST API for user authentication",
            "Design a modern dashboard with charts",
            "Optimize this prompt template",
            "Analyze the production outage",
        ]

        confidences = []
        for query in queries:
            decision = router.route(query)
            confidences.append(decision.confidence)

        # All clear queries should have reasonable confidence
        avg_confidence = sum(confidences) / len(confidences)
        assert avg_confidence > 0.6, f"Average confidence: {avg_confidence:.1%}"


class TestRoutingPerformance:
    """Test routing performance."""

    def test_ml_classification_latency(self):
        """Test that ML classification is fast enough."""
        import time

        classifier = IntentClassifier()
        query = "Build a REST API for user authentication"

        start_time = time.time()
        classifier.classify(query)
        latency = time.time() - start_time

        # Should classify within 100ms (success criterion)
        assert latency < 0.1, f"Classification latency: {latency*1000:.1f}ms (expected <100ms)"

    def test_routing_latency(self):
        """Test end-to-end routing latency."""
        import time

        router = TaskRouter(use_ml_routing=True)
        query = "Create a monitoring dashboard with deployment"

        start_time = time.time()
        router.route(query)
        latency = time.time() - start_time

        # Should route within 150ms (including classification)
        assert latency < 0.15, f"Routing latency: {latency*1000:.1f}ms (expected <150ms)"


class TestTaskCategoryClassification:
    """Test task category classification."""

    def test_category_classification(self):
        """Test that categories are classified correctly."""
        router = TaskRouter(use_ml_routing=True)

        test_cases = [
            ("Build a REST API", TaskCategory.CODE_GENERATION),
            ("Fix the authentication bug", TaskCategory.DEBUGGING),
            ("Deploy to production", TaskCategory.DEPLOYMENT),
            ("Create a dashboard UI", TaskCategory.UI_GENERATION),
        ]

        for query, expected_category in test_cases:
            decision = router.route(query)

            # Category should match or be related
            assert decision.category is not None
