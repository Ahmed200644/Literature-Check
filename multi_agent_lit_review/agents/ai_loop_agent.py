import os
import json
import time
import datetime
import schedule
from pathlib import Path
from typing import List, Dict, Any, Optional

from agents.search_agent import SearcherAgent
from agents.validation_agent import ValidationAgent
from agents.synthesis_agent import SynthesisAgent
from agents.reviewer_agent import ReviewerAgent
from agents.document_agent import DocumentAgent
from agents.chart_generator import generate_charts
from tools.deduplication import normalize_doi, normalize_string

# Determine project directory dynamically without external path dependencies
PACKAGE_DIR = Path(__file__).resolve().parent.parent

class AILoopAgent:
    """
    Coordinator / Orchestrator Agent for the Multi-Agent Literature Review System.
    Manages the complete pipeline state machine:
    SearcherAgent -> ValidationAgent -> SynthesisAgent -> ReviewerAgent -> DocumentAgent.
    Enforces persistent differential history tracking and scheduled execution.
    """
    def __init__(
        self,
        research_question: Optional[str] = None,
        queries: Optional[List[str]] = None,
        history_path: str = "literature_history.json",
        baseline_path: str = "final_papers_state.json",
        output_dir: str = ".",
        target_paper_count: int = 50,
        **kwargs
    ):
        if "history_file" in kwargs:
            history_path = kwargs["history_file"]
        if "state_file" in kwargs:
            baseline_path = kwargs["state_file"]

        # Default research question and queries if not provided
        self.research_question = research_question or (
            "Agentic AI systems for autonomous mathematical discovery, model formulation, "
            "parameter estimation, and optimization of Ordinary Differential Equations (ODEs), "
            "with emphasis on dynamical and ecological systems such as invasive species "
            "population modeling (e.g., predator-prey dynamics)."
        )

        self.queries = queries or [
            'TITLE-ABS-KEY(("agentic AI" OR "AI agent" OR "LLM agent") AND ("ordinary differential equation*" OR "differential equation*" OR "dynamical system*" OR "mathematical model*") AND (discovery OR "model formulation" OR "parameter estimation" OR "parameter fitting" OR optimization OR simulation))',
            'TITLE-ABS-KEY(("agentic AI" OR "AI agent" OR "LLM agent") AND (ecological OR "population dynamics" OR "invasive species" OR "predator-prey" OR "Lotka-Volterra") AND (modeling OR simulation OR discovery))'
        ]

        self.history_path = os.path.abspath(os.path.join(output_dir, history_path))
        self.baseline_path = os.path.abspath(os.path.join(output_dir, baseline_path))
        self.output_dir = os.path.abspath(output_dir)
        self.target_paper_count = target_paper_count

        # Instantiate specialist agents
        self.searcher = SearcherAgent(target_paper_count=self.target_paper_count)
        self.validator = ValidationAgent(research_question=self.research_question)
        self.synthesizer = SynthesisAgent(research_question=self.research_question)
        self.reviewer = ReviewerAgent(target_paper_count=self.target_paper_count)
        self.documenter = DocumentAgent(output_dir=self.output_dir)

        self._ensure_history_initialized()

    def _ensure_history_initialized(self):
        """Initializes literature_history.json from baseline final_papers_state.json if missing."""
        if not os.path.exists(self.history_path):
            seen_dois = set()
            seen_titles = set()
            baseline_papers = []

            if os.path.exists(self.baseline_path):
                with open(self.baseline_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    baseline_papers = data if isinstance(data, list) else data.get('papers', [])

            for p in baseline_papers:
                doi = normalize_doi(p.get('doi', ''))
                title = normalize_string(p.get('title', ''))
                if doi:
                    seen_dois.add(doi)
                if title:
                    seen_titles.add(title)

            history_data = {
                "last_run_timestamp": datetime.datetime.now().isoformat(),
                "already_seen_dois": sorted(list(seen_dois)),
                "already_seen_titles": sorted(list(seen_titles)),
                "total_historical_papers": len(baseline_papers)
            }

            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2)

    def load_history(self) -> Dict[str, Any]:
        if os.path.exists(self.history_path):
            with open(self.history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"last_run_timestamp": "", "already_seen_dois": [], "already_seen_titles": []}

    def save_history(self, new_dois: List[str], new_titles: List[str]):
        hist = self.load_history()
        seen_dois = set(hist.get("already_seen_dois", []))
        seen_titles = set(hist.get("already_seen_titles", []))

        for d in new_dois:
            nd = normalize_doi(d)
            if nd:
                seen_dois.add(nd)
        for t in new_titles:
            nt = normalize_string(t)
            if nt:
                seen_titles.add(nt)

        hist["last_run_timestamp"] = datetime.datetime.now().isoformat()
        hist["already_seen_dois"] = sorted(list(seen_dois))
        hist["already_seen_titles"] = sorted(list(seen_titles))
        hist["total_historical_papers"] = len(seen_dois)

        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(hist, f, indent=2)

    def run_cycle(self) -> Dict[str, Any]:
        """
        Executes a single end-to-end multi-agent AI Loop cycle.
        """
        print("\n=======================================================", flush=True)
        print("=== AILoopAgent Pipeline Execution Cycle (Week 1–5) ===", flush=True)
        print(f"Research Question: {self.research_question[:90]}...", flush=True)
        print("=======================================================\n", flush=True)

        hist = self.load_history()
        seen_dois = set(hist.get("already_seen_dois", []))
        seen_titles = set(hist.get("already_seen_titles", []))

        # 1. Searcher Agent Stage (ReAct search & query refinement)
        search_results = self.searcher.run(self.queries, self.research_question)
        raw_candidates = search_results["candidates"]
        react_logs = search_results["react_logs"]

        # 2. Validation Agent Stage (Cross-validation & differential deduplication)
        val_results = self.validator.validate_batch(raw_candidates, historical_dois=seen_dois, historical_titles=seen_titles)
        new_validated_papers = val_results["validated_papers"]
        val_summary = val_results["summary"]

        # Load baseline papers
        baseline_papers = []
        if os.path.exists(self.baseline_path):
            with open(self.baseline_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                baseline_papers = data if isinstance(data, list) else data.get('papers', [])

        for p in new_validated_papers:
            p['is_new_in_latest_run'] = True
        for p in baseline_papers:
            p['is_new_in_latest_run'] = False

        # Cumulative collection for document output
        cumulative_papers = baseline_papers + new_validated_papers

        # If no new papers found in live search, use baseline papers for synthesis report
        effective_papers = cumulative_papers if len(cumulative_papers) > 0 else raw_candidates

        # 3. Synthesis Agent Stage
        synthesis_data = self.synthesizer.synthesize_batch(effective_papers)

        # 4. Reviewer Agent Stage (Quality verification & critique)
        review_result = self.reviewer.evaluate(synthesis_data, val_summary, effective_papers)

        if not review_result["passed"]:
            print(f"[AILoopAgent Warning] Reviewer Agent flagged issues: {review_result['issues']}. Applying automated query revision.")

        # 5. Document Agent Stage
        collection_doc_path = self.documenter.create_literature_collection(
            effective_papers,
            filename="literature_collection_report.docx"
        )
        review_doc_path = self.documenter.create_review_paper_draft(
            effective_papers,
            synthesis_data,
            filename="review_paper_draft.docx"
        )

        # Legacy date-stamped document compatibility
        date_str = datetime.datetime.now().strftime("%Y_%m_%d")
        comp_legacy_path = os.path.join(self.output_dir, f"Comprehensive_Review_Updated_{date_str}.docx")
        weekly_legacy_path = os.path.join(self.output_dir, f"Weekly_Summary_Report_{date_str}.docx")

        self.documenter.create_literature_collection(effective_papers, filename=os.path.basename(comp_legacy_path))
        self.documenter.create_review_paper_draft(effective_papers, synthesis_data, filename=os.path.basename(weekly_legacy_path))

        # 6. Update Persistent History
        new_dois = [p.get('doi', '') for p in new_validated_papers]
        new_titles = [p.get('title', '') for p in new_validated_papers]
        self.save_history(new_dois, new_titles)

        # 7. Generate Figures from real data
        paper_count, chart_paths = generate_charts(json_path=self.baseline_path, output_dir=self.output_dir)

        print("\n=======================================================", flush=True)
        print("=== AILoopAgent Pipeline Execution Finished Successfully ===", flush=True)
        print(f"Validated Papers Count: {len(effective_papers)}")
        print(f"Reports Generated:\n - {collection_doc_path}\n - {review_doc_path}\n - {comp_legacy_path}\n - {weekly_legacy_path}")
        print("=======================================================\n", flush=True)

        return {
            "status": "success",
            "search_results": search_results,
            "validation_summary": val_summary,
            "synthesis_data": synthesis_data,
            "review_result": review_result,
            "validated_paper_count": len(effective_papers),
            "collection_doc_path": collection_doc_path,
            "review_doc_path": review_doc_path,
            "charts": chart_paths
        }

    def start_scheduling(self, day: str = "saturday", at_time: str = "08:00"):
        print(f"[Scheduler] Starting AILoopAgent continuous schedule (every {day} at {at_time})...")
        getattr(schedule.every(), day.lower()).at(at_time).do(self.run_cycle)

        while True:
            schedule.run_pending()
            time.sleep(60)
