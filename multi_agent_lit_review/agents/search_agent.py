import time
from typing import List, Dict, Any, Tuple
from tools.scopus_search import search_scopus, extract_papers
from tools.deduplication import deduplicate_papers

class SearcherAgent:
    """
    SearcherAgent: Specialist agent responsible for ReAct search execution,
    structured query refinement, multi-scenario handling (zero results, noisy results,
    API failures, duplicate rates), max iteration enforcement, and concise operational logging.
    """
    def __init__(self, target_paper_count: int = 50, max_iterations: int = 5):
        self.target_paper_count = target_paper_count
        self.max_iterations = max_iterations

    def refine_query(self, query: str, strategy: str, attempt: int) -> Tuple[str, str]:
        """
        Executes structured query refinement based on specified operational strategy.
        Returns: Tuple[refined_query, reason_for_revision]
        """
        if strategy == "broaden_terms":
            # Broaden query by expanding AND operators to OR or appending core synonyms
            if " AND " in query:
                refined = query.replace(" AND ", " OR ", 1)
                reason = "Broadened search by replacing first AND constraint with OR operator."
            else:
                refined = f'{query} OR TITLE-ABS-KEY("population dynamics" OR "ODE modeling")'
                reason = "Broadened query with additional general population dynamics terms."
        elif strategy == "tighten_terms":
            # Tighten query by adding stricter title constraints
            if not query.startswith("TITLE("):
                refined = f'TITLE("agentic AI" OR "differential equation" OR "predator-prey") AND {query}'
                reason = "Tightened search by requiring core terms in title field."
            else:
                refined = f'{query} AND TITLE-ABS-KEY("ODE" OR "dynamical system")'
                reason = "Tightened search with mandatory ODE/dynamical system keyword requirement."
        elif strategy == "remove_restrictive":
            # Simplify query by focusing on primary keywords
            refined = 'TITLE-ABS-KEY(("agentic AI" OR "AI agent") AND ("differential equation" OR "predator-prey"))'
            reason = "Refined query by removing overly restrictive sub-clause constraints."
        else:
            refined = query
            reason = "Preserved current query structure."

        return refined, reason

    def run(self, queries: List[str], research_question: str) -> Dict[str, Any]:
        """
        Executes literature search across queries with closed ReAct decision loop.
        Handles zero results, noisy results, API fallback, high duplicate ratio, and max iteration limits.
        """
        all_candidates = []
        react_logs = []
        active_queries = list(queries)

        print(f"[SearcherAgent] Starting ReAct search loop (Target: {self.target_paper_count} papers | Max Iterations: {self.max_iterations})...")

        iteration = 0
        query_idx = 0

        while iteration < self.max_iterations and query_idx < len(active_queries):
            iteration += 1
            current_q = active_queries[query_idx]

            # 1. Operational Decision & Action
            decision = f"Execute search iteration #{iteration} using query #{query_idx + 1}"
            action = f"Querying Scopus API with: {current_q[:80]}..."
            print(f"[SearcherAgent ReAct Loop #{iteration}] Decision: {decision}")

            # 2. Execution against Scopus or Offline Fallback
            raw_resp, data_source = search_scopus(current_q, count=25)
            extracted = extract_papers(raw_resp, source_label=data_source)

            # Check in-batch duplicates & historical duplicate ratio
            unique_in_step, dupes_in_step = deduplicate_papers(extracted)
            dup_ratio = (len(dupes_in_step) / len(extracted)) if len(extracted) > 0 else 0.0

            # 3. Operational Observation
            observation = {
                "iteration": iteration,
                "query_index": query_idx + 1,
                "raw_query": current_q,
                "data_source": data_source,
                "candidates_returned": len(extracted),
                "unique_candidates": len(unique_in_step),
                "duplicate_ratio": round(dup_ratio, 2)
            }
            print(f"[SearcherAgent ReAct Observation] Returned {len(extracted)} raw ({len(unique_in_step)} unique) via {data_source}.")

            # 4. ReAct Operational Decision Logic (Scenarios A - E)
            next_decision = "proceed_to_validation"
            query_strategy = "none"
            revision_reason = "Search yielded valid candidate pool."

            if len(extracted) == 0:
                # Case A: Zero results -> Broaden query
                next_decision = "broaden_query"
                query_strategy = "broaden_terms"
                refined_q, revision_reason = self.refine_query(current_q, query_strategy, iteration)
                active_queries.append(refined_q)
                print(f"[SearcherAgent ReAct Decision] Zero results returned. Decision: {next_decision} | Reason: {revision_reason}")

            elif len(extracted) > 40 and dup_ratio > 0.5:
                # Case B & D: Too many noisy/duplicate results -> Tighten query
                next_decision = "tighten_query"
                query_strategy = "tighten_terms"
                refined_q, revision_reason = self.refine_query(current_q, query_strategy, iteration)
                active_queries.append(refined_q)
                print(f"[SearcherAgent ReAct Decision] High duplicate/noisy ratio ({dup_ratio:.0%}). Decision: {next_decision}")

            elif "OFFLINE" in data_source:
                # Case C: API failure fallback
                next_decision = "accept_offline_fallback"
                revision_reason = "Scopus API unavailable; operating on OFFLINE / DEMO DATA baseline dataset."
                print(f"[SearcherAgent ReAct Decision] {revision_reason}")

            all_candidates.extend(unique_in_step)
            
            react_logs.append({
                "iteration": iteration,
                "decision": decision,
                "action": action,
                "observation": observation,
                "query_strategy": query_strategy,
                "reason_for_revision": revision_reason,
                "next_decision": next_decision
            })

            query_idx += 1
            time.sleep(0.2)

        total_unique, _ = deduplicate_papers(all_candidates)
        target_reached = len(total_unique) >= self.target_paper_count
        termination_status = "target_reached" if target_reached else ("max_iterations_reached" if iteration >= self.max_iterations else "search_completed")

        print(f"[SearcherAgent Status] Loop terminated: {termination_status} | Found: {len(total_unique)} unique candidates.")

        return {
            "status": "success",
            "termination_status": termination_status,
            "target_reached": target_reached,
            "candidates": total_unique,
            "total_raw_found": len(all_candidates),
            "target_paper_count": self.target_paper_count,
            "total_iterations": iteration,
            "react_logs": react_logs
        }
