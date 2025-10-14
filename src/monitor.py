"""
Monitoring Module - LLM Health and Token Usage Tracking

Provides monitoring capabilities for LLM providers, tracks token usage,
and checks the health of local and remote AI models.
"""

import random
import time
from datetime import datetime
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


def log_token_usage(
    agent_name: str,
    tokens_used: int,
    manifest: Dict[str, Any],
    model: str = "unknown"
) -> Dict[str, Any]:
    """
    Log token usage for an agent execution.

    Tracks tokens consumed by each agent and updates the manifest
    with usage statistics and timestamps.

    Args:
        agent_name: Name of the agent (e.g., 'claude', 'chatgpt')
        tokens_used: Number of tokens consumed
        manifest: Project manifest dictionary
        model: Model name/identifier

    Returns:
        Updated manifest with token usage data
    """
    timestamp = datetime.utcnow().isoformat()

    # Initialize token usage tracking if not present
    if "token_usage" not in manifest["monitoring"]:
        manifest["monitoring"]["token_usage"] = {}

    # Add or update agent token usage
    if agent_name not in manifest["monitoring"]["token_usage"]:
        manifest["monitoring"]["token_usage"][agent_name] = {
            "total_tokens": 0,
            "requests": [],
            "model": model
        }

    # Log this request
    manifest["monitoring"]["token_usage"][agent_name]["total_tokens"] += tokens_used
    manifest["monitoring"]["token_usage"][agent_name]["requests"].append({
        "tokens": tokens_used,
        "timestamp": timestamp
    })

    logger.info(
        "token_usage_logged",
        agent=agent_name,
        tokens=tokens_used,
        model=model,
        timestamp=timestamp
    )

    return manifest


def check_local_llm_health(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check health status of local LLM deployment.

    Simulates a health check ping to a local model (e.g., Ollama)
    and records latency and availability metrics.

    Args:
        manifest: Project manifest dictionary

    Returns:
        Updated manifest with LLM health status
    """
    # Simulate health check with random latency
    start_time = time.time()

    # Simulate health check request (random success/latency)
    is_healthy = random.choice([True, True, True, False])  # 75% success rate
    latency_ms = random.randint(50, 500) if is_healthy else 0

    # Simulate actual delay
    time.sleep(latency_ms / 1000.0)

    end_time = time.time()
    actual_latency = (end_time - start_time) * 1000  # Convert to ms

    # Update manifest
    manifest["monitoring"]["local_llm_status"] = {
        "healthy": is_healthy,
        "latency_ms": round(actual_latency, 2),
        "model": "llama2:13b",  # Example local model
        "endpoint": "http://localhost:11434",
        "last_checked": datetime.utcnow().isoformat(),
        "status_code": 200 if is_healthy else 503
    }

    status_emoji = "✅" if is_healthy else "❌"
    logger.info(
        "local_llm_health_check",
        healthy=is_healthy,
        latency_ms=round(actual_latency, 2),
        model="llama2:13b"
    )

    print(f"{status_emoji} Local LLM Health: {'Healthy' if is_healthy else 'Unhealthy'} "
          f"(latency: {round(actual_latency, 2)}ms)")

    return manifest


def simulate_agent_token_usage(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate token usage for all agents in the workflow.

    Generates realistic token usage patterns for demonstration purposes.

    Args:
        manifest: Project manifest dictionary

    Returns:
        Updated manifest with simulated token usage
    """
    # Token usage patterns for different agents
    agent_token_ranges = {
        "claude": (1200, 2500, "claude-3-sonnet-20240229"),
        "claude_code": (1500, 3000, "claude-3-opus-20240229"),
        "chatgpt": (800, 1800, "gpt-4-turbo-preview"),
        "gemini": (900, 1600, "gemini-pro"),
        "local": (1000, 2000, "llama2:13b")
    }

    for agent, (min_tokens, max_tokens, model) in agent_token_ranges.items():
        tokens = random.randint(min_tokens, max_tokens)
        manifest = log_token_usage(agent, tokens, manifest, model)

    return manifest


def print_monitoring_summary(manifest: Dict[str, Any]) -> None:
    """
    Print a formatted summary of monitoring metrics.

    Displays token usage, LLM health, and cost estimates in a
    readable format.

    Args:
        manifest: Project manifest dictionary
    """
    print("\n" + "="*70)
    print("📊 MONITORING SUMMARY")
    print("="*70)

    # Token usage summary
    if "token_usage" in manifest["monitoring"]:
        print("\n🔢 Token Usage by Agent:")
        total_tokens = 0
        for agent, data in manifest["monitoring"]["token_usage"].items():
            tokens = data["total_tokens"]
            total_tokens += tokens
            requests = len(data["requests"])
            model = data.get("model", "unknown")
            print(f"  • {agent:15s} → {tokens:,} tokens ({requests} requests) [{model}]")

        print(f"\n  Total Tokens: {total_tokens:,}")

    # LLM health status
    if "local_llm_status" in manifest["monitoring"]:
        print("\n🏥 Local LLM Health:")
        health = manifest["monitoring"]["local_llm_status"]
        status = "✅ Healthy" if health["healthy"] else "❌ Unhealthy"
        print(f"  Status: {status}")
        print(f"  Latency: {health['latency_ms']}ms")
        print(f"  Model: {health['model']}")
        print(f"  Endpoint: {health['endpoint']}")
        print(f"  Last Checked: {health['last_checked']}")

    # Cost estimate (if available)
    if "estimated_costs_usd" in manifest["monitoring"]:
        cost = manifest["monitoring"]["estimated_costs_usd"]
        if cost > 0:
            print(f"\n💰 Estimated Costs: ${cost:.4f} USD")

    print("="*70)


def get_monitoring_metrics(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract monitoring metrics in a structured format for API export.

    Args:
        manifest: Project manifest dictionary

    Returns:
        Dictionary containing all monitoring metrics
    """
    metrics = {
        "token_usage": manifest["monitoring"].get("token_usage", {}),
        "local_llm_status": manifest["monitoring"].get("local_llm_status", {}),
        "estimated_costs_usd": manifest["monitoring"].get("estimated_costs_usd", 0.0),
        "timestamp": datetime.utcnow().isoformat()
    }

    # Calculate aggregate metrics
    total_tokens = sum(
        data["total_tokens"]
        for data in metrics["token_usage"].values()
    )

    total_requests = sum(
        len(data["requests"])
        for data in metrics["token_usage"].values()
    )

    metrics["aggregates"] = {
        "total_tokens": total_tokens,
        "total_requests": total_requests,
        "agents_tracked": len(metrics["token_usage"])
    }

    return metrics


if __name__ == "__main__":
    # Test monitoring functions
    print("Testing Monitoring Module\n")

    # Create test manifest
    test_manifest = {
        "monitoring": {
            "token_usage": {},
            "local_llm_status": {}
        }
    }

    # Test token logging
    print("Testing token usage logging...")
    test_manifest = log_token_usage("claude", 1500, test_manifest, "claude-3-sonnet")
    test_manifest = log_token_usage("chatgpt", 1200, test_manifest, "gpt-4-turbo")

    # Test LLM health check
    print("\nTesting local LLM health check...")
    test_manifest = check_local_llm_health(test_manifest)

    # Print summary
    print_monitoring_summary(test_manifest)

    # Get structured metrics
    print("\n📊 Structured Metrics:")
    metrics = get_monitoring_metrics(test_manifest)
    print(f"Total Tokens: {metrics['aggregates']['total_tokens']}")
    print(f"Total Requests: {metrics['aggregates']['total_requests']}")
