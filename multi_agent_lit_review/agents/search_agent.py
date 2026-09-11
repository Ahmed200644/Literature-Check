import time
from typing import List, Dict, Any, Tuple
from tools.scopus_search import search_scopus, extract_papers

class SearcherAgent:
    """
    SearcherAgent: Specialist agent responsible for query generation,
    query refinement, execution against academic databases (Scopus / Offline fallback),
    and ReAct observation-driven search retries.
    """
    def __init__(self, target_paper_count: int = 50):
        self.target_paper_count = target_paper_count

    def run(self, queries: List[str], research_question: str) -> Dict[str, Any]:
        """
        Executes literature search across provided queries with ReAct query refinement loop.

        Returns:
            Dict[str, Any] containing candidate papers, logs, and execution status.
        """
        all_candidates = []
        react_logs = []
        active_queries = list(queries)

        print(f"[SearcherAgent] Starting search across {len(active_queries)} queries (Target: {self.target_paper_count} papers)...")

        for idx, q in enumerate(active_queries, 1):
            thought = f"Executing query #{idx} to search for literature matching research question."
            print(f"[SearcherAgent ReAct Thought] {thought}")

            action = f"Querying Scopus API (or offline fallback) with: {q[:75]}..."
            print(f"[SearcherAgent ReAct Action] {action}")

            raw_resp, data_source = search_scopus(q, count=25)
            extracted = extract_papers(raw_resp, source_label=data_source)

            observation = {
                "query_index": idx,
                "data_source": data_source,
                "candidates_returned": len(extracted)
            }
            print(f"[SearcherAgent ReAct Observation] Returned {len(extracted)} candidates via {data_source}.")

            # ReAct Decision Logic
            if len(extracted) == 0:
                decision = "Zero papers returned. Broadening query parameters for secondary attempt."
                next_action = "Refine search query with expanded OR terms."
                print(f"[SearcherAgent ReAct Decision] {decision}")
                
                # Dynamic query refinement (Broadening)
                refined_q = q.replace("AND", "OR")
                raw_resp_ref, ds_ref = search_scopus(refined_q, count=25)
                extracted_ref = extract_papers(raw_resp_ref, source_label=ds_ref)
                extracted.extend(extracted_ref)
                observation["candidates_after_refinement"] = len(extracted)
            else:
                decision = "Search returned candidate papers successfully."
                next_action = "Proceed to next query or pass candidates to ValidationAgent."

            react_logs.append({
                "step": idx,
                "thought": thought,
                "action": action,
                "observation": observation,
                "decision": decision,
                "next_action": next_action
            })

            all_candidates.extend(extracted)
            time.sleep(0.5)

        return {
            "status": "success",
            "candidates": all_candidates,
            "total_raw_found": len(all_candidates),
            "target_paper_count": self.target_paper_count,
            "react_logs": react_logs
        }
