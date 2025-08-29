import streamlit as st
import os
import subprocess
from codecarbon import EmissionsTracker
import pandas as pd
import uuid
import io
import contextlib
import time
from pathlib import Path
import shutil

# --- Configuration ---
original_wd = Path.cwd()  # Store the original working directory
temp_root_dir = original_wd / "temp_sessions"
temp_root_dir.mkdir(parents=True, exist_ok=True)
results_file = original_wd / "comparison_results.csv"  # Shared results CSV

st.set_page_config(page_title="GreenAI Comparometer - CodeCarbon Tracker", layout="centered")

# === Unified CSS styling (same as eco2AI for branding consistency) ===
st.markdown(
    """
    <style>
    /* Dark theme background */
    .stApp {
        background: url('https://www.thedigitalspeaker.com/content/images/2023/02/Sustainable-AI-greener-future.jpg') center/cover fixed no-repeat;
        position: relative;
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
        color: #e0e0e0;
        padding-top: 0;
        margin: 0;
        min-height: 100vh;
        background-color: #121a12; /* fallback dark background */
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(18, 26, 18, 0.85); /* darker overlay */
        backdrop-filter: blur(4px);
        pointer-events: none;
        z-index: 0;
    }
    [data-testid="stAppViewContainer"] > .main, .block-container {
        position: relative;
        z-index: 1;
        padding-top: 1rem;
        color: #e0e0e0;
    }

    /* Header/title */
    .header-wrapper {
        max-width: 1000px;
        margin: 0 auto 0.5rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 0.5rem 1rem;
        text-align: center;
        color: #a5d6a7;
    }
    .main-app-title {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 700;
        color: #81c784;
        line-height: 1.05;
    }
    .tagline {
        font-size: 1rem;
        font-style: italic;
        color: #a5d6a7;
        margin: 0;
    }

    /* Tracker card */
    .tracker-card {
        max-width: 1000px;
        margin: 1.75rem auto 2rem;
        display: flex;
        flex-wrap: wrap;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 40px 90px rgba(0,0,0,0.8);
        background: #1b2b1b; /* dark green background */
        color: #d0f0c8;
    }
    .tracker-left, .tracker-right {
        padding: 2.5rem 2rem;
        flex: 1;
        min-width: 320px;
        box-sizing: border-box;
    }
    .tracker-left {
        background: linear-gradient(135deg,#254625 0%,#346a34 100%);
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.75rem;
        color: #c8e6c9;
    }
    .tracker-left h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #a5d6a7;
    }
    .tracker-left .sub {
        font-size: 1rem;
        font-style: italic;
        color: #b2dfdb;
        line-height: 1.4;
        margin: 0;
    }

    /* Uploader & button */
    .upload-wrapper {
        background: #263926;
        border: 1px solid #3a5f3a;
        border-radius: 12px;
        padding: 1rem 1rem 0.5rem;
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 0.5rem;
        color: #e0e0e0;
    }
    .upload-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        color: #a5d6a7 !important;
        font-weight: 600;
    }
    .upload-instruction {
        background: #2e4d2e;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 4px 0 8px;
        font-size: 0.95rem;
        color: #b2dfdb;
    }

    .main-app-title {
    margin: 0;
    font-size: 2.4rem;
    font-weight: 700;
    color: #81c784;
    line-height: 1.05;
    text-shadow: 0 0 8px rgba(129, 199, 132, 0.8), 0 0 14px rgba(129, 199, 132, 0.6);
}

.tagline {
    font-size: 1rem;
    font-style: italic;
    color: #a5d6a7;
    margin: 0;
    text-shadow: 0 0 6px rgba(165, 214, 167, 0.7);
}

.tracker-left h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    color: #a5d6a7;
    text-shadow: 0 0 8px rgba(165, 214, 167, 0.8), 0 0 14px rgba(165, 214, 167, 0.6);
}

    .file-uploader-wrapper > div {
        border-radius: 12px !important;
        overflow: hidden;
        color: #e0e0e0 !important;
    }

    /* File uploader label text white */
    div[data-testid="stFileUploader"] > label {
        color: white !important;
        font-weight: 600;
        font-size: 1rem;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        background: linear-gradient(135deg,#4caf50,#2e7d32) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 14px 40px rgba(46,125,50,0.6) !important;
        transition: transform .15s, filter .15s;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .stButton>button:hover {
        filter: brightness(1.1);
        transform: translateY(-1px);
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        background: #4caf5080;
        color: #d0f0c8;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 12px;
        text-shadow: 0 0 4px #1b2b1b;
    }

    /* Code blocks */
    .stCodeBlock pre {
        border-radius: 10px !important;
        padding: 14px !important;
        background: #142214 !important;
        color: #d0f0c8 !important;
        font-size: 0.9rem !important;
    }

    /* DataFrame styling */
    .stDataFrame > div {
        border-radius: 10px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
        overflow: hidden;
        background: #1b2b1b;
        color: #c8e6c8;
    }

    /* Success message text white */
    .stAlert.stAlert-success > div {
        color: #c8e6c8 !important;
        font-weight: 600;
    }

    /* Warning message styling */
    .stAlert.stAlert-warning > div {
        color: #f9d56e !important;
        font-weight: 600;
    }

    /* Error message styling */
    .stAlert.stAlert-error > div {
        color: #ff6f6f !important;
        font-weight: 600;
    }

    /* Hide default Streamlit menu/footer */
    #MainMenu, footer { visibility: hidden; }

    @media (max-width: 980px) {
        .tracker-card { flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# === Header ===
st.markdown(
    """
    <div class="header-wrapper">
        <h1 class="main-app-title">🌱 GreenAI Comparometer</h1>
        <div class="tagline"><b><strong>Upload a .py or .ipynb file to track its carbon emissions.</strong></b></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# === Tracker card ===
st.markdown(
    """
    <div class="tracker-card">
      <div class="tracker-left">
        <h1>CodeCarbon Emission Tracker</h1>
        <div class="sub">Run arbitrary Python or notebook code and measure its carbon footprint using <strong>CodeCarbon</strong>.</div>
      </div>
      <div class="tracker-right">
        <div id="status_container">
          <div class="status-badge" id="status_badge">Ready to upload</div>
        </div>
    """,
    unsafe_allow_html=True,
)

# --- File Upload Section ---
uploaded_code_file = st.file_uploader("📂 Upload .py or .ipynb file", type=["py", "ipynb"])
uploaded_dataset_files = st.file_uploader(
    "📦 Upload dataset files (e.g., .csv, .json, .txt)",
    type=["csv", "json", "txt"],
    accept_multiple_files=True
)

if uploaded_code_file:
    # Create a fresh session dir
    session_dir = temp_root_dir / str(uuid.uuid4())
    session_dir.mkdir(parents=True, exist_ok=True)

    # Save code file
    code_path = session_dir / uploaded_code_file.name
    with open(code_path, "wb") as f:
        f.write(uploaded_code_file.getbuffer())
    st.success(f"✅ Code file '{uploaded_code_file.name}' uploaded.")

    # Save dataset files
    if uploaded_dataset_files:
        for file in uploaded_dataset_files:
            dataset_path = session_dir / file.name
            with open(dataset_path, "wb") as f:
                f.write(file.getbuffer())
        st.success(f"✅ {len(uploaded_dataset_files)} dataset(s) uploaded.")

    if st.button("🚀 Run with CodeCarbon"):
        try:
            os.chdir(session_dir)

            # Convert notebook if needed
            if uploaded_code_file.name.endswith(".ipynb"):
                st.info("🔄 Converting notebook to Python script...")
                base_name = uploaded_code_file.name.replace(".ipynb", "")
                subprocess.run(
                    ["jupyter", "nbconvert", "--to", "python", uploaded_code_file.name, "--output", base_name],
                    check=True
                )
                run_file = f"{base_name}.py"
            else:
                run_file = uploaded_code_file.name

            tracker = EmissionsTracker(output_file="emissions.csv")
            tracker.start()

            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                exec(Path(run_file).read_text(), {})

            tracker.stop()
            st.success("✅ Emission tracking completed.")

            # ✅ Save results BEFORE cleanup
            emission_file = Path("emissions.csv")
            if emission_file.exists():
                df = pd.read_csv(emission_file)
                st.subheader("📊 Latest Emission Data:")
                st.dataframe(df.tail(1))

                last_row = df.tail(1).iloc[0]
                result_row = {
                    "uploaded_filename": uploaded_code_file.name,
                    "tool_name": "CodeCarbon",
                    "co2_emissions_kg": last_row.get("emissions", 0),
                    "power_kwh": last_row.get("energy_consumed", 0),
                    "duration_s": last_row.get("duration", 0),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }

                if results_file.exists():
                    df_results = pd.read_csv(results_file)
                    df_results = pd.concat([df_results, pd.DataFrame([result_row])], ignore_index=True)
                else:
                    df_results = pd.DataFrame([result_row])

                df_results.to_csv(results_file, index=False)
                st.success("📂 Results saved for comparison.")
            else:
                st.warning("⚠️ emissions.csv not found.")

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

        finally:
            os.chdir(original_wd)
            shutil.rmtree(session_dir, ignore_errors=True)

# Close tracker card
st.markdown("</div></div>", unsafe_allow_html=True)
