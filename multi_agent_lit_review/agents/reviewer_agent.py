from typing import List, Dict, Any

class ReviewerAgent:
    """
    ReviewerAgent: Specialist agent that audits synthesized literature,
    verifies evidence completeness, evaluates relevance density, and determines
    whether the review output passes quality criteria or requires revision.
    """
    def __init__(self, target_paper_count: int = 50, min_validated_ratio: float = 0.5):
        self.target_paper_count = target_paper_count
        self.min_validated_ratio = min_validated_ratio

    def evaluate(self, synthesis_data: Dict[str, Any], validation_summary: Dict[str, Any], papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates synthesis and validation data against quality standards.

        Returns:
            Dict[str, Any]: Verdict (PASS/REJECT), quality score, issues, and revision directions.
        """
        issues = []
        recommendations = []

        validated_count = len(papers)
        total_candidates = validation_summary.get("total_candidates", 0)

        # Quality Check 1: Paper count presence
        if validated_count == 0:
            issues.append("Zero validated papers available in synthesis.")

        # Quality Check 2: Direct ODE relevance representation
        direct_count = sum(1 for p in papers if p.get("category") == "Direct")
        if direct_count == 0 and validated_count > 0:
            issues.append("No papers classified in 'Direct' ODE / Agentic AI category.")
            recommendations.append("Expand query terms to specifically cover agentic ODE discovery.")

        # Quality Check 3: Adequate candidate pool ratio
        if total_candidates > 0 and (validated_count / total_candidates) < 0.1:
            issues.append("Low validation acceptance ratio (<10% of candidates accepted).")
            recommendations.append("Tighten search queries to improve search precision.")

        passed = len(issues) == 0
        score = 100.0 if passed else max(50.0, 100.0 - (len(issues) * 20.0))

        verdict = "PASS" if passed else "REVISE"

        print(f"[ReviewerAgent Verdict] Status: {verdict} | Quality Score: {score:.1f}/100 | Issues Identified: {len(issues)}")

        return {
            "verdict": verdict,
            "passed": passed,
            "quality_score": score,
            "issues": issues,
            "recommendations": recommendations,
            "validated_paper_count": validated_count,
            "direct_category_count": direct_count
        }
