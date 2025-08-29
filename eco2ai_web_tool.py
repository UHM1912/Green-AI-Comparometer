import streamlit as st
import os
import subprocess
from eco2ai import Tracker
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

st.set_page_config(page_title="GreenAI Comparometer - eco2AI Tracker", layout="centered")

# === Unified CSS styling ===
st.markdown(
    """
    <style>
    /* === Background with stronger dark overlay === */
    .stApp {
        background: url('https://www.thedigitalspeaker.com/content/images/2023/02/Sustainable-AI-greener-future.jpg') center/cover fixed no-repeat;
        position: relative;
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
        color: #c7d9b9;
        padding-top: 0;
        margin: 0;
        min-height: 100vh;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(20, 30, 15, 0.75);  /* Darker greenish overlay */
        backdrop-filter: blur(6px);
        pointer-events: none;
        z-index: 0;
    }
    /* ensure main content sits above overlay */
    [data-testid="stAppViewContainer"] > .main, .block-container {
        position: relative;
        z-index: 1;
        padding-top: 1rem;
    }

    /* === Header/title === */
    .header-wrapper {
        max-width: 1000px;
        margin: 0 auto 0.5rem;
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 0.5rem 1rem;
        justify-content: center;
        flex-wrap: wrap;
    }
    .title-block {
        text-align: center;
    }
    .title-block h1 {
        margin: 0;
        font-size: 2.4rem;
        color: #a0d468;  /* lighter green */
        line-height: 1.05;
        text-shadow: 0 0 6px #335522aa;
    }
    .title-block .tagline {
        font-size: 1rem;
        font-style: italic;
        color: #8cbf40;
        margin-top: 4px;
        text-shadow: 0 0 4px #233311cc;
    }

    /* === Tracker card === */
    .tracker-card {
        max-width: 1000px;
        margin: 1.75rem auto 2rem;
        display: flex;
        flex-wrap: wrap;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 40px 90px rgba(0, 40, 0, 0.9);
        background: linear-gradient(145deg, #223322 0%, #1b2b1b 100%);
        border: 2px solid #4a7a33;
    }
    .tracker-left, .tracker-right {
        padding: 2.5rem 2rem;
        flex: 1;
        min-width: 320px;
        box-sizing: border-box;
        color: #a9d18e;
    }
    .tracker-left {
        background: linear-gradient(135deg,#2e4d20 0%,#3b6e28 100%);
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.75rem;
        border-right: 2px solid #5aa236;
    }
    .tracker-left h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #c0f06f;
        text-shadow: 0 0 8px #9ecc43cc;
    }
    .tracker-left .sub {
        font-size: 1rem;
        font-style: italic;
        color: #8bc34a;
        line-height: 1.4;
        margin: 0;
    }
      
    .title-block h1 {
    margin: 0;
    font-size: 2.4rem;
    color: white;  /* Changed from #1f4d0f */
    line-height: 1.05;
}
.title-block .tagline {
    font-size: 1rem;
    font-style: italic;
    color: white; /* Changed from #2f6a2f */
    margin-top: 4px;
}

.tracker-left h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    color: white;  /* Changed from #1f4d0f */
}
.tracker-left .sub {
    font-size: 1rem;
    font-style: italic;
    color: white; /* Changed from #2f6a2f */
    line-height: 1.4;
    margin: 0;
}

    /* Uploader & run area */
    .upload-wrapper {
        background: #1c2a14;
        border: 1px solid #497b24;
        border-radius: 12px;
        padding: 1rem 1rem 0.5rem;
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 0.5rem;
        color: #a6c76c;
    }
    .upload-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        color: #89a04f;
        font-weight: 500;
    }
    .upload-instruction {
        background: white;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 4px 0 8px;
        font-size: 0.95rem;
        color: #a8d77a;
    }
    .file-uploader-wrapper > div {
        border-radius: 12px !important;
        overflow: hidden;
    }
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        background: linear-gradient(135deg,#629f38,#2c5b11) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 14px 40px rgba(50,90,20,0.45) !important;
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
        background: #32521c;
        color: #a5e75b;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 12px;
        box-shadow: 0 0 6px #7ccd34;
        text-shadow: 0 0 2px #9dde3a;
    }

    /* Console & dataframe */
    .stCodeBlock pre {
        border-radius: 10px !important;
        padding: 14px !important;
        background: #0b170b !important;
        color: #b8e986 !important;
        font-size: 0.9rem !important;
        box-shadow: 0 0 15px #539a18aa;
    }
    .stDataFrame > div {
        border-radius: 12px;
        box-shadow: 0 0 20px #84a43ccc;
        overflow: hidden;
        border: 2px solid #5d8b2d;
        background: #182a10cc !important;
        color: #d4ef9e !important;
    }
    /* Table font color */
    table.dataframe tbody tr td {
        color: #c9e98a !important;
    }
    table.dataframe thead tr th {
        color: #e3f2b5 !important;
        background-color: #334d11 !important;
    }

    /* Hide default menu/footer */
    #MainMenu, footer {visibility: hidden;}

    /* Responsive */
    @media (max-width: 980px) {
        .tracker-card {
            flex-direction: column;
        }
        .tracker-left, .tracker-right {
            min-width: 100%;
        }
        .header-wrapper {
            flex-direction: column;
            gap: 8px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* Your existing styles ... */

    /* Make file uploader label text white */
    div[data-testid="stFileUploader"] > label {
        color: white !important;
        font-weight: 600;
        font-size: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* ... your other styles ... */

    /* Make file uploader label text white */
    div[data-testid="stFileUploader"] > label {
        color: white !important;
        font-weight: 600;
        font-size: 1rem;
    }

    /* Make success message text white */
    .stAlert.stAlert-success > div {
        color: white !important;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# === Title ===
st.markdown(
    """
    <div class="header-wrapper">
        <div class="title-block">
            <h1>🌱 GreenAI Comparometer</h1>
            <div class="tagline">Code Smart. Code Green. Compare to Care.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
# === Tracker card ===
st.markdown(
    """
    <div class="tracker-card">
      <div class="tracker-left">
        <h1>Eco2ai Emission Tracker</h1>
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
    # Create a fresh session dir for this run
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

    if st.button("🚀 Run with eco2AI"):
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

            tracker = Tracker(
                project_name="GreenAI Comparometer",
                experiment_description="eco2AI Web Tracker"
            )
            tracker.start()

            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                exec(Path(run_file).read_text(), {})

            tracker.stop()
            st.success("✅ Emission tracking completed.")

            # ✅ Save results BEFORE cleanup
            emission_file = Path("my_emission.csv")
            if emission_file.exists():
                df = pd.read_csv(emission_file)
                st.subheader("📊 Latest Emission Data:")
                st.dataframe(df.tail(1))

                last_row = df.tail(1).iloc[0]
                result_row = {
                    "uploaded_filename": uploaded_code_file.name,
                    "tool_name": "eco2AI",
                    "co2_emissions_kg": last_row.get("CO2_emissions(kg)", 0),
                    "power_kwh": last_row.get("power_consumption(kWh)", 0),
                    "duration_s": last_row.get("duration(s)", 0),
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
                st.warning("⚠️ my_emission.csv not found.")

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

        finally:
            os.chdir(original_wd)
            shutil.rmtree(session_dir, ignore_errors=True)

# Close tracker card
st.markdown("</div></div>", unsafe_allow_html=True)
