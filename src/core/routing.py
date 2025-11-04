"""Intelligent task routing engine."""

import re
import time
from typing import Optional, List, Tuple
from src.models.schemas import (
    LLMProvider,
    TaskCategory,
    RoutingDecision,
)
from src.core.intent_classifier import get_intent_classifier
import structlog

# Import routing metrics if available
try:
    from src.api.main import routing_method, routing_confidence, ml_classification_latency
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = structlog.get_logger()


class TaskRouter:
    """Routes tasks to appropriate LLM providers based on intent."""

    # Routing patterns with weights
    ROUTING_PATTERNS = {
        LLMProvider.CLAUDE_CODE: [
            (r"\b(build|code|implement|debug|refactor|deploy|docker|kubernetes|k8s)\b", 0.9),
            (r"\b(fix|bug|error|issue|problem)\b", 0.8),
            (r"\b(create|write|generate).*\b(function|class|api|service|script)\b", 0.85),
            (r"\b(ci/cd|pipeline|devops|automation)\b", 0.9),
            (r"\b(test|unit test|integration test)\b", 0.75),
        ],
        LLMProvider.CHATGPT: [
            (r"\b(ui|interface|dashboard|frontend|user experience|ux)\b", 0.9),
            (r"\b(automate workflow|workflow automation)\b", 0.85),
            (r"\b(design|layout|component|widget)\b", 0.8),
            (r"\b(report|document|presentation)\b.*\b(format|create|generate)\b", 0.75),
        ],
        LLMProvider.GEMINI: [
            (r"\b(optimize prompt|improve instruction|better prompt)\b", 0.95),
            (r"\b(meta-prompt|prompt template|prompt engineering)\b", 0.9),
            (r"\b(refine|enhance).*\b(prompt|instruction)\b", 0.85),
        ],
        LLMProvider.LOCAL: [
            (r"\b(analyze|investigate|triage).*\b(incident|event|outage|failure)\b", 0.95),
            (r"\b(analyze|parse|examine).*\b(log|logs|logging)\b", 0.9),
            (r"\b(root cause|postmortem|what happened|why did)\b", 0.9),
            (r"\b(security.*incident|breach|vulnerability.*analysis)\b", 0.95),
            (r"\b(performance.*degradation|slow|latency.*issue)\b", 0.85),
        ],
    }

    # Task category patterns
    CATEGORY_PATTERNS = {
        TaskCategory.CODE_GENERATION: [
            r"\b(create|write|generate|build).*\b(function|class|api|service)\b"
        ],
        TaskCategory.CODE_IMPLEMENTATION: [r"\b(implement|add|create).*\b(feature|functionality)\b"],
        TaskCategory.DEBUGGING: [r"\b(fix|debug|solve|resolve).*\b(bug|error|issue)\b"],
        TaskCategory.DEPLOYMENT: [r"\b(deploy|release|publish|launch)\b"],
        TaskCategory.UI_GENERATION: [r"\b(ui|interface|dashboard|frontend)\b"],
        TaskCategory.WORKFLOW_AUTOMATION: [r"\b(automate|automation|workflow)\b"],
        TaskCategory.PROMPT_OPTIMIZATION: [r"\b(optimize|improve|refine).*\b(prompt|instruction)\b"],
        TaskCategory.INCIDENT_ANALYSIS: [
            r"\b(analyze|investigate).*\b(incident|outage|failure)\b"
        ],
        TaskCategory.LOG_ANALYSIS: [r"\b(analyze|parse).*\b(log|logs)\b"],
        TaskCategory.DOCUMENTATION: [r"\b(document|explain|describe|write.*docs)\b"],
        TaskCategory.TECHNICAL_ANALYSIS: [r"\b(analyze|review|examine).*\b(code|architecture)\b"],
    }

    # Collaboration patterns - tasks that benefit from multiple LLMs
    COLLABORATION_PATTERNS = {
        r"\b(build|create).*\b(complete|full|entire).*\b(dashboard|application|system)\b": [
            LLMProvider.GEMINI,  # Optimize requirements
            LLMProvider.CHATGPT,  # Design UI
            LLMProvider.CLAUDE_CODE,  # Implement and deploy
        ],
        r"\b(analyze.*incident|outage).*\b(and|then).*\b(fix|create|write)\b": [
            LLMProvider.LOCAL,  # Analyze incident
            LLMProvider.CLAUDE_CODE,  # Implement fixes
        ],
        r"\b(analyze.*incident|outage).*\b(report|document)\b": [
            LLMProvider.LOCAL,  # Analyze incident
            LLMProvider.CHATGPT,  # Create report
        ],
    }

    def __init__(self, use_ml_routing: bool = True) -> None:
        """Initialize the router.

        Args:
            use_ml_routing: Whether to use ML-based intent classification (default: True)
                           Falls back to regex if False or if ML fails
        """
        self.logger = logger.bind(component="task_router")
        self.use_ml_routing = use_ml_routing

        # Initialize ML classifier if enabled
        if self.use_ml_routing:
            try:
                self.intent_classifier = get_intent_classifier()
                self.logger.info("ml_routing_enabled", model=self.intent_classifier.model_name)
            except Exception as e:
                self.logger.error("ml_classifier_init_failed", error=str(e))
                self.use_ml_routing = False
                self.intent_classifier = None
        else:
            self.intent_classifier = None
            self.logger.info("ml_routing_disabled", note="Using regex-based routing only")

    def extract_explicit_provider(self, message: str) -> Tuple[Optional[LLMProvider], str]:
        """Extract explicit provider mention from message.

        Args:
            message: User message

        Returns:
            Tuple of (provider, cleaned_message)
        """
        patterns = {
            LLMProvider.CLAUDE_CODE: r"@claude[-_]code:\s*",
            LLMProvider.CHATGPT: r"@chatgpt:\s*",
            LLMProvider.GEMINI: r"@gemini:\s*",
            LLMProvider.CLAUDE: r"@claude:\s*",
            LLMProvider.LOCAL: r"@local:\s*",
        }

        for provider, pattern in patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                cleaned = re.sub(pattern, "", message, flags=re.IGNORECASE).strip()
                self.logger.info("explicit_provider_detected", provider=provider)
                return provider, cleaned

        return None, message

    def classify_task(self, message: str) -> TaskCategory:
        """Classify the task category.

        Args:
            message: User message

        Returns:
            TaskCategory
        """
        message_lower = message.lower()

        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    self.logger.info("task_classified", category=category)
                    return category

        return TaskCategory.GENERAL

    def calculate_provider_scores_ml(
        self, message: str
    ) -> Tuple[LLMProvider, TaskCategory, float]:
        """Calculate provider using ML-based intent classification.

        Args:
            message: User message

        Returns:
            Tuple of (provider, category, confidence)
        """
        if not self.intent_classifier:
            raise RuntimeError("ML classifier not initialized")

        # Time the ML classification
        start_time = time.time()
        provider, category, confidence = self.intent_classifier.classify(message)
        classification_time = time.time() - start_time

        # Record metrics
        if METRICS_AVAILABLE:
            ml_classification_latency.observe(classification_time)
            routing_confidence.labels(
                provider=provider.value,
                method="ml"
            ).observe(confidence)

        self.logger.info(
            "ml_classification",
            provider=provider.value,
            category=category.value,
            confidence=f"{confidence:.3f}",
            latency_ms=f"{classification_time*1000:.1f}",
        )

        return provider, category, confidence

    def calculate_provider_scores(self, message: str) -> dict[LLMProvider, float]:
        """Calculate confidence scores for each provider using regex patterns.

        Args:
            message: User message

        Returns:
            Dict mapping providers to confidence scores
        """
        message_lower = message.lower()
        scores: dict[LLMProvider, float] = {provider: 0.0 for provider in LLMProvider}

        for provider, patterns in self.ROUTING_PATTERNS.items():
            for pattern, weight in patterns:
                if re.search(pattern, message_lower):
                    scores[provider] = max(scores[provider], weight)

        return scores

    def check_collaboration(self, message: str) -> Tuple[bool, Optional[List[LLMProvider]]]:
        """Check if task requires multi-LLM collaboration.

        Args:
            message: User message

        Returns:
            Tuple of (requires_collaboration, collaboration_plan)
        """
        message_lower = message.lower()

        for pattern, providers in self.COLLABORATION_PATTERNS.items():
            if re.search(pattern, message_lower):
                self.logger.info("collaboration_required", providers=providers)
                return True, providers

        return False, None

    def get_fallback_chain(self, category: TaskCategory) -> List[LLMProvider]:
        """Get fallback provider chain for a task category.

        Priority: Free-tier providers (Local, Gemini) before paid subscriptions (Claude, ChatGPT)

        Args:
            category: Task category

        Returns:
            List of fallback providers in order (free-tier first, then paid)
        """
        # Analysis tasks: Local first (free), then Gemini (free), then Claude (paid)
        if category in [
            TaskCategory.INCIDENT_ANALYSIS,
            TaskCategory.LOG_ANALYSIS,
            TaskCategory.TECHNICAL_ANALYSIS,
        ]:
            return [LLMProvider.LOCAL, LLMProvider.GEMINI, LLMProvider.CLAUDE]

        # Code tasks: Gemini first (free), then Claude Code (paid)
        if category in [
            TaskCategory.CODE_GENERATION,
            TaskCategory.CODE_IMPLEMENTATION,
            TaskCategory.DEBUGGING,
            TaskCategory.DEPLOYMENT,
        ]:
            return [LLMProvider.GEMINI, LLMProvider.LOCAL, LLMProvider.CLAUDE_CODE, LLMProvider.CLAUDE]

        # UI tasks: Gemini first (free), then ChatGPT (paid), then Claude (paid)
        if category in [TaskCategory.UI_GENERATION, TaskCategory.WORKFLOW_AUTOMATION]:
            return [LLMProvider.GEMINI, LLMProvider.LOCAL, LLMProvider.CHATGPT, LLMProvider.CLAUDE]

        # Default fallback chain: Free providers first, then paid
        return [LLMProvider.LOCAL, LLMProvider.GEMINI, LLMProvider.CLAUDE, LLMProvider.CHATGPT]

    def route(
        self,
        message: str,
        explicit_provider: Optional[LLMProvider] = None,
        enable_collaboration: bool = True,
    ) -> RoutingDecision:
        """Route a task to the appropriate provider.

        Args:
            message: User message
            explicit_provider: Explicitly specified provider (overrides routing)
            enable_collaboration: Whether to enable multi-LLM collaboration

        Returns:
            RoutingDecision
        """
        # Check for explicit provider mention in message
        extracted_provider, cleaned_message = self.extract_explicit_provider(message)
        if extracted_provider:
            explicit_provider = extracted_provider
            message = cleaned_message

        # If explicit provider specified, use it
        if explicit_provider:
            category = self.classify_task(message)
            fallback_chain = self.get_fallback_chain(category)

            # Record metrics
            if METRICS_AVAILABLE:
                routing_method.labels(method="explicit").inc()
                routing_confidence.labels(
                    provider=explicit_provider.value,
                    method="explicit"
                ).observe(1.0)

            return RoutingDecision(
                provider=explicit_provider,
                category=category,
                confidence=1.0,
                reasoning=f"Explicitly requested provider: {explicit_provider.value}",
                fallback_providers=fallback_chain,
                requires_collaboration=False,
            )

        # Check for collaboration opportunities
        requires_collab, collab_plan = (
            self.check_collaboration(message) if enable_collaboration else (False, None)
        )

        if requires_collab and collab_plan:
            category = self.classify_task(message)
            return RoutingDecision(
                provider=collab_plan[0],  # Start with first provider
                category=category,
                confidence=0.95,
                reasoning="Task requires multi-LLM collaboration",
                fallback_providers=[],
                requires_collaboration=True,
                collaboration_plan=collab_plan,
            )

        # Try ML-based classification first
        routing_method_used = "ml"
        if self.use_ml_routing and self.intent_classifier:
            try:
                provider, category, confidence = self.calculate_provider_scores_ml(message)
                reasoning = f"ML-based routing with {confidence:.0%} confidence"

                # If ML confidence is low, use regex as fallback
                if confidence < 0.6:
                    self.logger.info(
                        "ml_confidence_low_using_regex_fallback",
                        ml_confidence=f"{confidence:.3f}",
                    )

                    # Calculate regex scores
                    scores = self.calculate_provider_scores(message)
                    selected_regex = max(scores.items(), key=lambda x: x[1])
                    regex_provider, regex_confidence = selected_regex

                    # Use regex if it has higher confidence
                    if regex_confidence > confidence:
                        provider = regex_provider
                        confidence = regex_confidence
                        category = self.classify_task(message)
                        routing_method_used = "regex_fallback"
                        reasoning = (
                            f"Regex fallback routing with {confidence:.0%} confidence "
                            f"(ML confidence was too low)"
                        )
                        self.logger.info(
                            "regex_fallback_used",
                            regex_provider=regex_provider.value,
                            regex_confidence=f"{regex_confidence:.3f}",
                        )

                        # Record fallback metrics
                        if METRICS_AVAILABLE:
                            routing_confidence.labels(
                                provider=provider.value,
                                method="regex_fallback"
                            ).observe(confidence)

            except Exception as e:
                self.logger.error("ml_routing_failed", error=str(e))
                # Fall back to regex routing
                scores = self.calculate_provider_scores(message)
                category = self.classify_task(message)
                selected_provider = max(scores.items(), key=lambda x: x[1])
                provider, confidence = selected_provider
                routing_method_used = "regex_fallback"
                reasoning = f"Regex fallback routing (ML failed) with {confidence:.0%} confidence"

                # Record fallback metrics
                if METRICS_AVAILABLE:
                    routing_confidence.labels(
                        provider=provider.value,
                        method="regex_fallback"
                    ).observe(confidence)
        else:
            # Use regex-based routing
            scores = self.calculate_provider_scores(message)
            category = self.classify_task(message)

            # Select provider with highest score
            selected_provider = max(scores.items(), key=lambda x: x[1])
            provider, confidence = selected_provider
            routing_method_used = "regex"
            reasoning = f"Regex-based routing with {confidence:.0%} confidence"

            # Record regex metrics
            if METRICS_AVAILABLE:
                routing_confidence.labels(
                    provider=provider.value,
                    method="regex"
                ).observe(confidence)

        # If no strong match, default to Claude Code for technical tasks
        if confidence < 0.5:
            provider = LLMProvider.CLAUDE_CODE
            confidence = 0.6
            routing_method_used = "default"
            reasoning = "Default routing to Claude Code for general technical task"

        # Record routing method used
        if METRICS_AVAILABLE:
            routing_method.labels(method=routing_method_used).inc()

        fallback_chain = self.get_fallback_chain(category)

        self.logger.info(
            "routing_decision",
            provider=provider,
            category=category,
            confidence=confidence,
            fallback_chain=fallback_chain,
        )

        return RoutingDecision(
            provider=provider,
            category=category,
            confidence=confidence,
            reasoning=reasoning,
            fallback_providers=fallback_chain,
            requires_collaboration=False,
        )
