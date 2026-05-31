"""LLM Provider Pricing Configuration.

Pricing as of January 2025. Costs are per 1,000 tokens.
Update these values as provider pricing changes.
"""

from typing import Dict, Optional


# Pricing per 1K tokens (in USD)
PROVIDER_COSTS = {
    "chatgpt": {
        "model": "gpt-3.5-turbo",
        "input_cost_per_1k": 0.0015,   # $0.0015 per 1K input tokens
        "output_cost_per_1k": 0.002,   # $0.002 per 1K output tokens
        "average_cost_per_1k": 0.00175,  # Average for mixed usage
    },
    "claude": {
        "model": "claude-3-5-sonnet-20241022",
        "input_cost_per_1k": 0.003,    # $0.003 per 1K input tokens
        "output_cost_per_1k": 0.015,   # $0.015 per 1K output tokens
        "average_cost_per_1k": 0.009,  # Average for mixed usage
    },
    "claude_code": {
        "model": "claude-3-5-sonnet-20241022",
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
        "average_cost_per_1k": 0.009,
    },
    "gemini": {
        "model": "gemini-2.0-flash-exp",
        "input_cost_per_1k": 0.0,      # Free tier (up to quota)
        "output_cost_per_1k": 0.0,
        "average_cost_per_1k": 0.0,
        "paid_input_cost_per_1k": 0.00025,   # After quota
        "paid_output_cost_per_1k": 0.0005,
    },
    "local": {
        "model": "llama2/mistral/codellama",
        "input_cost_per_1k": 0.0,      # Free (self-hosted)
        "output_cost_per_1k": 0.0,
        "average_cost_per_1k": 0.0,
    },
    "deepseek": {
        "model": "deepseek-coder",
        "input_cost_per_1k": 0.0,      # Free (self-hosted via Ollama)
        "output_cost_per_1k": 0.0,
        "average_cost_per_1k": 0.0,
    },
}


def calculate_cost(provider: str, total_tokens: int,
                   input_tokens: Optional[int] = None,
                   output_tokens: Optional[int] = None) -> float:
    """Calculate cost for LLM usage.

    Args:
        provider: Provider name (chatgpt, claude, gemini, local, etc.)
        total_tokens: Total tokens used
        input_tokens: Optional input tokens for precise calculation
        output_tokens: Optional output tokens for precise calculation

    Returns:
        Cost in USD
    """
    if provider not in PROVIDER_COSTS:
        return 0.0

    pricing = PROVIDER_COSTS[provider]

    # If we have input/output breakdown, calculate precisely
    if input_tokens is not None and output_tokens is not None:
        input_cost = (input_tokens / 1000) * pricing.get("input_cost_per_1k", 0.0)
        output_cost = (output_tokens / 1000) * pricing.get("output_cost_per_1k", 0.0)
        return input_cost + output_cost

    # Otherwise use average cost
    average_cost_per_1k = pricing.get("average_cost_per_1k", 0.0)
    return (total_tokens / 1000) * average_cost_per_1k


def get_provider_info(provider: str) -> Dict[str, any]:
    """Get pricing information for a provider.

    Args:
        provider: Provider name

    Returns:
        Dictionary with model and pricing information
    """
    return PROVIDER_COSTS.get(provider, {
        "model": "unknown",
        "input_cost_per_1k": 0.0,
        "output_cost_per_1k": 0.0,
        "average_cost_per_1k": 0.0,
    })
