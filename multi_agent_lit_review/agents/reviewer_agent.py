from typing import List, Dict, Any

class ReviewerAgent:
    """
    ReviewerAgent: Specialist agent that audits synthesized literature,
    verifies evidence completeness, evaluates relevance density, checks cross-validation health,
    and determines whether review output passes quality criteria (PASS) or requires revision (REVISE).
    """
    def __init__(self, target_paper_count: int = 50, min_validated_ratio: float = 0.5):
        self.target_paper_count = target_paper_count
        self.min_validated_ratio = min_validated_ratio

    def evaluate(
        self,
        synthesis_data: Dict[str, Any],
        validation_summary: Dict[str, Any],
        papers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates synthesis quality, evidence coverage, category balance, and cross-validation status.

        Returns:
            Dict[str, Any]: Verdict (PASS/REVISE), quality score (0-100), issues list, and recommendations.
        """
        issues = []
        recommendations = []

        validated_count = len(papers)
        total_candidates = validation_summary.get("total_candidates", 0)

        # Quality Check 1: Paper count & target coverage
        if validated_count == 0:
            issues.append("Zero validated papers available in synthesis.")
            recommendations.append("Execute search broadening strategy to identify initial candidate papers.")
        elif validated_count < (self.target_paper_count * 0.3):
            issues.append(f"Low paper count ({validated_count}/{self.target_paper_count} target).")
            recommendations.append("Expand query terms to cover adjacent mathematical modeling domains.")

        # Quality Check 2: Direct ODE & Agentic AI relevance representation
        direct_count = sum(1 for p in papers if p.get("category") == "Direct")
        method_count = sum(1 for p in papers if p.get("category") == "Methodological")
        
        if direct_count == 0 and validated_count > 0:
            issues.append("No papers classified in 'Direct' ODE / Agentic AI category.")
            recommendations.append("Refine search query to explicitly include 'agentic AI' AND ('ODE' OR 'predator-prey').")

        # Quality Check 3: Adequate candidate validation acceptance ratio
        if total_candidates > 0 and (validated_count / total_candidates) < 0.1:
            issues.append("Low validation acceptance ratio (<10% of candidates accepted).")
            recommendations.append("Tighten search queries with specific title constraints to improve search precision.")

        # Quality Check 4: Summary & Citation evidence completeness
        papers_with_summaries = sum(1 for p in papers if p.get("summary") and len(str(p.get("summary")).strip()) > 15)
        if validated_count > 0 and (papers_with_summaries / validated_count) < 0.8:
            issues.append("Insufficient summary coverage across validated literature.")
            recommendations.append("Re-extract paper abstract and summary text from primary sources.")

        # Quality Check 5: Cross-validation health
        xv_verified = sum(1 for p in papers if p.get("cross_validation_status") in ["verified", "partially_verified"])
        if validated_count > 0 and (xv_verified / validated_count) < 0.2:
            # Note: If live API is unavailable, cross-validation is labeled "unavailable"
            if not any(p.get("cross_validation_status") == "unavailable" for p in papers):
                issues.append("Low cross-validation verification rate across independent metadata sources.")
                recommendations.append("Perform manual metadata verification or query secondary metadata APIs.")

        # Overall verdict & score calculation
        passed = len(issues) == 0
        score = 100.0 if passed else max(40.0, 100.0 - (len(issues) * 15.0))
        verdict = "PASS" if passed else "REVISE"

        print(f"[ReviewerAgent Audit] Verdict: {verdict} | Quality Score: {score:.1f}/100 | Issues: {len(issues)}")
        for issue in issues:
            print(f"  - Issue: {issue}")

        return {
            "verdict": verdict,
            "passed": passed,
            "quality_score": round(score, 1),
            "issues": issues,
            "recommendations": recommendations,
            "validated_paper_count": validated_count,
            "direct_category_count": direct_count,
            "methodological_category_count": method_count,
            "cross_val_verified_count": xv_verified
        }
