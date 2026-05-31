"""Query classification system for dynamic context-aware routing.

Enhancement 018: Pre-routing intent classification and context extraction.
"""

import re
import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import structlog
from src.models.schemas import LLMProvider, TaskCategory
from src.core.intent_classifier import IntentClassifier, get_intent_classifier

logger = structlog.get_logger()


@dataclass
class QueryContext:
    """Extracted context from a query."""

    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    code_languages: List[str] = field(default_factory=list)
    mentions_files: bool = False
    mentions_errors: bool = False
    mentions_logs: bool = False
    mentions_security: bool = False
    mentions_performance: bool = False
    has_code_block: bool = False
    question_type: str = "statement"  # question, statement, command
    sentiment: str = "neutral"  # urgent, neutral, exploratory


@dataclass
class ClassificationResult:
    """Result of query classification."""

    primary_intent: str
    confidence: float
    profile: str
    provider: LLMProvider
    category: TaskCategory
    context: QueryContext
    complexity_score: float
    needs_blending: bool
    blend_providers: List[LLMProvider] = field(default_factory=list)
    blend_strategy: str = "sequential"
    fallback_chain: List[LLMProvider] = field(default_factory=list)
    classification_time_ms: float = 0.0


class QueryClassifier:
    """Classifies queries for dynamic context-aware routing.

    Components:
    - IntentClassifier: Detect query intent category
    - ContextExtractor: Extract entities, keywords, signals
    - ComplexityScorer: Rate query complexity (1-10)
    - BlendingDetector: Identify multi-perspective needs
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize query classifier.

        Args:
            config_path: Path to routing_weights.yaml
        """
        self.intent_classifier = get_intent_classifier()

        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "routing_weights.yaml"

        self.config = self._load_config(config_path)
        self.intent_patterns = self.config.get("intent_patterns", {})
        self.routing_profiles = self.config.get("routing_profiles", {})
        self.complexity_config = self.config.get("complexity_scoring", {})
        self.global_settings = self.config.get("global_settings", {})

        logger.info("query_classifier_initialized", config_loaded=bool(self.config))

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load routing configuration from YAML."""
        try:
            if Path(config_path).exists():
                with open(config_path, "r") as f:
                    return yaml.safe_load(f)
            else:
                logger.warning("config_not_found", path=str(config_path))
                return {}
        except Exception as e:
            logger.error("config_load_error", error=str(e))
            return {}

    def classify_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """Classify a query for routing.

        Args:
            query: User query text
            context: Optional additional context (conversation history, etc.)

        Returns:
            ClassificationResult with routing information
        """
        start_time = time.time()

        # Extract context from query
        query_context = self._extract_context(query)

        # Detect profile
        profile = self._detect_profile(query, query_context)

        # Classify intent using ML classifier
        intent, confidence, provider, category = self._classify_intent(query, profile)

        # Score complexity
        complexity = self._score_complexity(query, query_context)

        # Check if blending is needed
        needs_blending, blend_providers, blend_strategy = self._detect_blending_need(
            query, intent, complexity, profile
        )

        # Get fallback chain for profile
        fallback_chain = self._get_fallback_chain(profile, intent)

        classification_time = (time.time() - start_time) * 1000

        result = ClassificationResult(
            primary_intent=intent,
            confidence=confidence,
            profile=profile,
            provider=provider,
            category=category,
            context=query_context,
            complexity_score=complexity,
            needs_blending=needs_blending,
            blend_providers=blend_providers,
            blend_strategy=blend_strategy,
            fallback_chain=fallback_chain,
            classification_time_ms=classification_time,
        )

        logger.info(
            "query_classified",
            intent=intent,
            confidence=confidence,
            profile=profile,
            provider=provider.value if provider else None,
            complexity=complexity,
            needs_blending=needs_blending,
            time_ms=classification_time,
        )

        return result

    def _extract_context(self, query: str) -> QueryContext:
        """Extract contextual information from query."""
        query_lower = query.lower()

        # Extract keywords
        keywords = self._extract_keywords(query)

        # Extract entities (file paths, URLs, etc.)
        entities = self._extract_entities(query)

        # Detect code languages
        code_languages = self._detect_languages(query)

        # Check for various signals
        mentions_files = bool(re.search(r'\b\w+\.\w{2,4}\b', query))
        mentions_errors = any(word in query_lower for word in [
            "error", "exception", "fail", "crash", "bug", "issue", "broken"
        ])
        mentions_logs = any(word in query_lower for word in [
            "log", "logs", "trace", "stack trace", "debug output"
        ])
        mentions_security = any(word in query_lower for word in [
            "security", "vulnerability", "breach", "attack", "exploit", "auth"
        ])
        mentions_performance = any(word in query_lower for word in [
            "slow", "performance", "latency", "bottleneck", "optimize", "memory"
        ])
        has_code_block = "```" in query or "    " in query

        # Determine question type
        if query.strip().endswith("?"):
            question_type = "question"
        elif any(query_lower.startswith(word) for word in ["create", "build", "write", "implement", "fix"]):
            question_type = "command"
        else:
            question_type = "statement"

        # Detect sentiment/urgency
        if any(word in query_lower for word in ["urgent", "asap", "immediately", "critical", "production down"]):
            sentiment = "urgent"
        elif any(word in query_lower for word in ["explore", "consider", "might", "could", "options"]):
            sentiment = "exploratory"
        else:
            sentiment = "neutral"

        return QueryContext(
            keywords=keywords,
            entities=entities,
            code_languages=code_languages,
            mentions_files=mentions_files,
            mentions_errors=mentions_errors,
            mentions_logs=mentions_logs,
            mentions_security=mentions_security,
            mentions_performance=mentions_performance,
            has_code_block=has_code_block,
            question_type=question_type,
            sentiment=sentiment,
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        # Technical keywords to look for
        tech_keywords = [
            "api", "database", "server", "client", "docker", "kubernetes",
            "deploy", "test", "debug", "refactor", "optimize", "cache",
            "authenticate", "authorize", "encrypt", "monitor", "log",
            "incident", "error", "bug", "performance", "security"
        ]

        query_lower = query.lower()
        found = [kw for kw in tech_keywords if kw in query_lower]
        return found

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities like file paths, URLs, function names."""
        entities = []

        # File paths
        file_patterns = re.findall(r'[\w/\-\.]+\.\w{2,4}', query)
        entities.extend(file_patterns)

        # URLs
        url_patterns = re.findall(r'https?://\S+', query)
        entities.extend(url_patterns)

        # Function/class names (camelCase or snake_case)
        code_patterns = re.findall(r'\b[a-z]+(?:[A-Z][a-z]+)+\b|\b[a-z]+(?:_[a-z]+)+\b', query)
        entities.extend(code_patterns[:5])  # Limit to 5

        return entities

    def _detect_languages(self, query: str) -> List[str]:
        """Detect programming languages mentioned."""
        language_patterns = {
            "python": r"\b(python|py|pip|pytest|django|flask)\b",
            "javascript": r"\b(javascript|js|node|npm|react|vue)\b",
            "typescript": r"\b(typescript|ts)\b",
            "java": r"\b(java|maven|gradle|spring)\b",
            "go": r"\b(golang|go)\b",
            "rust": r"\b(rust|cargo)\b",
            "sql": r"\b(sql|mysql|postgres|mongodb)\b",
            "bash": r"\b(bash|shell|sh)\b",
        }

        query_lower = query.lower()
        detected = []
        for lang, pattern in language_patterns.items():
            if re.search(pattern, query_lower):
                detected.append(lang)

        return detected

    def _detect_profile(self, query: str, context: QueryContext) -> str:
        """Detect the appropriate routing profile."""
        query_lower = query.lower()

        # Check for explicit profile mentions
        if "@developer" in query_lower or "@code" in query_lower:
            return "developer"
        if "@incident" in query_lower or "@privacy" in query_lower:
            return "incident_analysis"
        if "@production" in query_lower or "@balanced" in query_lower:
            return "production"

        # Check profile detection signals
        profile_detection = self.global_settings.get("profile_detection", {})

        # Developer signals
        developer_signals = profile_detection.get("developer_signals", [])
        if any(signal in query_lower for signal in developer_signals):
            return "developer"

        # Incident signals
        incident_signals = profile_detection.get("incident_signals", [])
        if any(signal in query_lower for signal in incident_signals):
            return "incident_analysis"

        # Context-based detection
        if context.mentions_logs or context.mentions_security:
            return "incident_analysis"
        if context.has_code_block or len(context.code_languages) > 0:
            return "developer"
        if context.mentions_errors and not context.mentions_logs:
            return "developer"

        # Default to production profile
        return self.global_settings.get("default_profile", "production")

    def _classify_intent(
        self, query: str, profile: str
    ) -> Tuple[str, float, LLMProvider, TaskCategory]:
        """Classify query intent using ML and patterns."""

        # Get ML classification
        # Returns: (LLMProvider, TaskCategory, float confidence)
        ml_result = self.intent_classifier.classify(query)
        provider = ml_result[0]
        category = ml_result[1]
        confidence = ml_result[2]

        # Map category to intent name
        intent = self._category_to_intent(category)

        # Boost confidence based on pattern matches
        for intent_name, patterns in self.intent_patterns.items():
            pattern_list = patterns.get("patterns", [])
            keywords = patterns.get("keywords", [])

            query_lower = query.lower()
            for pattern in pattern_list:
                if re.search(pattern, query_lower):
                    if intent_name == intent:
                        confidence = min(confidence + 0.1, 1.0)
                    else:
                        # Consider switching intent if pattern match is strong
                        intent = intent_name
                        confidence = 0.85
                    break

            for keyword in keywords:
                if keyword in query_lower:
                    if intent_name == intent:
                        confidence = min(confidence + 0.05, 1.0)
                    break

        # Adjust provider based on profile intent mapping
        profile_config = self.routing_profiles.get(profile, {})
        intent_mapping = profile_config.get("intent_mapping", {})

        if intent in intent_mapping:
            mapping = intent_mapping[intent]
            if "primary" in mapping:
                provider = LLMProvider(mapping["primary"])

        return intent, confidence, provider, category

    def _category_to_intent(self, category: TaskCategory) -> str:
        """Convert TaskCategory to intent name."""
        mapping = {
            TaskCategory.CODE_GENERATION: "code_generation",
            TaskCategory.CODE_IMPLEMENTATION: "code_generation",
            TaskCategory.DEBUGGING: "debugging",
            TaskCategory.DEPLOYMENT: "devops",
            TaskCategory.UI_GENERATION: "creative_query",
            TaskCategory.WORKFLOW_AUTOMATION: "devops",
            TaskCategory.PROMPT_OPTIMIZATION: "general_query",
            TaskCategory.INCIDENT_ANALYSIS: "root_cause_analysis",
            TaskCategory.LOG_ANALYSIS: "log_analysis",
            TaskCategory.DOCUMENTATION: "documentation",
            TaskCategory.TECHNICAL_ANALYSIS: "architecture_design",
            TaskCategory.GENERAL: "general_query",
        }
        return mapping.get(category, "general_query")

    def _score_complexity(self, query: str, context: QueryContext) -> float:
        """Score query complexity from 1-10."""
        score = 5.0  # Base score

        factors = self.complexity_config.get("factors", {})

        # Token count factor
        token_count_config = factors.get("token_count", {})
        weight = token_count_config.get("weight", 0.2)
        tokens = len(query.split())

        thresholds = token_count_config.get("thresholds", {})
        if tokens > thresholds.get("high", 500):
            score += 3 * weight * 10
        elif tokens > thresholds.get("medium", 200):
            score += 2 * weight * 10
        elif tokens > thresholds.get("low", 50):
            score += 1 * weight * 10

        # Keyword density factor
        keyword_config = factors.get("keyword_density", {})
        weight = keyword_config.get("weight", 0.15)
        keyword_count = len(context.keywords)
        score += keyword_count * 0.3 * weight * 10

        # Context requirements
        context_config = factors.get("context_requirements", {})
        weight = context_config.get("weight", 0.2)
        if context.has_code_block:
            score += context_config.get("needs_code_context", 2.0) * weight
        if context.mentions_errors or context.mentions_logs:
            score += context_config.get("needs_system_context", 1.5) * weight

        # Multiple entities suggest complexity
        if len(context.entities) > 3:
            score += 1.0

        # Code languages suggest technical complexity
        if len(context.code_languages) > 1:
            score += 1.0

        # Urgent queries are often complex
        if context.sentiment == "urgent":
            score += 1.5

        # Clamp to 1-10
        return max(1.0, min(10.0, score))

    def _detect_blending_need(
        self, query: str, intent: str, complexity: float, profile: str
    ) -> Tuple[bool, List[LLMProvider], str]:
        """Detect if query needs multi-provider blending."""

        # Check if blending is enabled
        if not self.global_settings.get("enable_blending", True):
            return False, [], "none"

        # High complexity queries may need blending
        needs_blending = complexity >= 7.0

        # Check profile for intent-specific blending
        profile_config = self.routing_profiles.get(profile, {})
        intent_mapping = profile_config.get("intent_mapping", {})

        blend_providers: List[LLMProvider] = []
        blend_strategy = "sequential"

        if intent in intent_mapping:
            mapping = intent_mapping[intent]
            if "blend" in mapping:
                needs_blending = True
                blend_config = mapping["blend"]

                if isinstance(blend_config, list):
                    # Simple list of providers
                    blend_providers = [LLMProvider(p) for p in blend_config]
                elif isinstance(blend_config, dict):
                    # Detailed blend config
                    providers = blend_config.get("providers", [])
                    blend_providers = [LLMProvider(p) for p in providers]
                    blend_strategy = blend_config.get("strategy", "sequential")

        # Multi-part queries need blending
        query_lower = query.lower()
        if " and then " in query_lower or " also " in query_lower:
            needs_blending = True
            if not blend_providers:
                # Default blending for multi-part
                blend_providers = [LLMProvider.LOCAL, LLMProvider.CLAUDE_CODE]

        return needs_blending, blend_providers, blend_strategy

    def _get_fallback_chain(self, profile: str, intent: str) -> List[LLMProvider]:
        """Get fallback chain for profile."""
        profile_config = self.routing_profiles.get(profile, {})

        # Check intent-specific fallback
        intent_mapping = profile_config.get("intent_mapping", {})
        if intent in intent_mapping:
            mapping = intent_mapping[intent]
            if "fallback" in mapping:
                return [LLMProvider(p) for p in mapping["fallback"]]

        # Return profile default fallback chain
        fallback = profile_config.get("fallback_chain", [])
        return [LLMProvider(p) for p in fallback]


# Singleton instance
_query_classifier: Optional[QueryClassifier] = None


def get_query_classifier() -> QueryClassifier:
    """Get singleton QueryClassifier instance."""
    global _query_classifier
    if _query_classifier is None:
        _query_classifier = QueryClassifier()
    return _query_classifier
