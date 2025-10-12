"""
run_simple_pipeline.py
A barebones script to run the entire agent pipeline in sequence with timing.
This script overwrites previous output files on each run.

Usage:
1. In one terminal, run the Flask server: `python app.py`
2. In a second terminal, run this script: `python run_simple_pipeline.py "path/to/image.jpg"`
"""

import sys
import subprocess
import time
import os


# In calai.py / run_simple_pipeline.py

def main():
    # Reverted to only check for the image path argument
    if len(sys.argv) < 2:
        print("Usage: python calai.py \"<path_to_your_image>\"")
        sys.exit(1)

    image_path = sys.argv[1]
    session_folder = sys.argv[2] if len(sys.argv) > 2 else None


    # --- Define Hardcoded Filenames as used by the agents ---
    confirmed_food_file = "final_confirmed_output.json"
    agent1_output_file = "agent1_output.json"
    agent2_output_file = "agent2_output.json"
    # The final output name is now fixed by agent3 itself
    agent3_output_file = "agent3_output.json" 
    density_pdf_file = "food_density_database.pdf"

    # --- List of Commands to Run in Order (using hardcoded outputs) ---
    commands_to_run = [
        ["python", "script2.py", image_path],
        ["python", "agent1_decomposer.py", confirmed_food_file],
        ["python", "agent2_masscalculator.py", density_pdf_file, agent1_output_file],
        # Agent 3 now uses its own hardcoded output name, so we don't pass it
        ["python", "agent3_nutritioncalculator.py", agent2_output_file] + ([session_folder] if session_folder else [])
    ]

    print("🚀 Starting Barebones Pipeline Execution...")

    try:
        for i, command in enumerate(commands_to_run, 1):
            print(f"\n--- Running Step {i}: {' '.join(command)} ---")
            # This will run interactively, showing prompts from the dialogue agent
            subprocess.run(command, check=True, text=True)
            print(f"--- Step {i} Completed ---")

        print("\n🎉🎉🎉 Full Pipeline Completed Successfully! 🎉🎉🎉")
        # Print the fixed output file name for the router to find
        print(f"Final output is in: {agent3_output_file}")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: A command failed with exit code {e.returncode}.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()