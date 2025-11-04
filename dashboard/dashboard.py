"""
Streamlit Dashboard - DevAI Orchestrator

Interactive dashboard for monitoring orchestrator status,
token usage, costs, and self-development progress.
"""

import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Page config
st.set_page_config(
    page_title="DevAI Orchestrator Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-metric {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4a90e2;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
    }
    .status-healthy {
        color: #50c878;
        font-weight: bold;
    }
    .status-unhealthy {
        color: #e74c3c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=5)
def load_manifest():
    """Load manifest state from file."""
    manifest_path = Path("manifest_state.json")

    if not manifest_path.exists():
        return None

    with open(manifest_path, 'r') as f:
        return json.load(f)


def create_token_usage_chart(manifest):
    """Create token usage bar chart."""
    if "token_usage" not in manifest.get("monitoring", {}):
        return None

    token_data = manifest["monitoring"]["token_usage"]

    agents = list(token_data.keys())
    tokens = [data["total_tokens"] for data in token_data.values()]
    models = [data.get("model", "unknown") for data in token_data.values()]

    fig = go.Figure(data=[
        go.Bar(
            x=agents,
            y=tokens,
            text=tokens,
            textposition='auto',
            marker=dict(
                color=['#4a90e2', '#50c878', '#f39c12', '#9b59b6', '#e74c3c'][:len(agents)]
            ),
            hovertemplate='<b>%{x}</b><br>Tokens: %{y:,}<br>Model: %{customdata}<extra></extra>',
            customdata=models
        )
    ])

    fig.update_layout(
        title="Token Usage by Agent",
        xaxis_title="Agent",
        yaxis_title="Tokens Used",
        height=400,
        showlegend=False
    )

    return fig


def create_cost_breakdown_chart(manifest):
    """Create cost breakdown pie chart."""
    if "cost_breakdown" not in manifest.get("monitoring", {}):
        return None

    cost_data = manifest["monitoring"]["cost_breakdown"]

    agents = list(cost_data.keys())
    costs = [data["cost_usd"] for data in cost_data.values()]

    fig = go.Figure(data=[
        go.Pie(
            labels=agents,
            values=costs,
            hole=0.3,
            marker=dict(
                colors=['#4a90e2', '#50c878', '#f39c12', '#9b59b6', '#e74c3c']
            )
        )
    ])

    fig.update_layout(
        title="Cost Distribution by Agent",
        height=400
    )

    return fig


def create_goals_progress_chart(manifest):
    """Create goals progress chart."""
    if "self_development" not in manifest:
        return None

    goals = manifest["self_development"].get("goals", [])

    if not goals:
        return None

    titles = [g["title"] for g in goals]
    progress = [g.get("progress", 0) for g in goals]
    statuses = [g.get("status", "Unknown") for g in goals]

    # Color mapping
    color_map = {
        "Completed": "#50c878",
        "In Progress": "#4a90e2",
        "Planned": "#95a5a6"
    }
    colors = [color_map.get(s, "#95a5a6") for s in statuses]

    fig = go.Figure(data=[
        go.Bar(
            y=titles,
            x=progress,
            orientation='h',
            text=[f"{p}%" for p in progress],
            textposition='inside',
            marker=dict(color=colors),
            hovertemplate='<b>%{y}</b><br>Progress: %{x}%<br>Status: %{customdata}<extra></extra>',
            customdata=statuses
        )
    ])

    fig.update_layout(
        title="Goal Progress",
        xaxis_title="Progress (%)",
        height=300,
        xaxis=dict(range=[0, 100]),
        showlegend=False
    )

    return fig


def system_status_tab(manifest):
    """Render system status tab."""
    st.header("📊 System Status")

    if manifest is None:
        st.warning("⚠️ No manifest data available. Run `python simulate_run.py` first.")
        return

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    # Token usage
    total_tokens = sum(
        data.get("total_tokens", 0)
        for data in manifest.get("monitoring", {}).get("token_usage", {}).values()
    )

    with col1:
        st.metric("Total Tokens", f"{total_tokens:,}")

    # Estimated cost
    with col2:
        cost = manifest.get("monitoring", {}).get("estimated_costs_usd", 0.0)
        st.metric("Estimated Cost", f"${cost:.4f}")

    # Phases completed
    with col3:
        phases = len(manifest.get("workflow", {}).get("phases_completed", []))
        st.metric("Phases Completed", phases)

    # LLM Health
    with col4:
        llm_health = manifest.get("monitoring", {}).get("local_llm_status", {})
        healthy = llm_health.get("healthy", False)
        health_text = "✅ Healthy" if healthy else "❌ Unhealthy"
        st.metric("LLM Health", health_text)

    st.divider()

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        # Token usage chart
        token_chart = create_token_usage_chart(manifest)
        if token_chart:
            st.plotly_chart(token_chart, use_container_width=True)

    with col2:
        # Cost breakdown chart
        cost_chart = create_cost_breakdown_chart(manifest)
        if cost_chart:
            st.plotly_chart(cost_chart, use_container_width=True)

    st.divider()

    # Detailed metrics
    st.subheader("📈 Detailed Metrics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Token Usage by Agent**")
        token_usage = manifest.get("monitoring", {}).get("token_usage", {})
        for agent, data in token_usage.items():
            st.write(f"- **{agent}**: {data['total_tokens']:,} tokens ({data.get('model', 'unknown')})")

    with col2:
        st.markdown("**LLM Health Status**")
        llm_status = manifest.get("monitoring", {}).get("local_llm_status", {})
        if llm_status:
            st.write(f"- **Model**: {llm_status.get('model', 'N/A')}")
            st.write(f"- **Endpoint**: {llm_status.get('endpoint', 'N/A')}")
            st.write(f"- **Latency**: {llm_status.get('latency_ms', 0)}ms")
            st.write(f"- **Status**: {llm_status.get('status_code', 'N/A')}")

    # Current phase
    st.subheader("🔄 Workflow Status")
    current_phase = manifest.get("workflow", {}).get("current_phase", "Unknown")
    st.info(f"**Current Phase**: {current_phase}")

    # Phases completed
    phases = manifest.get("workflow", {}).get("phases_completed", [])
    if phases:
        st.markdown("**Completed Phases:**")
        for phase in phases:
            st.write(f"- ✅ {phase['phase']} (Agent: {phase['agent']}) - {phase['completed_at']}")


def self_development_tab(manifest):
    """Render self-development tab."""
    st.header("🌱 Self-Development Tracking")

    if manifest is None:
        st.warning("⚠️ No manifest data available. Run `python simulate_run.py` first.")
        return

    self_dev = manifest.get("self_development", {})

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    metrics = self_dev.get("metrics", {})

    with col1:
        st.metric("Learning Hours", f"{metrics.get('learning_hours', 0)} hrs")

    with col2:
        goals = self_dev.get("goals", [])
        completed = sum(1 for g in goals if g.get("status") == "Completed")
        st.metric("Goals Completed", f"{completed}/{len(goals)}")

    with col3:
        st.metric("Milestones", len(self_dev.get("milestones", [])))

    with col4:
        st.metric("Skills Gained", len(metrics.get("skills_gained", [])))

    st.divider()

    # Goals progress chart
    goals_chart = create_goals_progress_chart(manifest)
    if goals_chart:
        st.plotly_chart(goals_chart, use_container_width=True)

    st.divider()

    # Goals details
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Goals")
        goals = self_dev.get("goals", [])
        for goal in goals:
            status_icon = "✅" if goal.get("status") == "Completed" else "🔄" if goal.get("status") == "In Progress" else "📋"
            with st.expander(f"{status_icon} {goal.get('title', 'Unnamed Goal')}"):
                st.write(f"**Status**: {goal.get('status', 'Unknown')}")
                st.progress(goal.get("progress", 0) / 100)
                st.write(f"Progress: {goal.get('progress', 0)}%")

    with col2:
        st.subheader("🏆 Milestones")
        milestones = self_dev.get("milestones", [])
        if milestones:
            for milestone in milestones:
                st.success(f"**{milestone.get('title')}**")
                st.write(milestone.get('description', ''))
                st.caption(f"Achieved: {milestone.get('achieved_at', 'N/A')}")
        else:
            st.info("No milestones recorded yet.")

    st.divider()

    # Skills and reflections
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💡 Skills Gained")
        skills = metrics.get("skills_gained", [])
        if skills:
            for skill in skills:
                st.write(f"- {skill}")
        else:
            st.info("No skills recorded yet.")

    with col2:
        st.subheader("💭 Recent Reflections")
        reflections = self_dev.get("reflections", [])
        if reflections:
            for reflection in reflections[-3:]:  # Last 3
                with st.expander(f"Reflection {reflection.get('id', 'N/A')}"):
                    st.write(reflection.get('content', ''))
                    st.caption(f"Generated: {reflection.get('generated_at', 'N/A')}")
        else:
            st.info("No reflections generated yet.")


def main():
    """Main dashboard function."""
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/4a90e2/ffffff?text=DevAI", use_column_width=True)
        st.title("DevAI Orchestrator")
        st.markdown("---")

        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
        if auto_refresh:
            st.rerun()

        st.markdown("---")

        # Run orchestration button
        if st.button("🚀 Run Orchestration", type="primary"):
            with st.spinner("Running orchestration..."):
                import subprocess
                result = subprocess.run(
                    ["python", "simulate_run.py"],
                    cwd=Path(__file__).parent.parent,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    st.success("✅ Orchestration completed!")
                    st.rerun()
                else:
                    st.error(f"❌ Orchestration failed:\n{result.stderr}")

        st.markdown("---")

        # Quick stats
        manifest = load_manifest()
        if manifest:
            st.markdown("### Quick Stats")
            total_tokens = sum(
                data.get("total_tokens", 0)
                for data in manifest.get("monitoring", {}).get("token_usage", {}).values()
            )
            st.metric("Total Tokens", f"{total_tokens:,}")

            cost = manifest.get("monitoring", {}).get("estimated_costs_usd", 0.0)
            st.metric("Est. Cost", f"${cost:.4f}")

            learning_hours = manifest.get("self_development", {}).get("metrics", {}).get("learning_hours", 0)
            st.metric("Learning Hours", f"{learning_hours} hrs")

    # Main content
    st.title("🤖 DevAI Orchestrator Dashboard")
    st.markdown("Real-time monitoring for multi-agent AI orchestration with self-development tracking")

    # Load data
    manifest = load_manifest()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 System Status", "🔍 Token Analytics", "🌱 Self-Development"])

    with tab1:
        system_status_tab(manifest)

    with tab2:
        # Import and render token analytics
        from dashboard import token_analytics
        if manifest:
            st.markdown("### 📊 Token Usage & Cost Analytics")
            st.markdown("Comprehensive monitoring of LLM token consumption and cost estimates")
            st.markdown("---")

            monitoring = manifest.get("monitoring", {})
            token_usage = monitoring.get("token_usage", {})
            cost_breakdown = monitoring.get("cost_breakdown", {})
            local_llm_status = monitoring.get("local_llm_status", {})

            # Key metrics
            total_tokens = sum(data.get("total_tokens", 0) for data in token_usage.values())
            total_cost = monitoring.get("estimated_costs_usd", 0.0)
            total_requests = sum(len(data.get("requests", [])) for data in token_usage.values())

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💵 Total Cost", f"${total_cost:.4f}")
            with col2:
                st.metric("🔢 Total Tokens", f"{total_tokens:,}")
            with col3:
                st.metric("📊 Requests", total_requests)
            with col4:
                st.metric("🤖 Agents", len(token_usage))

            st.markdown("---")

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                token_chart = token_analytics.create_token_usage_chart(token_usage)
                st.plotly_chart(token_chart, use_container_width=True)

            with col2:
                cost_chart = token_analytics.create_cost_breakdown_chart(cost_breakdown)
                st.plotly_chart(cost_chart, use_container_width=True)

            # Timeline
            st.markdown("### 📈 Token Usage Timeline")
            timeline_chart = token_analytics.create_token_timeline_chart(token_usage)
            st.plotly_chart(timeline_chart, use_container_width=True)

            # Detailed table
            st.markdown("### 💰 Cost Breakdown")
            token_analytics.render_cost_table(cost_breakdown, token_usage)

            # LLM health
            st.markdown("### 🏥 Local LLM Health")
            token_analytics.render_health_status(local_llm_status)

            # Pricing reference
            with st.expander("📋 Model Pricing Reference"):
                token_analytics.render_pricing_table()
        else:
            st.info("ℹ️ No manifest data available. Run an orchestration to generate data.")

    with tab3:
        self_development_tab(manifest)

    # Footer
    st.markdown("---")
    st.caption(f"Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
