"""Cost calculation for LLM provider requests.

Enhancement 007: Cost Tracking & Budget Alerts
- Token-based pricing for each provider
- Accurate cost calculation within $0.01
- Support for multiple models per provider
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class ModelPricing(Enum):
    """Pricing tiers for different models (USD per 1M tokens)."""

    # OpenAI GPT-4o (January 2025 pricing)
    GPT4O_INPUT = 2.50
    GPT4O_OUTPUT = 10.00

    # OpenAI GPT-4o-mini (January 2025 pricing)
    GPT4O_MINI_INPUT = 0.15
    GPT4O_MINI_OUTPUT = 0.60

    # OpenAI GPT-4-turbo (January 2025 pricing)
    GPT4_TURBO_INPUT = 10.00
    GPT4_TURBO_OUTPUT = 30.00

    # Anthropic Claude 3.5 Sonnet (January 2025 pricing)
    CLAUDE_35_SONNET_INPUT = 3.00
    CLAUDE_35_SONNET_OUTPUT = 15.00

    # Anthropic Claude 3 Haiku (January 2025 pricing)
    CLAUDE_3_HAIKU_INPUT = 0.25
    CLAUDE_3_HAIKU_OUTPUT = 1.25

    # Anthropic Claude 3 Opus (January 2025 pricing)
    CLAUDE_3_OPUS_INPUT = 15.00
    CLAUDE_3_OPUS_OUTPUT = 75.00

    # Google Gemini 1.5 Pro (January 2025 pricing)
    GEMINI_15_PRO_INPUT = 1.25
    GEMINI_15_PRO_OUTPUT = 5.00

    # Google Gemini 1.5 Flash (January 2025 pricing)
    GEMINI_15_FLASH_INPUT = 0.075
    GEMINI_15_FLASH_OUTPUT = 0.30

    # Local LLMs (free)
    LOCAL_INPUT = 0.0
    LOCAL_OUTPUT = 0.0


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a request."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    pricing_tier: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "input_cost": round(self.input_cost, 4),
            "output_cost": round(self.output_cost, 4),
            "total_cost": round(self.total_cost, 4),
            "pricing_tier": self.pricing_tier,
        }


class CostCalculator:
    """Calculate costs for LLM requests based on provider and model."""

    # Provider-to-model mapping (default models)
    DEFAULT_MODELS = {
        "chatgpt": "gpt-4o",
        "claude": "claude-3-5-sonnet-20241022",
        "claude_code": "claude-3-5-sonnet-20241022",  # Uses Claude API
        "gemini": "gemini-1.5-pro",
        "local": "local-model",
        "deepseek": "deepseek-coder-6.7b",
        "mistral": "mistral-7b",
        "llama2": "llama2-7b",
        "codellama": "codellama-7b",
    }

    # Model pricing configuration
    # Format: {model_name: (input_price_per_1M, output_price_per_1M)}
    MODEL_PRICING: Dict[str, Tuple[float, float]] = {
        # OpenAI models
        "gpt-4o": (ModelPricing.GPT4O_INPUT.value, ModelPricing.GPT4O_OUTPUT.value),
        "gpt-4o-mini": (ModelPricing.GPT4O_MINI_INPUT.value, ModelPricing.GPT4O_MINI_OUTPUT.value),
        "gpt-4-turbo": (ModelPricing.GPT4_TURBO_INPUT.value, ModelPricing.GPT4_TURBO_OUTPUT.value),
        "gpt-4-turbo-preview": (ModelPricing.GPT4_TURBO_INPUT.value, ModelPricing.GPT4_TURBO_OUTPUT.value),

        # Anthropic models
        "claude-3-5-sonnet-20241022": (ModelPricing.CLAUDE_35_SONNET_INPUT.value, ModelPricing.CLAUDE_35_SONNET_OUTPUT.value),
        "claude-3-5-sonnet": (ModelPricing.CLAUDE_35_SONNET_INPUT.value, ModelPricing.CLAUDE_35_SONNET_OUTPUT.value),
        "claude-3-haiku-20240307": (ModelPricing.CLAUDE_3_HAIKU_INPUT.value, ModelPricing.CLAUDE_3_HAIKU_OUTPUT.value),
        "claude-3-haiku": (ModelPricing.CLAUDE_3_HAIKU_INPUT.value, ModelPricing.CLAUDE_3_HAIKU_OUTPUT.value),
        "claude-3-opus-20240229": (ModelPricing.CLAUDE_3_OPUS_INPUT.value, ModelPricing.CLAUDE_3_OPUS_OUTPUT.value),
        "claude-3-opus": (ModelPricing.CLAUDE_3_OPUS_INPUT.value, ModelPricing.CLAUDE_3_OPUS_OUTPUT.value),

        # Google models
        "gemini-1.5-pro": (ModelPricing.GEMINI_15_PRO_INPUT.value, ModelPricing.GEMINI_15_PRO_OUTPUT.value),
        "gemini-1.5-flash": (ModelPricing.GEMINI_15_FLASH_INPUT.value, ModelPricing.GEMINI_15_FLASH_OUTPUT.value),
        "gemini-pro": (ModelPricing.GEMINI_15_PRO_INPUT.value, ModelPricing.GEMINI_15_PRO_OUTPUT.value),

        # Local models (free)
        "local-model": (ModelPricing.LOCAL_INPUT.value, ModelPricing.LOCAL_OUTPUT.value),
        "deepseek-coder-6.7b": (ModelPricing.LOCAL_INPUT.value, ModelPricing.LOCAL_OUTPUT.value),
        "mistral-7b": (ModelPricing.LOCAL_INPUT.value, ModelPricing.LOCAL_OUTPUT.value),
        "llama2-7b": (ModelPricing.LOCAL_INPUT.value, ModelPricing.LOCAL_OUTPUT.value),
        "codellama-7b": (ModelPricing.LOCAL_INPUT.value, ModelPricing.LOCAL_OUTPUT.value),
    }

    @classmethod
    def get_model_for_provider(cls, provider: str, model: Optional[str] = None) -> str:
        """Get the model name for a provider.

        Args:
            provider: Provider identifier
            model: Optional model override

        Returns:
            Model name
        """
        if model:
            return model
        return cls.DEFAULT_MODELS.get(provider.lower(), "unknown")

    @classmethod
    def get_pricing(cls, model: str) -> Tuple[float, float]:
        """Get pricing for a model.

        Args:
            model: Model identifier

        Returns:
            Tuple of (input_price_per_1M, output_price_per_1M)
        """
        # Try exact match
        if model in cls.MODEL_PRICING:
            return cls.MODEL_PRICING[model]

        # Try partial match (e.g., "gpt-4o-2024-05-13" -> "gpt-4o")
        for model_key in cls.MODEL_PRICING:
            if model.startswith(model_key):
                return cls.MODEL_PRICING[model_key]

        # Default to GPT-4o pricing if unknown (conservative estimate)
        logger.warning("unknown_model_pricing", model=model, using_default="gpt-4o")
        return cls.MODEL_PRICING["gpt-4o"]

    @classmethod
    def calculate_cost(
        cls,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None,
    ) -> CostBreakdown:
        """Calculate cost for a request.

        Args:
            provider: Provider identifier (e.g., "chatgpt", "claude")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Optional model identifier (if not provided, uses default for provider)

        Returns:
            CostBreakdown with detailed cost information
        """
        # Determine model
        model_name = cls.get_model_for_provider(provider, model)

        # Get pricing
        input_price_per_1m, output_price_per_1m = cls.get_pricing(model_name)

        # Calculate costs (divide by 1,000,000 to get cost from per-million pricing)
        input_cost = (input_tokens / 1_000_000) * input_price_per_1m
        output_cost = (output_tokens / 1_000_000) * output_price_per_1m
        total_cost = input_cost + output_cost

        # Round to 4 decimal places for accuracy
        input_cost = round(input_cost, 4)
        output_cost = round(output_cost, 4)
        total_cost = round(total_cost, 4)

        # Determine pricing tier
        if total_cost == 0:
            pricing_tier = "free"
        elif total_cost < 0.001:
            pricing_tier = "ultra_low"
        elif total_cost < 0.01:
            pricing_tier = "low"
        elif total_cost < 0.10:
            pricing_tier = "medium"
        else:
            pricing_tier = "high"

        breakdown = CostBreakdown(
            provider=provider,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            pricing_tier=pricing_tier,
        )

        logger.info(
            "cost_calculated",
            provider=provider,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=total_cost,
            pricing_tier=pricing_tier,
        )

        return breakdown

    @classmethod
    def estimate_cost(
        cls,
        provider: str,
        estimated_tokens: int,
        model: Optional[str] = None,
        input_output_ratio: float = 0.7,
    ) -> CostBreakdown:
        """Estimate cost before making a request.

        Args:
            provider: Provider identifier
            estimated_tokens: Total estimated tokens
            model: Optional model identifier
            input_output_ratio: Ratio of input to total tokens (default 0.7 = 70% input, 30% output)

        Returns:
            CostBreakdown with estimated cost
        """
        # Split tokens based on ratio
        input_tokens = int(estimated_tokens * input_output_ratio)
        output_tokens = estimated_tokens - input_tokens

        return cls.calculate_cost(provider, input_tokens, output_tokens, model)

    @classmethod
    def get_cheapest_provider(
        cls,
        input_tokens: int,
        output_tokens: int,
        providers: Optional[list] = None,
    ) -> Tuple[str, float]:
        """Find the cheapest provider for a given token count.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            providers: Optional list of providers to consider (default: all)

        Returns:
            Tuple of (cheapest_provider, cost)
        """
        if providers is None:
            providers = list(cls.DEFAULT_MODELS.keys())

        costs = {}
        for provider in providers:
            breakdown = cls.calculate_cost(provider, input_tokens, output_tokens)
            costs[provider] = breakdown.total_cost

        # Find minimum cost
        cheapest = min(costs.items(), key=lambda x: x[1])

        logger.info(
            "cheapest_provider_calculated",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=cheapest[0],
            cost=cheapest[1],
            all_costs=costs,
        )

        return cheapest

    @classmethod
    def compare_providers(
        cls,
        input_tokens: int,
        output_tokens: int,
    ) -> Dict[str, CostBreakdown]:
        """Compare costs across all providers.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dictionary mapping provider to CostBreakdown
        """
        comparisons = {}
        for provider in cls.DEFAULT_MODELS.keys():
            comparisons[provider] = cls.calculate_cost(provider, input_tokens, output_tokens)

        return comparisons
