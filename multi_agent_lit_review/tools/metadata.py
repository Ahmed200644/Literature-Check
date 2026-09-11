from typing import Dict, Any, Tuple, List

def validate_paper_metadata(paper: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates required metadata fields of a paper candidate.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_missing_or_invalid_reasons)
    """
    reasons = []

    title = paper.get("title", "")
    if not title or not isinstance(title, str) or len(title.strip()) < 5:
        reasons.append("Missing or invalid title (min 5 characters).")

    authors = paper.get("authors", "")
    if not authors or authors == "Unknown":
        reasons.append("Missing author metadata.")

    year = paper.get("year", "")
    if not year or str(year) == "Unknown":
        reasons.append("Missing publication year.")
    else:
        try:
            year_int = int(year)
            if year_int < 1900 or year_int > 2030:
                reasons.append(f"Publication year out of valid range: {year_int}")
        except ValueError:
            reasons.append(f"Publication year is not numeric: {year}")

    is_valid = len(reasons) == 0
    return is_valid, reasons

def evaluate_paper_relevance(paper: Dict[str, Any], research_question: str) -> Tuple[bool, str, str]:
    """
    Evaluates paper relevance against the research question using concept-combination scoring.

    Returns:
        Tuple[bool, str, str]: (is_relevant, category, reasoning)
    """
    text = f"{paper.get('title', '')} {paper.get('abstract', '')} {paper.get('summary', '')}".lower()

    # Core Concept Domains
    agentic_concepts = [
        "agentic ai", "agentic", "ai agent", "llm agent", "multi-agent",
        "autonomous agent", "reasoning agent", "scientific agent", "tool use"
    ]
    ode_math_concepts = [
        "ode", "ordinary differential equation", "differential equation",
        "dynamical system", "mathematical model", "parameter estimation",
        "parameter fitting", "model discovery", "numerical simulation"
    ]
    ecological_concepts = [
        "predator-prey", "lotka-volterra", "population dynamics",
        "invasive species", "ecological modeling", "epidemic", "hare", "lynx"
    ]
    adjacent_concepts = [
        "reinforcement learning", "control system", "neural ode",
        "scientific ml", "optimization", "dynamical control", "synergistic"
    ]

    agentic_matches = [kw for kw in agentic_concepts if kw in text]
    ode_matches = [kw for kw in ode_math_concepts if kw in text]
    eco_matches = [kw for kw in ecological_concepts if kw in text]
    adj_matches = [kw for kw in adjacent_concepts if kw in text]

    total_agentic = len(agentic_matches)
    total_ode = len(ode_matches)
    total_eco = len(eco_matches)
    total_adj = len(adj_matches)

    # Classification Rules
    if total_agentic >= 1 and (total_ode >= 1 or total_eco >= 1):
        return True, "Direct", f"Direct overlap: Agentic AI ({total_agentic} match) + ODE/Ecological modeling ({total_ode + total_eco} matches)."
    elif total_ode >= 2 or total_eco >= 2 or (total_ode >= 1 and total_eco >= 1):
        return True, "Methodological", f"Strong mathematical/ecological modeling methodology ({total_ode + total_eco} matches)."
    elif total_agentic >= 1 or total_adj >= 2 or (total_ode >= 1 and total_adj >= 1):
        return True, "Adjacent", f"Adjacent autonomous control or scientific machine learning methodology ({total_agentic + total_adj} matches)."
    elif (total_ode >= 1 or total_eco >= 1) and any(w in text for w in ["model", "simulation", "dynamic", "analysis", "system"]):
        return True, "General Literature", "Provides general context for scientific modeling and system dynamics."
    else:
        return False, "Irrelevant", "Does not contain sufficient concept overlap related to Agentic AI, ODE modeling, or population dynamics."

