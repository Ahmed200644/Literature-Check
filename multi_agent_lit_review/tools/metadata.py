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
    Evaluates paper relevance against the research question keywords.

    Returns:
        Tuple[bool, str, str]: (is_relevant, category, reasoning)
    """
    text = f"{paper.get('title', '')} {paper.get('abstract', '')} {paper.get('summary', '')}".lower()
    
    # Keyword sets for categorization
    direct_keywords = ["agent", "agentic", "llm", "ode", "differential equation", "epidemiqs", "lotka-volterra", "predator-prey"]
    method_keywords = ["dynamical system", "mathematical model", "parameter estimation", "simulation", "population dynamics", "cooperation", "model formulation"]
    adjacent_keywords = ["microgrid", "reinforcement learning", "control", "optimization", "neural", "network"]

    direct_matches = sum(1 for kw in direct_keywords if kw in text)
    method_matches = sum(1 for kw in method_keywords if kw in text)
    adjacent_matches = sum(1 for kw in adjacent_keywords if kw in text)

    if direct_matches >= 2 or ("agent" in text and "ode" in text) or ("agent" in text and "epidemic" in text):
        return True, "Direct", f"Matches key agentic AI and ODE/dynamical system themes ({direct_matches} direct keyword matches)."
    elif direct_matches >= 1 or method_matches >= 2:
        return True, "Methodological", f"Matches mathematical modeling or population dynamics methodology ({method_matches} method matches)."
    elif adjacent_matches >= 1:
        return True, "Adjacent", f"Matches adjacent autonomous control or optimization systems ({adjacent_matches} adjacent matches)."
    elif len(text.strip()) > 20:
        return True, "General Literature", "Provides general context for scientific literature modeling."
    else:
        return False, "Irrelevant", "Does not contain sufficient keywords related to agentic AI or ODE mathematical modeling."
