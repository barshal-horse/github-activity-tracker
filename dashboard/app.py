"""
GitHub Open Source Activity Tracker — Streamlit Dashboard

Connects to BigQuery when credentials are available (Streamlit Cloud or local .env),
falls back to CSV data files for local development.

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
    initial_sidebar_state="collapsed"
)

# ============================================================
# Premium Dark Theme CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark background */
    .stApp {
        background: #0d1117;
    }

    /* Header styling */
    .dashboard-header {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .dashboard-header h1 {
        background: linear-gradient(135deg, #7c3aed, #2563eb, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }
    .dashboard-header p {
        color: #8b949e;
        font-size: 1rem;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #161b22, #1c2333);
        border: 1px solid #30363d;
        border-radius: 16px;
        padding: 1.2rem !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }

    /* Section headers */
    .section-header {
        color: #e6edf3;
        font-weight: 600;
        font-size: 1.3rem;
        padding: 0.5rem 0;
        border-bottom: 2px solid #7c3aed;
        margin-bottom: 1rem;
        display: inline-block;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Dividers */
    hr { border-color: #21262d !important; }

    /* Dataframe */
    .stDataFrame { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Color palette — vibrant, modern, harmonious
# ============================================================
COLORS = {
    "PushEvent": "#7c3aed",
    "CreateEvent": "#2563eb",
    "PullRequestEvent": "#06b6d4",
    "IssueCommentEvent": "#10b981",
    "WatchEvent": "#f59e0b",
    "IssuesEvent": "#ef4444",
    "ForkEvent": "#ec4899",
    "DeleteEvent": "#6366f1",
    "PullRequestReviewCommentEvent": "#14b8a6",
    "PullRequestReviewEvent": "#8b5cf6",
    "ReleaseEvent": "#f97316",
    "MemberEvent": "#22d3ee",
    "GollumEvent": "#a78bfa",
    "CommitCommentEvent": "#38bdf8",
    "PublicEvent": "#64748b",
    "SponsorshipEvent": "#db2777",
}

METRIC_COLORS = ["#7c3aed", "#2563eb", "#06b6d4", "#10b981"]


# ============================================================
# Data Loading — BigQuery → CSV fallback
# ============================================================
@st.cache_data(ttl=3600)
def load_data():
    """Try BigQuery first, fall back to CSV files."""
    # Try BigQuery
    try:
        from google.cloud import bigquery

        # Check for Streamlit Cloud secrets or env var
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )
            project_id = st.secrets["gcp_service_account"]["project_id"]
            client = bigquery.Client(credentials=credentials, project=project_id)
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            client = bigquery.Client()
        else:
            raise Exception("No BigQuery credentials found")

        dataset = os.getenv("BQ_DATASET", "github_analytics")

        hourly_df = client.query(f"""
            SELECT event_date, event_hour, event_type,
                   COUNT(*) as event_count,
                   COUNT(DISTINCT actor_login) as unique_actors,
                   COUNT(DISTINCT repo_name) as unique_repos
            FROM `{dataset}.stg_github_events`
            GROUP BY event_date, event_hour, event_type
            ORDER BY event_date, event_hour
        """).to_dataframe()

        dist_df = client.query(f"""
            SELECT * FROM `{dataset}.fct_event_distribution`
            ORDER BY event_count DESC
        """).to_dataframe()

        top_repos_df = client.query(f"""
            SELECT * FROM `{dataset}.fct_top_repos`
            ORDER BY activity_rank LIMIT 20
        """).to_dataframe()

        return hourly_df, dist_df, top_repos_df, "BigQuery"

    except Exception:
        pass

    # Fallback: CSV files
    data_dir = Path(__file__).parent / "data"
    if (data_dir / "event_distribution.csv").exists():
        dist_df = pd.read_csv(data_dir / "event_distribution.csv")
        hourly_df = pd.read_csv(data_dir / "hourly_activity.csv")
        top_repos_df = pd.read_csv(data_dir / "top_repos.csv")
        return hourly_df, dist_df, top_repos_df, "CSV"

    st.error("No data source available. Please set up BigQuery or run the data pipeline.")
    st.stop()


# ============================================================
# Load Data
# ============================================================
hourly_df, dist_df, top_repos_df, data_source = load_data()


# ============================================================
# Header
# ============================================================
total_events = int(dist_df["event_count"].sum())

st.markdown(f"""
<div class="dashboard-header">
    <h1>🔭 GitHub Activity Tracker</h1>
    <p>Analyzing <strong>{total_events:,}</strong> real public GitHub events from
    <a href="https://www.gharchive.org/" style="color: #7c3aed;">GH Archive</a>
    &nbsp;·&nbsp; Data via {data_source}</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# KPI Metrics
# ============================================================
total_actors = int(dist_df["unique_actors"].sum())
total_repos = int(dist_df["unique_repos"].sum())
num_event_types = len(dist_df)

cols = st.columns(4)
metrics = [
    ("⚡ Total Events", f"{total_events:,}"),
    ("👩‍💻 Unique Developers", f"{total_actors:,}"),
    ("📦 Active Repos", f"{total_repos:,}"),
    ("🏷️ Event Types", str(num_event_types)),
]
for col, (label, value) in zip(cols, metrics):
    col.metric(label, value)

st.markdown("---")

# ============================================================
# TILE 1 + TILE 2 side by side
# ============================================================
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="section-header">📊 Event Type Distribution</div>', unsafe_allow_html=True)

    fig_dist = px.pie(
        dist_df,
        names="event_type",
        values="event_count",
        color="event_type",
        color_discrete_map=COLORS,
        hole=0.45,
    )
    fig_dist.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6edf3", family="Inter", size=12),
        legend=dict(
            orientation="v", yanchor="middle", y=0.5,
            xanchor="left", x=1.02, font=dict(size=10, color="#8b949e"),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
    )
    fig_dist.update_traces(
        textposition='inside', textinfo='percent',
        textfont=dict(size=11, color="white"),
        marker=dict(line=dict(color='#0d1117', width=2)),
    )
    st.plotly_chart(fig_dist, key="dist_chart")

with col_right:
    st.markdown('<div class="section-header">📈 Activity Over Time</div>', unsafe_allow_html=True)

    top_events = dist_df.head(6)["event_type"].tolist()
    hourly_filtered = hourly_df[hourly_df["event_type"].isin(top_events)].copy()

    if "event_hour" in hourly_filtered.columns:
        hourly_filtered["time_label"] = (
            hourly_filtered["event_date"].astype(str) + " " +
            hourly_filtered["event_hour"].astype(str).str.zfill(2) + ":00"
        )
        x_col = "time_label"
        x_label = "Time (UTC)"
    else:
        x_col = "event_date"
        x_label = "Date"

    fig_trend = px.area(
        hourly_filtered, x=x_col, y="event_count",
        color="event_type", color_discrete_map=COLORS,
        labels={"event_count": "Events", x_col: x_label, "event_type": "Type"},
    )
    fig_trend.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6edf3", family="Inter"),
        xaxis=dict(gridcolor="#161b22", showgrid=True, color="#8b949e"),
        yaxis=dict(gridcolor="#161b22", showgrid=True, color="#8b949e"),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.35,
            xanchor="center", x=0.5, font=dict(size=10, color="#8b949e"),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
    )
    st.plotly_chart(fig_trend, key="trend_chart")

st.markdown("---")

# ============================================================
# TILE 3: Top Repositories
# ============================================================
st.markdown('<div class="section-header">🏆 Most Active Repositories</div>', unsafe_allow_html=True)

fig_repos = px.bar(
    top_repos_df.head(15),
    y="repo_name", x="total_events",
    orientation="h",
    color="total_events",
    color_continuous_scale=["#1e1b4b", "#7c3aed", "#c084fc"],
    labels={"total_events": "Total Events", "repo_name": ""},
)
fig_repos.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e6edf3", family="Inter"),
    yaxis=dict(autorange="reversed", color="#8b949e"),
    xaxis=dict(gridcolor="#161b22", showgrid=True, color="#8b949e"),
    coloraxis_showscale=False,
    margin=dict(l=10, r=10, t=10, b=10),
    height=500,
)
st.plotly_chart(fig_repos, key="repos_chart")

st.markdown("---")

# ============================================================
# TILE 4: Event Breakdown Table
# ============================================================
st.markdown('<div class="section-header">📋 Event Breakdown</div>', unsafe_allow_html=True)

table_df = dist_df[["event_type", "event_count", "unique_actors", "unique_repos", "percentage"]].copy()
table_df.columns = ["Event Type", "Events", "Developers", "Repos", "Share %"]
table_df = table_df.reset_index(drop=True)

st.dataframe(
    table_df, hide_index=True,
    column_config={
        "Events": st.column_config.NumberColumn(format="%d"),
        "Developers": st.column_config.NumberColumn(format="%d"),
        "Repos": st.column_config.NumberColumn(format="%d"),
        "Share %": st.column_config.ProgressColumn(
            min_value=0, max_value=100, format="%.1f%%"
        ),
    }
)

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #484f58; font-size: 0.8rem; padding: 1rem;">
    Built for <a href="https://github.com/DataTalksClub/data-engineering-zoomcamp" style="color: #7c3aed;">
    DE Zoomcamp 2026</a> &nbsp;·&nbsp;
    Data: <a href="https://www.gharchive.org/" style="color: #7c3aed;">GH Archive</a> &nbsp;·&nbsp;
    <a href="https://github.com/barshal-horse/github-activity-tracker" style="color: #7c3aed;">Source Code</a>
</div>
""", unsafe_allow_html=True)
