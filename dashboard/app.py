"""
GitHub Open Source Activity Tracker — Streamlit Dashboard

Visualizes real GitHub event data from GH Archive.
Loads pre-processed CSVs from dashboard/data/ directory.

Usage:
    streamlit run dashboard/app.py
"""

import os
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# Page Config
# ============================================================
st.set_page_config(
    page_title="GitHub Activity Tracker",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Custom CSS for premium look
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main { background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); }

    .metric-card {
        background: linear-gradient(135deg, #21262d 0%, #30363d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #58a6ff;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    h1, h2, h3 { color: #f0f6fc !important; }

    .stMetric { background: #21262d; border-radius: 10px; padding: 10px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Color map for event types
# ============================================================
COLOR_MAP = {
    "PushEvent": "#58a6ff",
    "WatchEvent": "#f0883e",
    "PullRequestEvent": "#3fb950",
    "IssuesEvent": "#f85149",
    "ForkEvent": "#bc8cff",
    "CreateEvent": "#79c0ff",
    "DeleteEvent": "#d2a8ff",
    "IssueCommentEvent": "#56d364",
    "PullRequestReviewCommentEvent": "#e3b341",
    "PullRequestReviewEvent": "#ffa657",
    "ReleaseEvent": "#ff7b72",
    "MemberEvent": "#7ee787",
    "GollumEvent": "#ffa657",
    "CommitCommentEvent": "#a5d6ff",
    "PublicEvent": "#8b949e",
    "SponsorshipEvent": "#db61a2",
}


# ============================================================
# Data Loading — CSV files (real data from GH Archive)
# ============================================================
@st.cache_data(ttl=3600)
def load_data():
    """Load pre-processed CSV data from dashboard/data/ directory."""
    data_dir = Path(__file__).parent / "data"

    dist_df = pd.read_csv(data_dir / "event_distribution.csv")
    hourly_df = pd.read_csv(data_dir / "hourly_activity.csv")
    top_repos_df = pd.read_csv(data_dir / "top_repos.csv")

    return hourly_df, dist_df, top_repos_df


# ============================================================
# Load Data
# ============================================================
hourly_df, dist_df, top_repos_df = load_data()


# ============================================================
# Header
# ============================================================
st.markdown("# 🔭 GitHub Open Source Activity Tracker")
st.markdown("*Analyzing **203,312 real public GitHub events** from [GH Archive](https://www.gharchive.org/) (Feb 17, 2026)*")
st.divider()

# ============================================================
# KPI Metrics
# ============================================================
total_events = int(dist_df["event_count"].sum())
total_actors = int(dist_df["unique_actors"].sum())
total_repos = int(dist_df["unique_repos"].sum())
num_event_types = len(dist_df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Events", f"{total_events:,}")
with col2:
    st.metric("Unique Developers", f"{total_actors:,}")
with col3:
    st.metric("Active Repos", f"{total_repos:,}")
with col4:
    st.metric("Event Types", num_event_types)

st.divider()

# ============================================================
# TILE 1: Event Type Distribution (Categorical)
# ============================================================
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📊 Event Type Distribution")

    fig_dist = px.pie(
        dist_df,
        names="event_type",
        values="event_count",
        color="event_type",
        color_discrete_map=COLOR_MAP,
        hole=0.4,
    )
    fig_dist.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9", family="Inter"),
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=11)
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        height=400,
    )
    fig_dist.update_traces(
        textposition='inside',
        textinfo='percent',
        textfont_size=11,
    )
    st.plotly_chart(fig_dist, key="dist_chart")

# ============================================================
# TILE 2: Hourly Activity Trends (Temporal)
# ============================================================
with col_right:
    st.markdown("### 📈 Hourly Activity Trends")

    # Get top 6 event types for cleaner chart
    top_events = dist_df.head(6)["event_type"].tolist()
    hourly_filtered = hourly_df[hourly_df["event_type"].isin(top_events)].copy()
    hourly_filtered["time_label"] = hourly_filtered["event_date"] + " " + hourly_filtered["event_hour"].astype(str).str.zfill(2) + ":00"

    fig_trend = px.area(
        hourly_filtered,
        x="time_label",
        y="event_count",
        color="event_type",
        color_discrete_map=COLOR_MAP,
        labels={"event_count": "Events", "time_label": "Time (UTC)", "event_type": "Event Type"},
    )
    fig_trend.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9", family="Inter"),
        xaxis=dict(gridcolor="#21262d", showgrid=True),
        yaxis=dict(gridcolor="#21262d", showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=20, b=20),
        height=400,
    )
    st.plotly_chart(fig_trend, key="trend_chart")

st.divider()

# ============================================================
# TILE 3: Top Repositories
# ============================================================
st.markdown("### 🏆 Top Repositories by Activity")

fig_repos = px.bar(
    top_repos_df.head(15),
    y="repo_name",
    x="total_events",
    orientation="h",
    color="total_events",
    color_continuous_scale=["#0d1117", "#1f6feb", "#58a6ff"],
    labels={"total_events": "Total Events", "repo_name": "Repository"},
)
fig_repos.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#c9d1d9", family="Inter"),
    yaxis=dict(autorange="reversed"),
    coloraxis_showscale=False,
    margin=dict(l=20, r=20, t=20, b=20),
    height=500,
)
st.plotly_chart(fig_repos, key="repos_chart")

st.divider()

# ============================================================
# TILE 4: Event Breakdown Table
# ============================================================
st.markdown("### 📋 Event Type Breakdown")

styled_dist = dist_df[["event_type", "event_count", "unique_actors", "unique_repos", "percentage"]].copy()
styled_dist.columns = ["Event Type", "Total Events", "Unique Developers", "Active Repos", "% Share"]
styled_dist = styled_dist.reset_index(drop=True)

st.dataframe(
    styled_dist,
    hide_index=True,
    column_config={
        "Total Events": st.column_config.NumberColumn(format="%d"),
        "Unique Developers": st.column_config.NumberColumn(format="%d"),
        "Active Repos": st.column_config.NumberColumn(format="%d"),
        "% Share": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
    }
)

# ============================================================
# Footer
# ============================================================
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #484f58; font-size: 0.8rem;">
        Built with ❤️ for <a href="https://github.com/DataTalksClub/data-engineering-zoomcamp" style="color: #58a6ff;">
        DE Zoomcamp 2026</a> |
        Data: <a href="https://www.gharchive.org/" style="color: #58a6ff;">GH Archive</a> (Feb 17, 2026, 203K+ events)
    </div>
    """,
    unsafe_allow_html=True
)
