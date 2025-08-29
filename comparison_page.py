import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

results_file = Path("comparison_results.csv")

st.set_page_config(page_title="GreenAI Comparometer - Comparison", layout="wide")

# === Dark mode CSS styling with graph borders ===
st.markdown(
    """
    <style>
    /* Dark background with subtle texture */
    .stApp {
        background: linear-gradient(135deg, #121a13, #1b2b1e);
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        color: #a8d5a3;
        min-height: 100vh;
        position: relative;
    }
    [data-testid="stAppViewContainer"] > .main, .block-container {
        max-width: 1100px;
        margin: 0 auto;
        padding: 1rem 2rem 2rem;
        position: relative;
        z-index: 10;
    }

    /* Title styling */
    .title-block {
        text-align: center;
        margin-bottom: 2rem;
    }
    .title-block h1 {
        margin: 0;
        font-size: 3rem;
        font-weight: 800;
        color: #6bdc6b;
        text-shadow: 0 0 8px #4ca64c;
    }
    .title-block p {
        font-size: 1.3rem;
        font-style: italic;
        color: #92c891;
        margin-top: 0.3rem;
        margin-bottom: 2rem;
    }

    /* Warning style for dark mode */
    .stWarning {
        background-color: #4d3c2f;
        border-left: 6px solid #bb8f42;
        color: #f3d88b;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }

    /* Dataframe styling */
    .stDataFrame > div {
        border-radius: 12px;
        box-shadow: 0 0 20px 1px rgba(107,220,107,0.4);
        overflow-x: auto;
        border: 1.5px solid #6bdc6b;
    }

    /* Separator line */
    hr {
        border: none;
        border-top: 1px solid #3e5a3e;
        margin: 2rem 0;
    }

    /* Hide Streamlit footer and menu */
    #MainMenu, footer {visibility: hidden;}

    /* Plotly graph container styling */
    .plotly-graph-div {
        border: 2.5px solid #4ca64c !important;
        border-radius: 12px !important;
        box-shadow: 0 0 20px 2px rgba(76,166,76,0.45);
        background: #182618 !important;
    }

    /* Plotly axis titles and ticks */
    .main-svg text, .main-svg .xtick text, .main-svg .ytick text {
        fill: #a8d5a3 !important;
        font-weight: 600 !important;
    }

    /* Plotly bar text styling */
    .main-svg .bar text {
        fill: #a8d5a3 !important;
        font-weight: 700 !important;
    }

    /* Responsive tweaks */
    @media (max-width: 1100px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title & subtitle
st.markdown(
    """
    <div class="title-block">
        <h1>📊 GreenAI Comparometer - Emissions Comparison</h1>
        <p>Compare results from <strong>eco2AI</strong>, <strong>CodeCarbon</strong>, and <strong>CarbonTracker</strong>.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not results_file.exists():
    st.warning("⚠️ No results found. Please run at least one tracker first.")
    st.stop()

df = pd.read_csv(results_file)

filenames = df["uploaded_filename"].unique().tolist()
selected_file = st.selectbox("Select file to compare:", filenames)

df_filtered = df[df["uploaded_filename"] == selected_file]

if df_filtered.empty:
    st.warning("⚠️ No data available for the selected file.")
    st.stop()

st.subheader("📄 Results Table")
st.dataframe(df_filtered, use_container_width=True)

col1, col2, col3 = st.columns(3)

with col1:
    fig_co2 = px.bar(
        df_filtered,
        x="tool_name",
        y="co2_emissions_kg",
        title="CO₂ Emissions (kg)",
        color="tool_name",
        text_auto=".6f",
        color_discrete_map={
            "eco2AI": "#4caf50",
            "CodeCarbon": "#388e3c",
            "CarbonTracker": "#81c784"
        },
        template="plotly_dark"
    )
    fig_co2.update_layout(
        plot_bgcolor="#182618",
        paper_bgcolor="#182618",
        font_color="#a8d5a3",
        title_font_size=20,
        title_font_color="#6bdc6b",
        margin=dict(t=50, b=30, l=40, r=40),
        yaxis=dict(showgrid=True, gridcolor='#2f4f2f', zerolinecolor='#4ca64c'),
        xaxis=dict(showgrid=False)
    )
    fig_co2.update_traces(marker_line_color='black', marker_line_width=1.8)
    st.plotly_chart(fig_co2, use_container_width=True)

with col2:
    fig_power = px.bar(
        df_filtered,
        x="tool_name",
        y="power_kwh",
        title="Energy Consumption (kWh)",
        color="tool_name",
        text_auto=".6f",
        color_discrete_map={
            "eco2AI": "#2196f3",
            "CodeCarbon": "#1565c0",
            "CarbonTracker": "#64b5f6"
        },
        template="plotly_dark"
    )
    fig_power.update_layout(
        plot_bgcolor="#182f3e",
        paper_bgcolor="#182f3e",
        font_color="#a8d5a3",
        title_font_size=20,
        title_font_color="#5db7f5",
        margin=dict(t=50, b=30, l=40, r=40),
        yaxis=dict(showgrid=True, gridcolor='#2c4660', zerolinecolor='#2196f3'),
        xaxis=dict(showgrid=False)
    )
    fig_power.update_traces(marker_line_color='black', marker_line_width=1.8)
    st.plotly_chart(fig_power, use_container_width=True)

with col3:
    fig_duration = px.bar(
        df_filtered,
        x="tool_name",
        y="duration_s",
        title="Execution Time (s)",
        color="tool_name",
        text_auto=".2f",
        color_discrete_map={
            "eco2AI": "#ff9800",
            "CodeCarbon": "#ef6c00",
            "CarbonTracker": "#ffb74d"
        },
        template="plotly_dark"
    )
    fig_duration.update_layout(
        plot_bgcolor="#3e2e18",
        paper_bgcolor="#3e2e18",
        font_color="#a8d5a3",
        title_font_size=20,
        title_font_color="#f4a42f",
        margin=dict(t=50, b=30, l=40, r=40),
        yaxis=dict(showgrid=True, gridcolor='#6f4b00', zerolinecolor='#ff9800'),
        xaxis=dict(showgrid=False)
    )
    fig_duration.update_traces(marker_line_color='black', marker_line_width=1.8)
    st.plotly_chart(fig_duration, use_container_width=True)

st.markdown("---")
st.markdown(
    f"✅ Comparison complete for **{selected_file}**. "
    "You can now visually analyze which tool has lower emissions, energy usage, and time.",
    unsafe_allow_html=True
)
