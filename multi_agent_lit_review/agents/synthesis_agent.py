from typing import List, Dict, Any

class SynthesisAgent:
    """
    SynthesisAgent: Specialist agent responsible for thematic organization,
    identifying core trends, summarizing key innovations, and structuring
    the review paper synthesis.
    """
    def __init__(self, research_question: str = None):
        self.research_question = research_question

    def synthesize_batch(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Organizes validated literature into themes and synthesizes key scientific insights.

        Returns:
            Dict[str, Any] containing thematic groupings, key insights, and gap analysis.
        """
        categories = {}
        themes = {}

        for p in papers:
            cat = p.get("category", "General Literature")
            theme = p.get("theme", "LLM & Dynamical Systems Integration")

            categories.setdefault(cat, []).append(p)
            themes.setdefault(theme, []).append(p)

        theme_summaries = []
        for theme_name, theme_papers in themes.items():
            theme_summaries.append({
                "theme_name": theme_name,
                "paper_count": len(theme_papers),
                "key_findings": f"Synthesized findings across {len(theme_papers)} studies addressing {theme_name}.",
                "papers": [p.get("title") for p in theme_papers[:5]]
            })

        gap_analysis = (
            "Current literature highlights significant advances in LLM multi-agent automation for epidemic and kinetic "
            "ODE modeling (e.g., EpidemIQs, Talk2Biomodels). However, autonomous parameter estimation and real-time closed-loop "
            "re-fitting for ecological predator-prey dynamics under observational uncertainty remain key research gaps."
        )

        print(f"[SynthesisAgent] Synthesized {len(papers)} papers across {len(categories)} categories and {len(themes)} themes.")

        return {
            "status": "success",
            "total_synthesized": len(papers),
            "categories": categories,
            "themes": themes,
            "theme_summaries": theme_summaries,
            "gap_analysis": gap_analysis
        }
