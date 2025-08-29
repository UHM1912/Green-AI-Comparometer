import sys
import os
import subprocess
import pandas as pd
import time
from pathlib import Path
from carbontracker.tracker import CarbonTracker
import glob
import shutil
import uuid

# Shared results file
results_file = Path("comparison_results.csv")

def run_with_carbontracker(user_code_path, epochs=5):
    # Store the original working directory
    original_wd = Path.cwd()
    
    # Create a temporary session directory
    temp_root_dir = original_wd / "temp_sessions"
    temp_root_dir.mkdir(parents=True, exist_ok=True)
    session_dir = temp_root_dir / str(uuid.uuid4())
    session_dir.mkdir(parents=True, exist_ok=True)

    # Copy the user's code to the temporary directory
    user_code_filename = Path(user_code_path).name
    shutil.copy(user_code_path, session_dir)
    
    # Change the current working directory to the temporary session directory
    os.chdir(session_dir)

    print(f"✅ Tracking emissions with CarbonTracker for: {user_code_filename}")

    # Convert .ipynb to .py if needed
    if user_code_filename.endswith(".ipynb"):
        print("🔄 Converting notebook to Python script...")
        base_name = os.path.splitext(user_code_filename)[0]
        subprocess.run([
            "jupyter", "nbconvert", "--to", "python", user_code_filename,
            "--output", base_name
        ], check=True)
        run_file = f"{base_name}.py"
    else:
        run_file = user_code_filename

    # Create log directory for CarbonTracker inside the session dir
    log_dir = Path("carbontracker_logs")
    log_dir.mkdir(exist_ok=True)
    
    tracker = CarbonTracker(epochs=epochs, monitor_epochs=epochs, output_dir=str(log_dir))

    try:
        with open(run_file, "r", encoding="utf-8") as f:
            code = f.read()

        for _ in range(epochs):
            tracker.epoch_start()
            exec(code, {})
            tracker.epoch_end()

        tracker.stop()
        print("✅ Execution complete.")

    except Exception as e:
        tracker.stop()
        print(f"❌ Error while running code: {e}")
        return

    finally:
        # Change the working directory back to the original one before cleanup
        os.chdir(original_wd)
        # Now, delete the temporary session directory safely
        try:
            shutil.rmtree(session_dir)
            print("🧹 Temporary session directory cleaned up.")
        except Exception as e:
            print(f"⚠️ Could not remove temporary directory: {e}")

    try:
        # Get the latest CarbonTracker log file from the temporary directory
        log_files = glob.glob(str(session_dir / log_dir / "*.csv"))
        if not log_files:
            print("⚠️ No CarbonTracker log file found.")
            return

        latest_log = max(log_files, key=os.path.getctime)
        df_log = pd.read_csv(latest_log)

        # Take the final recorded row
        latest = df_log.iloc[-1]
        duration_s = latest.get("duration (s)", 0)
        energy_kwh = latest.get("energy_consumed (kWh)", 0)
        co2_kg = latest.get("emissions (kg)", 0)

        print("\n📊 Emission Summary (CarbonTracker):")
        print(f"🕒 Duration: {duration_s} seconds")
        print(f"🔋 Energy: {energy_kwh} kWh")
        print(f"🌍 CO₂: {co2_kg} kg")

        # Save to comparison file
        result_row = {
            "uploaded_filename": os.path.basename(user_code_path),
            "tool_name": "CarbonTracker",
            "co2_emissions_kg": co2_kg,
            "power_kwh": energy_kwh,
            "duration_s": duration_s,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        if results_file.exists():
            df_results = pd.read_csv(results_file)
            df_results = pd.concat([df_results, pd.DataFrame([result_row])], ignore_index=True)
        else:
            df_results = pd.DataFrame([result_row])

        df_results.to_csv(results_file, index=False)
        print("📂 Results saved to comparison_results.csv")
        print(f"📄 Detailed CarbonTracker log saved at: {latest_log}")

    except Exception as e:
        print("⚠️ Could not read or store CarbonTracker results:", e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python carbontracker_runner.py <file.py or file.ipynb>")
    else:
        run_with_carbontracker(sys.argv[1])