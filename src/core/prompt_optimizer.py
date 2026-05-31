"""Prompt Optimizer - Provider-Specific Prompt Templates

Enhancement 021: Enhance Current FREE Providers
Loads and applies provider-specific prompt templates for better response quality.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import structlog

from src.models.schemas import LLMProvider

logger = structlog.get_logger(__name__)


class TaskType(str, Enum):
    """Task types for prompt template selection."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    INCIDENT_ANALYSIS = "incident_analysis"
    LOG_ANALYSIS = "log_analysis"
    GENERAL_QUERY = "general_query"
    DOCUMENTATION = "documentation"
    CREATIVE_QUERY = "creative_query"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    UI_UX_DESIGN = "ui_ux_design"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"
    CREATIVE_BRAINSTORMING = "creative_brainstorming"


class PromptOptimizer:
    """Load and apply provider-specific prompt templates for better quality."""

    def __init__(self):
        self.templates: Dict[LLMProvider, Dict[str, Any]] = {}
        self.config_dir = Path(__file__).parent.parent.parent / "config" / "prompts"
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all provider-specific prompt templates from YAML files."""
        try:
            # Load Ollama templates
            ollama_path = self.config_dir / "ollama_templates.yaml"
            if ollama_path.exists():
                with open(ollama_path, "r") as f:
                    self.templates[LLMProvider.LOCAL] = yaml.safe_load(f)
                logger.info("ollama_templates_loaded", path=str(ollama_path))

            # Load Gemini templates
            gemini_path = self.config_dir / "gemini_templates.yaml"
            if gemini_path.exists():
                with open(gemini_path, "r") as f:
                    self.templates[LLMProvider.GEMINI] = yaml.safe_load(f)
                logger.info("gemini_templates_loaded", path=str(gemini_path))

            logger.info(
                "prompt_templates_loaded",
                providers=list(self.templates.keys()),
                total_templates=sum(
                    len(t.get("templates", {})) for t in self.templates.values()
                ),
            )

        except Exception as e:
            logger.error("failed_to_load_prompt_templates", error=str(e))
            # Continue with empty templates - graceful degradation

    def has_template(self, provider: LLMProvider, task_type: TaskType) -> bool:
        """Check if a template exists for provider and task type."""
        if provider not in self.templates:
            return False

        templates = self.templates[provider].get("templates", {})
        return task_type.value in templates

    def get_optimized_prompt(
        self,
        provider: LLMProvider,
        task_type: TaskType,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, str, Dict[str, Any]]:
        """Get optimized system and user prompts for provider and task.

        Args:
            provider: LLM provider
            task_type: Type of task
            user_message: Original user message
            context: Additional context for template variables

        Returns:
            Tuple of (system_prompt, user_prompt, parameters)
        """
        if not self.has_template(provider, task_type):
            # No template available - return defaults
            return self._get_default_prompts(user_message)

        try:
            template_data = self.templates[provider]["templates"][task_type.value]

            # Get system prompt
            system_prompt = template_data.get("system_prompt", "").strip()

            # Get user prompt template and populate with variables
            user_prompt_template = template_data.get(
                "user_prompt_template", "{query}"
            ).strip()

            # Prepare template variables
            template_vars = context or {}
            template_vars.setdefault("query", user_message)
            template_vars.setdefault("task_description", user_message)

            # Populate user prompt with variables
            user_prompt = self._populate_template(user_prompt_template, template_vars)

            # Get model-specific parameters
            parameters = template_data.get("parameters", {})

            logger.debug(
                "prompt_optimized",
                provider=provider,
                task_type=task_type,
                has_system_prompt=bool(system_prompt),
                template_vars=list(template_vars.keys()),
            )

            return system_prompt, user_prompt, parameters

        except Exception as e:
            logger.error(
                "prompt_optimization_failed",
                provider=provider,
                task_type=task_type,
                error=str(e),
            )
            return self._get_default_prompts(user_message)

    def _populate_template(
        self, template: str, variables: Dict[str, Any]
    ) -> str:
        """Populate template with variables using safe substitution."""
        try:
            # Simple string formatting with missing variables as empty strings
            result = template
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value or ""))

            # Remove any remaining unfilled placeholders
            import re
            result = re.sub(r"\{[^}]+\}", "", result)

            return result.strip()

        except Exception as e:
            logger.error("template_population_failed", error=str(e))
            return template

    def _get_default_prompts(self, user_message: str) -> tuple[str, str, Dict[str, Any]]:
        """Return default prompts when no template is available."""
        system_prompt = "You are a helpful AI assistant providing accurate and clear responses."
        user_prompt = user_message
        parameters = {"temperature": 0.7, "max_tokens": 2000}
        return system_prompt, user_prompt, parameters

    def detect_task_type(self, message: str) -> TaskType:
        """Detect task type from user message for automatic template selection.

        Args:
            message: User message

        Returns:
            Detected TaskType (defaults to GENERAL_QUERY)
        """
        message_lower = message.lower()

        # Code-related patterns
        if any(kw in message_lower for kw in ["write code", "implement", "function", "class", "generate code"]):
            return TaskType.CODE_GENERATION

        if any(kw in message_lower for kw in ["review code", "review this", "check code", "code review"]):
            return TaskType.CODE_REVIEW

        if any(kw in message_lower for kw in ["debug", "fix", "error", "bug", "not working"]):
            return TaskType.DEBUGGING

        # Incident and log analysis
        if any(kw in message_lower for kw in ["incident", "outage", "production issue", "root cause"]):
            return TaskType.INCIDENT_ANALYSIS

        if any(kw in message_lower for kw in ["analyze logs", "log analysis", "parse logs"]):
            return TaskType.LOG_ANALYSIS

        # Documentation and creative
        if any(kw in message_lower for kw in ["document", "write docs", "create documentation"]):
            return TaskType.DOCUMENTATION

        if any(kw in message_lower for kw in ["brainstorm", "ideas", "creative", "innovative"]):
            return TaskType.CREATIVE_BRAINSTORMING

        # UI/UX and design
        if any(kw in message_lower for kw in ["design ui", "user interface", "dashboard", "frontend"]):
            return TaskType.UI_UX_DESIGN

        # Data and reporting
        if any(kw in message_lower for kw in ["analyze data", "metrics", "data analysis", "trends"]):
            return TaskType.DATA_ANALYSIS

        if any(kw in message_lower for kw in ["generate report", "create report", "report on"]):
            return TaskType.REPORT_GENERATION

        # Prompt engineering
        if any(kw in message_lower for kw in ["optimize prompt", "improve prompt", "better prompt"]):
            return TaskType.PROMPT_OPTIMIZATION

        # Default to general query
        return TaskType.GENERAL_QUERY

    def get_model_preferences(
        self, provider: LLMProvider, task_type: TaskType
    ) -> List[str]:
        """Get preferred models for a provider and task type.

        Args:
            provider: LLM provider
            task_type: Type of task

        Returns:
            List of preferred model names (e.g., ["deepseek", "llama2"])
        """
        if provider not in self.templates:
            return []

        try:
            template_data = self.templates[provider]["templates"].get(task_type.value, {})
            return template_data.get("model_preferences", [])

        except Exception as e:
            logger.error(
                "failed_to_get_model_preferences",
                provider=provider,
                task_type=task_type,
                error=str(e),
            )
            return []

    def should_use_provider(
        self, provider: LLMProvider, task_type: TaskType
    ) -> bool:
        """Check if a provider should be used for a task type.

        Uses routing_recommendations from templates to determine
        if this provider is suitable for the task.

        Args:
            provider: LLM provider
            task_type: Type of task

        Returns:
            True if provider is recommended for this task
        """
        if provider not in self.templates:
            return True  # No restrictions if no template

        try:
            config = self.templates[provider]

            # Check "prefer" recommendations
            prefer = config.get("routing_recommendations", {}).get("prefer_gemini", [])
            if any(rec.get("task") == task_type.value for rec in prefer):
                return True

            # Check "avoid" recommendations
            avoid = config.get("routing_recommendations", {}).get("avoid_gemini", [])
            if any(rec.get("task") == task_type.value for rec in avoid):
                return False

            # No specific recommendation - allow
            return True

        except Exception as e:
            logger.error(
                "failed_to_check_provider_suitability",
                provider=provider,
                task_type=task_type,
                error=str(e),
            )
            return True  # Default to allowing


# Singleton instance
_prompt_optimizer: Optional[PromptOptimizer] = None


def get_prompt_optimizer() -> PromptOptimizer:
    """Get or create the global PromptOptimizer instance."""
    global _prompt_optimizer
    if _prompt_optimizer is None:
        _prompt_optimizer = PromptOptimizer()
    return _prompt_optimizer
