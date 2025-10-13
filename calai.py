"""
calai.py
A barebones script to run the entire agent pipeline in sequence with timing.
This script executes each step individually without a loop.

Usage:
1. In one terminal, run the Flask server: `python app.py`
2. In a second terminal, run this script: `python calai.py "path/to/image.jpg"`
"""

import sys
import subprocess
import os

def main():
    # Check for the image path argument
    if len(sys.argv) < 2:
        print("Usage: python calai.py \"<path_to_your_image>\"")
        sys.exit(1)

    image_path = sys.argv[1]
    session_folder = sys.argv[2] if len(sys.argv) > 2 else None

    # --- Define Hardcoded Filenames as used by the agents ---
    confirmed_food_file = "final_confirmed_output.json"
    verified_volumes_file = "verified_volumes.json"
    agent1_output_file = "agent1_output.json"
    agent2_output_file = "agent2_output.json"
    agent3_output_file = "agent3_output.json" 
    density_pdf_file = "food_density_database.pdf"

    print("🚀 Starting Barebones Pipeline Execution...")

    try:
        # --- Step 1: VLM Analysis (script2.py) ---
        print("\n--- Running Step 1: VLM Analysis (script2.py) ---")
        cmd_step1 = ["python", "script2.py", image_path]
        print(f"Command: {' '.join(cmd_step1)}")
        subprocess.run(cmd_step1, check=True, text=True)
        print("--- Step 1 Completed ---")

        # --- Step 2: Volume Verification ---
        print("\n--- Running Step 2: Volume Verification ---")
        cmd_step2 = ["python", "volume_verify.py", confirmed_food_file, image_path]
        print(f"Command: {' '.join(cmd_step2)}")
        subprocess.run(cmd_step2, check=True, text=True)
        print("--- Step 2 Completed ---")

        # --- Step 3: Food Decomposition (Agent 1) ---
        print("\n--- Running Step 3: Food Decomposition (Agent 1) ---")
        cmd_step3 = ["python", "agent1_decomposer.py", verified_volumes_file]
        print(f"Command: {' '.join(cmd_step3)}")
        subprocess.run(cmd_step3, check=True, text=True)
        print("--- Step 3 Completed ---")

        # --- Step 4: Mass Calculation (Agent 2) ---
        print("\n--- Running Step 4: Mass Calculation (Agent 2) ---")
        cmd_step4 = ["python", "agent2_masscalculator.py", density_pdf_file, agent1_output_file]
        print(f"Command: {' '.join(cmd_step4)}")
        subprocess.run(cmd_step4, check=True, text=True)
        print("--- Step 4 Completed ---")

        # --- Step 5: Nutritional Profiling (Agent 3) ---
        print("\n--- Running Final Step 5: Nutritional Profiling (Agent 3) ---")
        print(f"DEBUG: About to run Agent 3 with session_folder = '{session_folder}'")
        print(f"DEBUG: agent2_output_file exists: {os.path.exists(agent2_output_file)}")
        cmd_step5 = ["python", "agent3_nutritioncalculator.py", agent2_output_file, session_folder]
        print(f"Command: {' '.join(cmd_step5)}")
        subprocess.run(cmd_step5, check=True, text=True)
        print("--- Final Step 5 Completed ---")

        # --- Success Message ---
        print("\nFull Pipeline Completed Successfully! ")
        print(f"Final output is in: {agent3_output_file}")
        print("\n--- Running Final Confirmation Print ---")
        subprocess.run(["python", "-c", "print(' DONE - All agents completed successfully!')"], check=True)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: A command failed with exit code {e.returncode}. The pipeline has stopped.")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: A script was not found. Please check the file name and path.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()