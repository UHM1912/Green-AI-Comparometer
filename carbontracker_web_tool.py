import streamlit as st
import os
import uuid
import subprocess
import pandas as pd
import io
import contextlib
import time
import re
from pathlib import Path
import shutil

# --- Configuration ---
# Store the original working directory at the top level
original_wd = Path.cwd()
temp_root_dir = original_wd / "temp_sessions"
temp_root_dir.mkdir(parents=True, exist_ok=True)
results_file = original_wd / "comparison_results.csv"

st.set_page_config(page_title="GreenAI Comparometer - CarbonTracker", layout="centered")

st.markdown(
    """
    <style>
    /* Dark background with subtle green overlay */
    .stApp {
        background: url('https://www.thedigitalspeaker.com/content/images/2023/02/Sustainable-AI-greener-future.jpg') center/cover fixed no-repeat;
        position: relative;
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
        color: #b5d6a1;
        padding-top: 0;
        margin: 0;
        min-height: 100vh;
        background-color: #121912; /* fallback dark bg */
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(18,25,18,0.7);
        backdrop-filter: blur(4px);
        pointer-events: none;
        z-index: 0;
    }
    [data-testid="stAppViewContainer"] > .main, .block-container {
        position: relative;
        z-index: 1;
        padding-top: 1rem;
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
    }
    .main-app-title {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 700;
        color: #8bc34a;  /* lighter green */
        line-height: 1.05;
        text-shadow: 0 0 6px #63952d88;
    }
    .tagline {
        font-size: 1rem;
        font-style: italic;
        color: #9ccc65;
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
        box-shadow: 0 40px 90px rgba(140,180,100,0.6);
        background: #1a2a1a;
    }
    .tracker-left, .tracker-right {
        padding: 2.5rem 2rem;
        flex: 1;
        min-width: 320px;
        box-sizing: border-box;
        color: #c5e1a5;
    }
    .tracker-left {
        background: linear-gradient(135deg, #2f462f 0%, #466446 100%);
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.75rem;
    }
    .tracker-left h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #aed581;
        text-shadow: 0 0 5px #8bc34aaa;
    }
    .tracker-left .sub {
        font-size: 1rem;
        font-style: italic;
        color: #9ccc65;
        line-height: 1.4;
        margin: 0;
    }

    /* Input & uploader */
    .upload-wrapper {
        background: #274627;
        border: 1px solid #3a6b2f;
        border-radius: 12px;
        padding: 1rem 1rem 0.5rem;
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 0.5rem;
        color: #d0e8a8;
    }
    .upload-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        color: #a5c270;
        font-weight: 500;
    }
    .upload-instruction {
        background: #3a6b2f;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 4px 0 8px;
        font-size: 0.95rem;
        color: #c5e1a5;
    }
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        background: linear-gradient(135deg,#8bc34a,#4a7a0f) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 14px 40px rgba(75,128,20,0.6) !important;
        transition: transform .15s, filter .15s;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .stButton>button:hover {
        filter: brightness(1.15);
        transform: translateY(-1px);
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        background: #4a7a0f;
        color: #d0e8a8;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 12px;
        text-shadow: 0 0 3px #a5c270cc;
    }

    /* Output styling */
    .stCodeBlock pre {
        border-radius: 10px !important;
        padding: 14px !important;
        background: #263926 !important;
        color: #d0f0a3 !important;
        font-size: 0.9rem !important;
    }
    .stDataFrame > div {
        border-radius: 10px;
        box-shadow: 0 12px 40px rgba(140,180,100,0.2);
        overflow: hidden;
        background: #182518;
        color: #c5e1a5;
    }

    /* Hide default UI */
    #MainMenu, footer { visibility: hidden; }

    @media (max-width: 980px) {
        .tracker-card {
            flex-direction: column;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    label {
        color: white !important;
    }
    input[type="text"],
    input[type="password"],
    input[type="number"],
    input[type="file"] {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="header-wrapper">
        <h1 class="main-app-title">🌱 GreenAI Comparometer</h1>
        <div class="tagline">Upload a .py or .ipynb file to track its carbon emissions.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="tracker-card">
      <div class="tracker-left">
        <h1>Carbon Tracker</h1>
        <div class="sub">Run arbitrary Python or notebook code and measure its carbon footprint using <strong>CarbonTracker</strong>.</div>
      </div>
      <div class="tracker-right">
        <div id="status_container">
          <div class="status-badge" id="status_badge">Ready to upload</div>
        </div>
    """,
    unsafe_allow_html=True,
)

# --- File Upload Section ---
api_key = st.text_input("🔑 Electricity Maps API Key", type="password")
epochs = st.number_input("🔁 Number of Epochs", min_value=1, max_value=100, value=5)

uploaded_code_file = st.file_uploader("📂 Upload Python or Notebook file", type=["py", "ipynb"], key="carbontracker_upload")
uploaded_dataset_files = st.file_uploader(
    "📦 Upload one or more dataset files (e.g., .csv, .json, .txt)",
    type=["csv", "json", "txt"],
    accept_multiple_files=True
)

if uploaded_code_file:
    # Create a unique session directory for this run
    session_dir = temp_root_dir / str(uuid.uuid4())
    session_dir.mkdir(parents=True, exist_ok=True)

    # Save the code file to the temporary session directory
    code_path = session_dir / uploaded_code_file.name
    with open(code_path, "wb") as f:
        f.write(uploaded_code_file.getbuffer())
    st.success(f"✅ Code file '{uploaded_code_file.name}' uploaded successfully.")
    
    # Save all dataset files
    if uploaded_dataset_files:
        for file in uploaded_dataset_files:
            dataset_path = session_dir / file.name
            with open(dataset_path, "wb") as f:
                f.write(file.getbuffer())
        st.success(f"✅ {len(uploaded_dataset_files)} dataset(s) uploaded successfully.")

    if st.button("🚀 Run with CarbonTracker"):
        try:
            # Change the current working directory to the temporary session folder
            os.chdir(session_dir)

            # Determine the file to run (convert .ipynb if needed)
            user_code_file_name = uploaded_code_file.name
            if user_code_file_name.endswith(".ipynb"):
                st.info("🔄 Converting notebook to Python script...")
                base_name = user_code_file_name.replace(".ipynb", "")
                subprocess.run(
                    ["jupyter", "nbconvert", "--to", "python", user_code_file_name, "--output", base_name],
                    check=True
                )
                user_script = f"{base_name}.py"
            else:
                user_script = user_code_file_name

            with open(user_script, "r", encoding="utf-8") as f:
                user_code = f.read()

            wrapped_code = f"""
from carbontracker.tracker import CarbonTracker
import sys

tracker = CarbonTracker(epochs={epochs})
tracker.epoch_start()

# === User code start ===
{user_code}

tracker.epoch_end()
tracker.stop()
"""

            wrapped_file_path = f"carbon_run_{str(uuid.uuid4())[:8]}.py"
            with open(wrapped_file_path, "w", encoding="utf-8") as f:
                f.write(wrapped_code)
            
            # --- Capture output and execute ---
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                exec(Path(wrapped_file_path).read_text(), {})

            result_output = output_buffer.getvalue()
            st.subheader("🖥 Console Output")
            st.text_area("", result_output, height=250)

            # --- Extract Energy & CO₂ ---
            energy_match = re.search(r"Energy:\s*([\d.]+)\s*kWh", result_output)
            co2_match = re.search(r"CO2eq:\s*([\d.]+)\s*g", result_output)

            if energy_match and co2_match:
                energy_kwh = float(energy_match.group(1))
                co2_kg = float(co2_match.group(1)) / 1000.0  # convert g → kg
                duration_match = re.search(r"Time:\s*(\d+):(\d+):(\d+)", result_output)
                if duration_match:
                    h, m, s = map(int, duration_match.groups())
                    duration_s = h * 3600 + m * 60 + s
                else:
                    duration_s = None

                result_row = {
                    "uploaded_filename": uploaded_code_file.name,
                    "tool_name": "CarbonTracker",
                    "co2_emissions_kg": co2_kg,
                    "energy_consumed_kwh": energy_kwh,
                    "duration_seconds": duration_s,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                # --- Save results for comparison ---
                if results_file.exists():
                    df_all = pd.read_csv(results_file)
                    df_all = pd.concat([df_all, pd.DataFrame([result_row])], ignore_index=True)
                    df_all.to_csv(results_file, index=False)
                else:
                    df_all = pd.DataFrame([result_row])
                    df_all.to_csv(results_file, index=False)

                st.success("📂 Results saved for comparison.")
                df_all.to_csv(results_file, index=False)

                st.markdown("### 📊Emission Summary ")
                st.dataframe(pd.DataFrame([result_row]).style.format({
                    "co2_emissions_kg": "{:.4f}",
                    "energy_consumed_kwh": "{:.4f}",
                    "duration_seconds": "{:.0f}"
                })) 
                st.success("📂 Results saved for comparison.")
            else:
                st.warning("⚠️ Could not extract emissions data from CarbonTracker output. Ensure your script ran and produced a summary.")

        except Exception as e:
            st.error(f"❌ Error running code: {e}")
        finally:
        # Change the working directory back to the original one before cleanup
        # This resolves the WinError 3 by moving out of the directory to be deleted
            os.chdir(original_wd)
        
        # Now, delete the temporary session directory safely
        try:
            shutil.rmtree(session_dir)
            print("🧹 Temporary session directory cleaned up.")
        except Exception as e:
            print(f"⚠️ Could not remove temporary directory: {e}")
# Close tracker-right and tracker-card divs
st.markdown("</div></div>", unsafe_allow_html=True)