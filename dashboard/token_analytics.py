"""
Token Analytics Dashboard - Real-time LLM Usage Monitoring

Provides comprehensive visualization of token usage, cost estimates,
and LLM health metrics using Streamlit.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.monitor import get_monitoring_metrics
from src.cost_estimator import PRICING_TABLE


def load_manifest(manifest_path: str = "manifest_state.json") -> Dict[str, Any]:
    """
    Load manifest state from JSON file.

    Args:
        manifest_path: Path to manifest file

    Returns:
        Manifest dictionary
    """
    manifest_file = Path(manifest_path)

    if not manifest_file.exists():
        # Return default empty structure
        return {
            "monitoring": {
                "token_usage": {},
                "local_llm_status": {},
                "estimated_costs_usd": 0.0,
                "cost_breakdown": {}
            }
        }

    with open(manifest_file, 'r') as f:
        return json.load(f)


def create_token_usage_chart(token_data: Dict[str, Any]) -> go.Figure:
    """
    Create interactive bar chart for token usage.

    Args:
        token_data: Token usage data by agent

    Returns:
        Plotly figure
    """
    if not token_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No token usage data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    agents = list(token_data.keys())
    tokens = [data.get("total_tokens", 0) for data in token_data.values()]
    models = [data.get("model", "unknown") for data in token_data.values()]

    fig = go.Figure(data=[
        go.Bar(
            x=agents,
            y=tokens,
            text=tokens,
            textposition='outside',
            marker_color='rgb(55, 83, 109)',
            hovertemplate='<b>%{x}</b><br>Tokens: %{y:,}<br>Model: %{customdata}<extra></extra>',
            customdata=models
        )
    ])

    fig.update_layout(
        title="Token Usage by Agent",
        xaxis_title="Agent",
        yaxis_title="Total Tokens",
        hovermode='x',
        height=400,
        showlegend=False
    )

    return fig


def create_cost_breakdown_chart(cost_data: Dict[str, Any]) -> go.Figure:
    """
    Create pie chart for cost breakdown.

    Args:
        cost_data: Cost breakdown by agent

    Returns:
        Plotly figure
    """
    if not cost_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No cost data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    agents = list(cost_data.keys())
    costs = [data.get("cost_usd", 0) for data in cost_data.values()]

    # Filter out zero costs
    filtered_data = [(agent, cost) for agent, cost in zip(agents, costs) if cost > 0]

    if not filtered_data:
        fig = go.Figure()
        fig.add_annotation(
            text="All agents have zero cost (local models)",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
        return fig

    agents, costs = zip(*filtered_data)

    fig = go.Figure(data=[
        go.Pie(
            labels=agents,
            values=costs,
            hovertemplate='<b>%{label}</b><br>Cost: $%{value:.6f}<br>%{percent}<extra></extra>',
            textinfo='label+percent'
        )
    ])

    fig.update_layout(
        title="Cost Distribution by Agent",
        height=400
    )

    return fig


def create_token_timeline_chart(token_data: Dict[str, Any]) -> go.Figure:
    """
    Create timeline chart showing token usage over time.

    Args:
        token_data: Token usage data with request timestamps

    Returns:
        Plotly figure
    """
    if not token_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No token usage data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    # Build timeline data
    timeline_data = []
    for agent, data in token_data.items():
        requests = data.get("requests", [])
        for req in requests:
            timeline_data.append({
                "agent": agent,
                "tokens": req["tokens"],
                "timestamp": req["timestamp"]
            })

    if not timeline_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No request history available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    df = pd.DataFrame(timeline_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    fig = px.line(
        df,
        x='timestamp',
        y='tokens',
        color='agent',
        title='Token Usage Timeline',
        labels={'timestamp': 'Time', 'tokens': 'Tokens', 'agent': 'Agent'}
    )

    fig.update_layout(height=400, hovermode='x unified')

    return fig


def render_health_status(llm_status: Dict[str, Any]) -> None:
    """
    Render LLM health status indicators.

    Args:
        llm_status: LLM health status data
    """
    if not llm_status:
        st.info("ℹ️ No local LLM health data available")
        return

    is_healthy = llm_status.get("healthy", False)
    latency = llm_status.get("latency_ms", 0)
    model = llm_status.get("model", "unknown")
    endpoint = llm_status.get("endpoint", "unknown")
    last_checked = llm_status.get("last_checked", "never")

    # Parse timestamp
    try:
        last_checked_dt = datetime.fromisoformat(last_checked.replace('Z', '+00:00'))
        time_ago = datetime.utcnow().replace(tzinfo=last_checked_dt.tzinfo) - last_checked_dt
        time_ago_str = f"{int(time_ago.total_seconds())}s ago"
    except:
        time_ago_str = "unknown"

    # Status indicator
    status_color = "green" if is_healthy else "red"
    status_text = "🟢 Healthy" if is_healthy else "🔴 Unhealthy"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", status_text)

    with col2:
        st.metric("Latency", f"{latency:.2f}ms")

    with col3:
        st.metric("Model", model)

    with col4:
        st.metric("Last Checked", time_ago_str)

    with st.expander("📡 Connection Details"):
        st.code(f"Endpoint: {endpoint}", language="text")


def render_cost_table(cost_breakdown: Dict[str, Any], token_usage: Dict[str, Any]) -> None:
    """
    Render detailed cost breakdown table.

    Args:
        cost_breakdown: Cost breakdown by agent
        token_usage: Token usage data
    """
    if not cost_breakdown:
        st.info("ℹ️ No cost data available")
        return

    # Build table data
    table_data = []
    for agent, cost_data in cost_breakdown.items():
        model = cost_data.get("model", "unknown")
        tokens = cost_data.get("tokens", 0)
        cost = cost_data.get("cost_usd", 0)

        # Get number of requests
        requests = len(token_usage.get(agent, {}).get("requests", []))

        # Calculate avg cost per request
        avg_cost_per_request = cost / requests if requests > 0 else 0

        table_data.append({
            "Agent": agent.title(),
            "Model": model,
            "Tokens": f"{tokens:,}",
            "Requests": requests,
            "Cost (USD)": f"${cost:.6f}",
            "Avg Cost/Request": f"${avg_cost_per_request:.6f}"
        })

    df = pd.DataFrame(table_data)

    # Sort by cost descending
    df = df.sort_values("Cost (USD)", ascending=False)

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_pricing_table() -> None:
    """Render the pricing reference table for all models."""
    st.subheader("💲 Model Pricing Reference")

    pricing_data = []
    for model, (input_cost, output_cost) in PRICING_TABLE.items():
        if model == "unknown":
            continue
        pricing_data.append({
            "Model": model,
            "Input (per 1K tokens)": f"${input_cost:.6f}",
            "Output (per 1K tokens)": f"${output_cost:.6f}",
            "Type": "Local" if input_cost == 0 and output_cost == 0 else "Cloud"
        })

    df = pd.DataFrame(pricing_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Token Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🔍 Token Analytics Dashboard")
    st.markdown("Real-time monitoring of LLM token usage, costs, and health metrics")

    # Sidebar controls
    st.sidebar.title("⚙️ Controls")

    manifest_path = st.sidebar.text_input(
        "Manifest Path",
        value="manifest_state.json",
        help="Path to the manifest state JSON file"
    )

    auto_refresh = st.sidebar.checkbox("Auto Refresh (15s)", value=False)

    if st.sidebar.button("🔄 Refresh Now") or auto_refresh:
        st.rerun()

    if auto_refresh:
        import time
        time.sleep(15)
        st.rerun()

    # Load data
    manifest = load_manifest(manifest_path)
    monitoring = manifest.get("monitoring", {})
    token_usage = monitoring.get("token_usage", {})
    cost_breakdown = monitoring.get("cost_breakdown", {})
    local_llm_status = monitoring.get("local_llm_status", {})
    total_cost = monitoring.get("estimated_costs_usd", 0.0)

    # Calculate aggregates
    total_tokens = sum(data.get("total_tokens", 0) for data in token_usage.values())
    total_requests = sum(len(data.get("requests", [])) for data in token_usage.values())
    agents_tracked = len(token_usage)

    # Key metrics row
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💵 Total Cost", f"${total_cost:.4f}", help="Estimated total cost in USD")

    with col2:
        st.metric("🔢 Total Tokens", f"{total_tokens:,}", help="Sum of all tokens across agents")

    with col3:
        st.metric("📊 Total Requests", total_requests, help="Total number of agent requests")

    with col4:
        st.metric("🤖 Agents Tracked", agents_tracked, help="Number of agents with usage data")

    st.divider()

    # Token usage visualization
    st.subheader("📊 Token Usage Analysis")

    tab1, tab2 = st.tabs(["📊 Bar Chart", "📈 Timeline"])

    with tab1:
        token_chart = create_token_usage_chart(token_usage)
        st.plotly_chart(token_chart, use_container_width=True)

    with tab2:
        timeline_chart = create_token_timeline_chart(token_usage)
        st.plotly_chart(timeline_chart, use_container_width=True)

    st.divider()

    # Cost analysis
    st.subheader("💰 Cost Analysis")

    col1, col2 = st.columns([2, 1])

    with col1:
        render_cost_table(cost_breakdown, token_usage)

    with col2:
        cost_chart = create_cost_breakdown_chart(cost_breakdown)
        st.plotly_chart(cost_chart, use_container_width=True)

    st.divider()

    # LLM Health Status
    st.subheader("🏥 Local LLM Health Status")
    render_health_status(local_llm_status)

    st.divider()

    # Pricing reference (collapsible)
    with st.expander("📋 View Model Pricing Reference"):
        render_pricing_table()

    # Footer
    st.divider()
    last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    st.caption(f"Last updated: {last_updated}")


if __name__ == "__main__":
    main()
