import os
import sys
import json
import time
import datetime
import schedule
from typing import List, Dict, Any, Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

stem_root = r"D:\Ahmed\study\research\E-labs\Week3\STEM-Literature-Agent"
if stem_root not in sys.path:
    sys.path.insert(0, stem_root)

try:
    from tools.scopus_search import search_scopus, extract_papers
except ImportError:
    search_scopus = None
    extract_papers = None

class AILoopAgent:
    """
    Automated Literature Monitoring and Review Maintenance Agent.
    Wraps full pipeline (Search -> Validation -> Synthesis -> Consolidation -> Document).
    Reuses exact research_question and queries passed from main.py (Single Source of Truth).
    """
    def __init__(
        self,
        research_question: Optional[str] = None,
        queries: Optional[List[str]] = None,
        history_path: str = "literature_history.json",
        baseline_path: str = "final_papers_state.json",
        output_dir: str = ".",
        **kwargs
    ):
        if "history_file" in kwargs:
            history_path = kwargs["history_file"]
        if "state_file" in kwargs:
            baseline_path = kwargs["state_file"]

        if research_question is None or queries is None:
            import main
            self.research_question = research_question or main.research_question
            self.queries = queries or main.queries
        else:
            self.research_question = research_question
            self.queries = queries

        self.history_path = history_path
        self.baseline_path = baseline_path
        self.output_dir = output_dir
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
                    if isinstance(data, list):
                        baseline_papers = data
                    elif isinstance(data, dict):
                        baseline_papers = data.get('papers', [])

            for p in baseline_papers:
                doi = (p.get('doi') or '').strip().lower()
                title = (p.get('title') or '').strip().lower()
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
            if d:
                seen_dois.add(d.strip().lower())
        for t in new_titles:
            if t:
                seen_titles.add(t.strip().lower())

        hist["last_run_timestamp"] = datetime.datetime.now().isoformat()
        hist["already_seen_dois"] = sorted(list(seen_dois))
        hist["already_seen_titles"] = sorted(list(seen_titles))
        hist["total_historical_papers"] = len(hist["already_seen_dois"])

        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(hist, f, indent=2)

    def run_cycle(self) -> Dict[str, Any]:
        """Runs single differential literature update cycle using main.py queries."""
        print("\n=== AILoopAgent Pipeline Execution Cycle ===", flush=True)
        print(f"Research Question: {self.research_question[:90]}...", flush=True)
        print(f"Executing {len(self.queries)} query(s) against Scopus API...", flush=True)

        hist = self.load_history()
        seen_dois = set(hist.get("already_seen_dois", []))
        seen_titles = set(hist.get("already_seen_titles", []))

        all_found = []
        if search_scopus and extract_papers:
            for idx, q in enumerate(self.queries, 1):
                try:
                    print(f"Running Scopus Query {idx}: {q[:80]}...", flush=True)
                    raw_resp = search_scopus(q, count=25)
                    extracted = extract_papers(raw_resp)
                    all_found.extend(extracted)
                    print(f" -> Query {idx} returned {len(extracted)} candidates.", flush=True)
                    time.sleep(1) # Polite pause between queries
                except Exception as e:
                    print(f" -> Query {idx} search error: {e}", flush=True)

        dedup_found = {}
        for p in all_found:
            doi = (p.get('doi') or '').strip().lower()
            title = (p.get('title') or '').strip().lower()
            key = doi or title
            if key and key not in dedup_found:
                dedup_found[key] = p
        unique_candidates = list(dedup_found.values())

        print(f"\n[1] Total candidates found by search (before baseline dedup): {len(unique_candidates)}", flush=True)

        new_candidates = []
        already_seen_count = 0
        for p in unique_candidates:
            doi = (p.get('doi') or '').strip().lower()
            title = (p.get('title') or '').strip().lower()

            if (doi and doi in seen_dois) or (title and title in seen_titles):
                already_seen_count += 1
                continue
            new_candidates.append(p)

        print(f"[2] Candidates filtered out as already-seen: {already_seen_count}", flush=True)
        print(f"[3] Genuinely NEW papers to process: {len(new_candidates)}", flush=True)

        baseline_papers = []
        if os.path.exists(self.baseline_path):
            with open(self.baseline_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                baseline_papers = data if isinstance(data, list) else data.get('papers', [])

        processed_new = new_candidates

        for p in processed_new:
            p['is_new_in_latest_run'] = True
        for p in baseline_papers:
            p['is_new_in_latest_run'] = False

        cumulative_papers = baseline_papers + processed_new

        date_str = datetime.datetime.now().strftime("%Y_%m_%d")
        comp_path = os.path.join(self.output_dir, f"Comprehensive_Review_Updated_{date_str}.docx")
        weekly_path = os.path.join(self.output_dir, f"Weekly_Summary_Report_{date_str}.docx")

        self.generate_comprehensive_docx(cumulative_papers, comp_path)
        self.generate_weekly_summary_docx(processed_new, weekly_path)

        new_dois = [p.get('doi', '') for p in processed_new]
        new_titles = [p.get('title', '') for p in processed_new]
        self.save_history(new_dois, new_titles)

        final_hist = self.load_history()
        final_count = len(final_hist.get("already_seen_dois", []))

        print(f"\n[4] Confirmed Word files generated:\n - {comp_path}\n - {weekly_path}", flush=True)
        print(f"[5] Final literature_history.json paper count: {final_count}", flush=True)

        return {
            "status": "success",
            "total_found": len(unique_candidates),
            "already_seen": already_seen_count,
            "new_count": len(processed_new),
            "comprehensive_path": comp_path,
            "weekly_path": weekly_path,
            "final_history_count": final_count
        }

    def generate_comprehensive_docx(self, papers: List[Dict[str, Any]], output_path: str):
        doc = Document()
        doc.add_heading('Comprehensive Literature Review (Cumulative)', level=0)
        doc.add_paragraph(f"Total Cumulative Papers: {len(papers)}")

        for p in papers:
            title_p = doc.add_paragraph()
            r = title_p.add_run(f"• {p.get('title', 'Untitled')}")
            if p.get('is_new_in_latest_run', False):
                r.font.color.rgb = RGBColor(0, 85, 204) # #0055CC blue
                r.font.bold = True

            meta_p = doc.add_paragraph()
            meta_p.add_run(f"  Authors: {p.get('authors', 'N/A')} | Year: {p.get('year', 'N/A')} | DOI: {p.get('doi', 'N/A')}")

            summary = p.get('summary') or p.get('abstract', '')
            if summary:
                sum_p = doc.add_paragraph()
                r_sum = sum_p.add_run(f"  Summary: {summary[:300]}...")
                if p.get('is_new_in_latest_run', False):
                    r_sum.font.color.rgb = RGBColor(0, 85, 204)

        doc.save(output_path)

    def generate_weekly_summary_docx(self, new_papers: List[Dict[str, Any]], output_path: str):
        doc = Document()
        for section in doc.sections:
            section.orientation = 1 # Landscape
            new_w, new_h = section.page_height, section.page_width
            section.page_width = new_w
            section.page_height = new_h

        h1 = doc.add_heading('Weekly Differential Literature Report', level=0)
        h1.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph(f"Generated Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph(f"Newly Discovered Validated Papers: {len(new_papers)}")

        if not new_papers:
            doc.add_paragraph("No new literature matching inclusion criteria was discovered during this cycle.")
        else:
            table = doc.add_table(rows=1, cols=4)
            hdr_cells = table.rows[0].cells
            headers = ["Title and Authors", "Relevance and Key Innovation", "Methodology / ODE Focus", "DOI / Reference"]
            widths = [Inches(2.5), Inches(3.0), Inches(2.5), Inches(1.5)]
            for i, (t, w) in enumerate(zip(headers, widths)):
                hdr_cells[i].text = t
                hdr_cells[i].width = w

            for paper in new_papers:
                row_cells = table.add_row().cells
                for cell, w in zip(row_cells, widths):
                    cell.width = w
                row_cells[0].text = f"{paper.get('title', 'N/A')}\n\nAuthors: {paper.get('authors', 'N/A')}"
                row_cells[1].text = f"{paper.get('relevance_summary', paper.get('summary', 'N/A'))}\n\nInnovation: {paper.get('key_innovation', 'N/A')}"
                row_cells[2].text = f"{paper.get('methodology', 'N/A')}"
                row_cells[3].text = f"{paper.get('doi', 'N/A')}"

        doc.save(output_path)

    def start_scheduling(self, day: str = "saturday", at_time: str = "08:00"):
        print(f"Scheduling AILoopAgent to run every {day} at {at_time}...")
        getattr(schedule.every(), day.lower()).at(at_time).do(self.run_cycle)

        while True:
            schedule.run_pending()
            time.sleep(60)

    def start_scheduler(self):
        self.start_scheduling()
