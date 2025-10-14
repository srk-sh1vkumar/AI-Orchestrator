"""
Cost Estimator Module - LLM Usage Cost Calculation

Calculates estimated costs based on token usage across different
LLM providers using current pricing models.
"""

from typing import Dict, Any, Tuple
import structlog

logger = structlog.get_logger()

# Pricing per 1K tokens (as of 2025)
# Format: (input_cost, output_cost) per 1K tokens in USD
PRICING_TABLE = {
    # OpenAI Models
    "gpt-4-turbo-preview": (0.01, 0.03),
    "gpt-4": (0.03, 0.06),
    "gpt-4-32k": (0.06, 0.12),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "gpt-3.5-turbo-16k": (0.001, 0.002),

    # Anthropic Claude Models
    "claude-3-opus-20240229": (0.015, 0.075),
    "claude-3-sonnet-20240229": (0.003, 0.015),
    "claude-3-haiku-20240307": (0.00025, 0.00125),
    "claude-2.1": (0.008, 0.024),
    "claude-2.0": (0.008, 0.024),

    # Google Gemini Models
    "gemini-pro": (0.0005, 0.0015),
    "gemini-pro-vision": (0.0005, 0.0015),
    "gemini-ultra": (0.01, 0.03),

    # Local models (free, but include compute costs)
    "llama2:13b": (0.0, 0.0),
    "llama2:70b": (0.0, 0.0),
    "mistral:7b": (0.0, 0.0),

    # Default fallback pricing
    "unknown": (0.002, 0.006)
}


def get_model_pricing(model_name: str) -> Tuple[float, float]:
    """
    Get pricing for a specific model.

    Args:
        model_name: Name/identifier of the LLM model

    Returns:
        Tuple of (input_cost_per_1k, output_cost_per_1k)
    """
    # Normalize model name
    model_lower = model_name.lower()

    # Direct match
    if model_name in PRICING_TABLE:
        return PRICING_TABLE[model_name]

    # Partial match for flexibility
    for key, pricing in PRICING_TABLE.items():
        if key.lower() in model_lower or model_lower in key.lower():
            return pricing

    # Default pricing
    logger.warning("model_pricing_unknown", model=model_name, using_default=True)
    return PRICING_TABLE["unknown"]


def calculate_token_cost(
    tokens: int,
    model: str,
    input_ratio: float = 0.6
) -> float:
    """
    Calculate cost for a given number of tokens.

    Assumes a mixed ratio of input/output tokens since we typically
    don't track them separately in simplified scenarios.

    Args:
        tokens: Total number of tokens
        model: Model name/identifier
        input_ratio: Ratio of input tokens (0.0-1.0), default 0.6

    Returns:
        Estimated cost in USD
    """
    input_cost_per_1k, output_cost_per_1k = get_model_pricing(model)

    # Split tokens into input and output
    input_tokens = tokens * input_ratio
    output_tokens = tokens * (1 - input_ratio)

    # Calculate costs
    input_cost = (input_tokens / 1000.0) * input_cost_per_1k
    output_cost = (output_tokens / 1000.0) * output_cost_per_1k

    total_cost = input_cost + output_cost

    logger.debug(
        "token_cost_calculated",
        model=model,
        tokens=tokens,
        input_tokens=int(input_tokens),
        output_tokens=int(output_tokens),
        cost_usd=round(total_cost, 6)
    )

    return total_cost


def calculate_costs(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate total costs from manifest token usage data.

    Reads token usage from monitoring data and applies pricing
    for each model to calculate estimated costs.

    Args:
        manifest: Project manifest dictionary

    Returns:
        Updated manifest with cost breakdown and total
    """
    if "token_usage" not in manifest.get("monitoring", {}):
        logger.warning("no_token_usage_data")
        manifest["monitoring"]["estimated_costs_usd"] = 0.0
        return manifest

    cost_breakdown = {}
    total_cost = 0.0

    # Calculate cost per agent/model
    for agent, data in manifest["monitoring"]["token_usage"].items():
        tokens = data.get("total_tokens", 0)
        model = data.get("model", "unknown")

        # Calculate cost
        cost = calculate_token_cost(tokens, model)
        cost_breakdown[agent] = {
            "model": model,
            "tokens": tokens,
            "cost_usd": round(cost, 6)
        }

        total_cost += cost

    # Update manifest
    manifest["monitoring"]["estimated_costs_usd"] = round(total_cost, 4)
    manifest["monitoring"]["cost_breakdown"] = cost_breakdown

    logger.info(
        "costs_calculated",
        total_cost_usd=round(total_cost, 4),
        agents=len(cost_breakdown)
    )

    return manifest


def print_cost_summary(manifest: Dict[str, Any]) -> None:
    """
    Print a formatted cost summary report.

    Args:
        manifest: Project manifest dictionary
    """
    print("\n" + "="*70)
    print("💰 COST ESTIMATION SUMMARY")
    print("="*70)

    if "cost_breakdown" not in manifest.get("monitoring", {}):
        print("No cost data available.")
        return

    cost_breakdown = manifest["monitoring"]["cost_breakdown"]
    total_cost = manifest["monitoring"]["estimated_costs_usd"]

    print("\n📊 Cost Breakdown by Agent/Model:\n")

    # Sort by cost (highest first)
    sorted_costs = sorted(
        cost_breakdown.items(),
        key=lambda x: x[1]["cost_usd"],
        reverse=True
    )

    for agent, data in sorted_costs:
        model = data["model"]
        tokens = data["tokens"]
        cost = data["cost_usd"]

        print(f"  • {agent:15s} [{model}]")
        print(f"    Tokens: {tokens:,} | Cost: ${cost:.6f}")

    print(f"\n{'─'*70}")
    print(f"  TOTAL ESTIMATED COST: ${total_cost:.4f} USD")
    print(f"{'─'*70}")

    # Cost efficiency metrics
    total_tokens = sum(d["tokens"] for d in cost_breakdown.values())
    if total_tokens > 0:
        avg_cost_per_1k = (total_cost / total_tokens) * 1000
        print(f"\n  📈 Average cost per 1K tokens: ${avg_cost_per_1k:.4f}")

    print("="*70)


def estimate_future_costs(
    total_tokens: int,
    model: str,
    requests_per_day: int = 100
) -> Dict[str, float]:
    """
    Estimate future costs based on projected usage.

    Args:
        total_tokens: Average tokens per request
        model: Model to use
        requests_per_day: Expected requests per day

    Returns:
        Dictionary with daily, weekly, and monthly cost estimates
    """
    cost_per_request = calculate_token_cost(total_tokens, model)

    estimates = {
        "cost_per_request": round(cost_per_request, 6),
        "daily": round(cost_per_request * requests_per_day, 2),
        "weekly": round(cost_per_request * requests_per_day * 7, 2),
        "monthly": round(cost_per_request * requests_per_day * 30, 2),
        "yearly": round(cost_per_request * requests_per_day * 365, 2)
    }

    return estimates


def compare_model_costs(tokens: int) -> Dict[str, float]:
    """
    Compare costs across different models for the same token count.

    Useful for cost optimization decisions.

    Args:
        tokens: Number of tokens to compare

    Returns:
        Dictionary mapping model names to estimated costs
    """
    comparison = {}

    # Compare popular models
    models_to_compare = [
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "gemini-pro"
    ]

    for model in models_to_compare:
        cost = calculate_token_cost(tokens, model)
        comparison[model] = round(cost, 6)

    return comparison


if __name__ == "__main__":
    # Test cost estimation
    print("Testing Cost Estimator Module\n")

    # Create test manifest
    test_manifest = {
        "monitoring": {
            "token_usage": {
                "claude": {
                    "total_tokens": 2500,
                    "model": "claude-3-sonnet-20240229"
                },
                "chatgpt": {
                    "total_tokens": 1800,
                    "model": "gpt-4-turbo-preview"
                },
                "gemini": {
                    "total_tokens": 1500,
                    "model": "gemini-pro"
                },
                "local": {
                    "total_tokens": 2000,
                    "model": "llama2:13b"
                }
            }
        }
    }

    # Calculate costs
    test_manifest = calculate_costs(test_manifest)

    # Print summary
    print_cost_summary(test_manifest)

    # Future cost estimation
    print("\n📊 Future Cost Projections:")
    print(f"Based on 100 requests/day with 2000 tokens average (GPT-4 Turbo)")
    projections = estimate_future_costs(2000, "gpt-4-turbo-preview", 100)
    print(f"  Daily:   ${projections['daily']}")
    print(f"  Weekly:  ${projections['weekly']}")
    print(f"  Monthly: ${projections['monthly']}")
    print(f"  Yearly:  ${projections['yearly']}")

    # Model comparison
    print("\n🔍 Model Cost Comparison (2000 tokens):")
    comparison = compare_model_costs(2000)
    for model, cost in sorted(comparison.items(), key=lambda x: x[1]):
        print(f"  {model:30s} → ${cost:.6f}")
