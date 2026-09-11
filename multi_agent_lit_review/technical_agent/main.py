import sys
import os
import argparse
import schedule
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from agents import (
    UnderstandingAgent,
    ModelSelectionAgent,
    FittingAgent,
    SimulationAgent,
    CritiqueAgent,
    TechnicalAILoopAgent
)

def scheduled_job(loop_agent):
    print("\n[Scheduler] Triggering monthly census data re-fit cycle...")
    loop_agent.run_cycle()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ecological Multi-Agent Modeling & Technical AI Loop")
    parser.add_argument("--schedule", action="store_true", help="Enable scheduled monthly re-fit mode (every 30 days)")
    args = parser.parse_args()

    understanding_real = {
        "species_prey": "hare",
        "species_predator": "lynx",
        "initial_prey": 30.0,
        "initial_predator": 4.0,
        "time_span_years": 90.0,
        "has_real_data": True,
        "missing_info": []
    }

    loop_agent = TechnicalAILoopAgent(understanding_real, data_file=str(CURRENT_DIR / "population_data.json"))

    if args.schedule:
        print("Starting TechnicalAILoopAgent in continuous scheduled mode (re-checking every 30 days)...")
        schedule.every(30).days.do(scheduled_job, loop_agent)
        # Execute immediately on start once
        loop_agent.run_cycle()
        print("Scheduler active. Waiting for scheduled triggers (Press Ctrl+C to stop)...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nScheduler terminated by user.")
    else:
        print("--- Running Technical AI Loop Agent (Single Run Mode) ---")
        loop_agent.run_cycle()
