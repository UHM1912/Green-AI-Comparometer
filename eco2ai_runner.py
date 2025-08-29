import sys
import os
import subprocess
from eco2ai import Tracker
import pandas as pd
import time
from pathlib import Path
import shutil
import uuid

def run_with_eco2ai(user_code_path):
    original_wd = Path.cwd()
    results_file = original_wd / "comparison_results.csv"

    session_dir = original_wd / "temp_sessions" / str(uuid.uuid4())
    session_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(user_code_path, session_dir)
    user_code_filename = Path(user_code_path).name

    os.chdir(session_dir)

    print(f"✅ Tracking emissions for: {user_code_filename}")

    if user_code_filename.endswith(".ipynb"):
        base_name = os.path.splitext(user_code_filename)[0]
        subprocess.run(
            ["jupyter", "nbconvert", "--to", "python", user_code_filename, "--output", base_name],
            check=True
        )
        run_file = f"{base_name}.py"
    else:
        run_file = user_code_filename

    tracker = Tracker(
        project_name="GreenAI Comparometer",
        experiment_description=f"Tracking {user_code_filename}"
    )

    try:
        tracker.start()
        exec(Path(run_file).read_text(), {})
        tracker.stop()
        print("✅ Execution complete.")

        # ✅ read results BEFORE cleanup
        emission_file = session_dir / "my_emission.csv"
        if emission_file.exists():
            df = pd.read_csv(emission_file)
            latest = df.iloc[-1]

            result_row = {
                "uploaded_filename": os.path.basename(user_code_path),
                "tool_name": "eco2AI",
                "co2_emissions_kg": latest.get("CO2_emissions(kg)", 0),
                "power_kwh": latest.get("power_consumption(kWh)", 0),
                "duration_s": latest.get("duration(s)", 0),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            if results_file.exists():
                df_results = pd.read_csv(results_file)
                df_results = pd.concat([df_results, pd.DataFrame([result_row])], ignore_index=True)
            else:
                df_results = pd.DataFrame([result_row])

            df_results.to_csv(results_file, index=False)
            print("📂 eco2AI results saved to comparison_results.csv")
        else:
            print("⚠️ my_emission.csv not found")

    except Exception as e:
        tracker.stop()
        print(f"❌ Error: {e}")

    finally:
        os.chdir(original_wd)
        shutil.rmtree(session_dir, ignore_errors=True)
