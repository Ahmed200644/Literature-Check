from typing import List, Dict, Any, Set, Tuple
from tools.deduplication import deduplicate_papers, normalize_doi, normalize_string
from tools.metadata import validate_paper_metadata, evaluate_paper_relevance
from tools.cross_validation import verify_paper_cross_validation

class ValidationAgent:
    """
    ValidationAgent: Specialist agent responsible for metadata validation,
    cross-validation, deduplication against historical state, and relevance verification.
    """
    def __init__(self, research_question: str = None, run_live_cross_validation: bool = True):
        self.research_question = research_question
        self.run_live_cross_validation = run_live_cross_validation

    def validate_batch(
        self,
        papers: List[Dict[str, Any]],
        historical_dois: Set[str] = None,
        historical_titles: Set[str] = None
    ) -> Dict[str, Any]:
        """
        Validates, deduplicates, and evaluates relevance for a batch of candidate papers.

        Returns:
            Dict[str, Any] containing validated papers, rejected papers, and validation summary metrics.
        """
        if historical_dois is None:
            historical_dois = set()
        if historical_titles is None:
            historical_titles = set()

        validated_papers = []
        rejected_papers = []
        needs_review_papers = []

        # Step 1: In-batch deduplication
        unique_candidates, duplicates_in_batch = deduplicate_papers(papers)

        # Metrics counters
        total_candidates = len(papers)
        duplicate_count = len(duplicates_in_batch)
        already_seen_count = 0
        metadata_failed_count = 0
        relevance_failed_count = 0
        cross_val_verified_count = 0

        print(f"[ValidationAgent] Processing {total_candidates} raw candidates ({duplicate_count} in-batch duplicates removed)...")

        # Step 2: Validate metadata, check historical presence, evaluate relevance
        for p in unique_candidates:
            doi = normalize_doi(p.get("doi", ""))
            title = normalize_string(p.get("title", ""))

            # Check historical state (differential literature search)
            if (doi and doi in historical_dois) or (title and title in historical_titles):
                already_seen_count += 1
                p["validation_status"] = "rejected"
                p["rejection_reason"] = "Previously processed in historical literature state."
                rejected_papers.append(p)
                continue

            # Check metadata validity
            meta_valid, meta_reasons = validate_paper_metadata(p)
            if not meta_valid:
                metadata_failed_count += 1
                p["validation_status"] = "rejected"
                p["rejection_reason"] = f"Metadata validation failed: {'; '.join(meta_reasons)}"
                rejected_papers.append(p)
                continue

            # Evaluate relevance against research question
            rq = self.research_question or "Agentic AI systems and ODE dynamical modeling"
            is_relevant, category, rel_reason = evaluate_paper_relevance(p, rq)
            p["category"] = category
            p["tier"] = category
            p["relevance_reason"] = rel_reason

            if not is_relevant:
                relevance_failed_count += 1
                p["validation_status"] = "rejected"
                p["rejection_reason"] = f"Relevance check failed: {rel_reason}"
                rejected_papers.append(p)
                continue

            # Step 3: Perform transparent cross-validation (OpenAlex & Crossref)
            if self.run_live_cross_validation:
                xv_res = verify_paper_cross_validation(p, timeout=3.0)
                p["cross_validation_status"] = xv_res["cross_validation_status"]
                p["cross_validation_details"] = xv_res
                p["validated_openalex"] = xv_res["openalex_validated"]
                p["validated_crossref"] = xv_res["crossref_validated"]
                if xv_res["cross_validation_status"] in ["verified", "partially_verified"]:
                    cross_val_verified_count += 1
            else:
                p["cross_validation_status"] = "unavailable"
                p["cross_validation_details"] = {"reason": "Cross-validation disabled or offline"}
                p["validated_openalex"] = False
                p["validated_crossref"] = False

            # If all checks pass
            p["validated"] = True
            p["validation_status"] = "validated"
            validated_papers.append(p)

        summary = {
            "total_candidates": total_candidates,
            "in_batch_duplicates_removed": duplicate_count,
            "already_seen_historical_filtered": already_seen_count,
            "metadata_failures": metadata_failed_count,
            "relevance_failures": relevance_failed_count,
            "cross_val_verified_count": cross_val_verified_count,
            "validated_count": len(validated_papers),
            "rejected_count": len(rejected_papers),
            "needs_review_count": len(needs_review_papers)
        }

        print(f"[ValidationAgent Cross-Validation Summary] Validated: {len(validated_papers)} | Cross-Val Verified: {cross_val_verified_count} | Filtered (Already Seen): {already_seen_count} | Rejected: {len(rejected_papers)}")

        return {
            "status": "success",
            "validated_papers": validated_papers,
            "rejected_papers": rejected_papers,
            "needs_review_papers": needs_review_papers,
            "summary": summary
        }

