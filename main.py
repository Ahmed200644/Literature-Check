import os
import sys
import argparse
from pathlib import Path

# Add project directory dynamically to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
LIT_REVIEW_DIR = PROJECT_ROOT / "multi_agent_lit_review"

if str(LIT_REVIEW_DIR) not in sys.path:
    sys.path.insert(0, str(LIT_REVIEW_DIR))

from agents import AILoopAgent, generate_charts

STATE_FILE = "final_papers_state.json"

research_question = (
    "Agentic AI systems for autonomous mathematical discovery, model formulation, "
    "parameter estimation, and optimization of Ordinary Differential Equations (ODEs), "
    "with emphasis on dynamical and ecological systems such as invasive species "
    "population modeling (e.g., predator-prey dynamics)."
)

queries = [
    'TITLE-ABS-KEY(("agentic AI" OR "AI agent" OR "LLM agent") AND ("ordinary differential equation*" OR "differential equation*" OR "dynamical system*" OR "mathematical model*") AND (discovery OR "model formulation" OR "parameter estimation" OR "parameter fitting" OR optimization OR simulation))',
    'TITLE-ABS-KEY(("agentic AI" OR "AI agent" OR "LLM agent") AND (ecological OR "population dynamics" OR "invasive species" OR "predator-prey" OR "Lotka-Volterra") AND (modeling OR simulation OR discovery))'
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="STEM Literature Reviewer Agent — Multi-Agent Research Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run continuous scheduler mode (executes automatically every Saturday at 8:00 AM).",
    )
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    agent = AILoopAgent(
        research_question=research_question,
        queries=queries,
        history_file="literature_history.json",
        state_file=STATE_FILE,
        output_dir=str(LIT_REVIEW_DIR),
        target_paper_count=50
    )

    if args.schedule:
        print("Starting AILoopAgent in continuous scheduled mode...", flush=True)
        agent.start_scheduling(day="saturday", at_time="08:00")
    else:
        print("Running AILoopAgent once immediately (test mode)...", flush=True)
        results = agent.run_cycle()
        print(f"Cycle finished successfully. Validated paper count: {results['validated_paper_count']}", flush=True)

if __name__ == "__main__":
    main()
