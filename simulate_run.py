"""
Simulation Harness - End-to-End Orchestrator Execution

Runs the complete orchestrator workflow including all phases:
- Multi-agent orchestration
- Monitoring and health checks
- Cost estimation
- Telemetry logging
- Self-development tracking

Saves final manifest and displays comprehensive summary.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_orchestrator import (
    initialize_project_context,
    agent_design_architecture,
    agent_code_generation,
    agent_deployment_ci
)
from monitor import (
    simulate_agent_token_usage,
    check_local_llm_health,
    print_monitoring_summary
)
from cost_estimator import calculate_costs, print_cost_summary
from telemetry_logger import get_telemetry_logger
from self_dev_agent import agent_self_development


def run_complete_simulation():
    """
    Execute complete orchestrator simulation with all phases.

    This demonstrates the full capability of the DevAI Orchestrator:
    - Multi-agent workflow
    - Token usage tracking
    - Cost estimation
    - LLM health monitoring
    - Structured logging
    - Self-development tracking
    """
    print("\n" + "="*80)
    print("🚀 DEVAI ORCHESTRATOR - COMPLETE SIMULATION")
    print("="*80)
    print("Executing full orchestrator workflow with monitoring and self-development\n")

    # Initialize telemetry logger
    tel = get_telemetry_logger()

    # PHASE 1: Initialize project context
    print("Initializing project context...")
    manifest = initialize_project_context()

    # PHASE 2: Run multi-agent orchestration workflow
    print("\n" + "─"*80)
    print("STAGE 1: Multi-Agent Orchestration Workflow")
    print("─"*80)

    manifest = agent_design_architecture(manifest)
    tel.log_agent_execution(
        agent="Claude",
        phase="Architecture Design",
        tokens_used=1850,
        model="claude-3-sonnet-20240229",
        status="success"
    )

    manifest = agent_code_generation(manifest)
    tel.log_agent_execution(
        agent="Claude Code",
        phase="Code Generation",
        tokens_used=2750,
        model="claude-3-opus-20240229",
        status="success"
    )

    manifest = agent_deployment_ci(manifest)
    tel.log_agent_execution(
        agent="Claude Code",
        phase="Deployment & CI/CD",
        tokens_used=1980,
        model="claude-3-opus-20240229",
        status="success"
    )

    # PHASE 3: Monitoring & Token Usage
    print("\n" + "─"*80)
    print("STAGE 2: Monitoring & Health Checks")
    print("─"*80)

    # Simulate token usage for all agents
    manifest = simulate_agent_token_usage(manifest)

    # Check local LLM health
    print("\nChecking local LLM health...")
    manifest = check_local_llm_health(manifest)

    # PHASE 4: Cost Estimation
    print("\n" + "─"*80)
    print("STAGE 3: Cost Estimation")
    print("─"*80)

    manifest = calculate_costs(manifest)
    print_cost_summary(manifest)

    # Log costs
    tel.log_cost_calculation(
        total_cost=manifest["monitoring"]["estimated_costs_usd"],
        breakdown=manifest["monitoring"]["cost_breakdown"]
    )

    # PHASE 5: Self-Development Tracking
    print("\n" + "─"*80)
    print("STAGE 4: Self-Development Tracking")
    print("─"*80)

    manifest = agent_self_development(manifest)

    # Log self-dev update
    metrics = manifest["self_development"]["metrics"]
    tel.log_self_dev_update(
        learning_hours=metrics["learning_hours"],
        goals_updated=len(manifest["self_development"]["goals"]),
        reflection=manifest["self_development"]["reflections"][-1]["content"] if manifest["self_development"]["reflections"] else None
    )

    # FINAL: Print comprehensive summary
    print("\n" + "="*80)
    print("📊 SIMULATION COMPLETE - FINAL SUMMARY")
    print("="*80)

    # Token metrics
    total_tokens = sum(
        data["total_tokens"]
        for data in manifest["monitoring"]["token_usage"].values()
    )
    total_requests = sum(
        len(data["requests"])
        for data in manifest["monitoring"]["token_usage"].values()
    )

    print(f"\n🔢 Token Usage Summary:")
    print(f"  Total Tokens: {total_tokens:,}")
    print(f"  Total Requests: {total_requests}")
    print(f"  Agents Tracked: {len(manifest['monitoring']['token_usage'])}")

    # Cost metrics
    print(f"\n💰 Cost Summary:")
    print(f"  Total Estimated Cost: ${manifest['monitoring']['estimated_costs_usd']:.4f} USD")

    # Workflow metrics
    print(f"\n🔄 Workflow Summary:")
    print(f"  Phases Completed: {len(manifest['workflow']['phases_completed'])}")
    print(f"  Current Phase: {manifest['workflow']['current_phase']}")

    # Self-development metrics
    self_dev_metrics = manifest["self_development"]["metrics"]
    print(f"\n🌱 Self-Development Summary:")
    print(f"  Learning Hours: {self_dev_metrics['learning_hours']} hours")
    print(f"  Skills Gained: {len(self_dev_metrics['skills_gained'])}")
    print(f"  Milestones: {len(manifest['self_development']['milestones'])}")
    print(f"  Reflections: {len(manifest['self_development']['reflections'])}")
    print(f"  Goals Completed: {sum(1 for g in manifest['self_development']['goals'] if g['status'] == 'Completed')}/{len(manifest['self_development']['goals'])}")

    # LLM Health
    llm_health = manifest["monitoring"]["local_llm_status"]
    health_emoji = "✅" if llm_health["healthy"] else "❌"
    print(f"\n🏥 LLM Health:")
    print(f"  Status: {health_emoji} {'Healthy' if llm_health['healthy'] else 'Unhealthy'}")
    print(f"  Latency: {llm_health['latency_ms']}ms")
    print(f"  Model: {llm_health['model']}")

    # Print monitoring summary
    print_monitoring_summary(manifest)

    # Save manifest to file
    print("\n" + "─"*80)
    print("💾 Saving state...")

    manifest_path = Path("manifest_state.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"✅ Manifest saved to: {manifest_path.absolute()}")

    # Save compact summary
    summary_path = Path("orchestrator_summary.json")
    summary = {
        "execution_timestamp": manifest["project"]["created_at"],
        "total_tokens": total_tokens,
        "estimated_cost_usd": manifest["monitoring"]["estimated_costs_usd"],
        "phases_completed": len(manifest["workflow"]["phases_completed"]),
        "learning_hours": self_dev_metrics["learning_hours"],
        "skills_gained": len(self_dev_metrics["skills_gained"]),
        "goals_status": {
            "total": len(manifest["self_development"]["goals"]),
            "completed": sum(1 for g in manifest["self_development"]["goals"] if g["status"] == "Completed"),
            "in_progress": sum(1 for g in manifest["self_development"]["goals"] if g["status"] == "In Progress")
        }
    }

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Summary saved to: {summary_path.absolute()}")

    print(f"\n📁 Log files written to: logs/")
    print(f"  - orchestrator.log (main events)")
    print(f"  - agents.log (agent executions)")
    print(f"  - errors.log (error tracking)")

    print("\n" + "="*80)
    print("🎉 Simulation completed successfully!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Start API server: cd api && python server.py")
    print("  2. View metrics: http://localhost:8002/metrics")
    print("  3. Check status: http://localhost:8002/status")
    print("  4. Growth data: http://localhost:8002/growth")
    print("  5. API docs: http://localhost:8002/docs")
    print("  6. Dashboard: cd dashboard && streamlit run dashboard.py")

    return manifest


if __name__ == "__main__":
    try:
        final_manifest = run_complete_simulation()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Simulation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
