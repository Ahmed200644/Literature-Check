import re
from typing import List, Dict, Any, Tuple

def normalize_string(s: str) -> str:
    """Normalizes whitespace, casing, and punctuation for matching."""
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r'[\W_]+', ' ', s)
    return " ".join(s.split())

def normalize_doi(doi: str) -> str:
    """Normalizes DOI strings."""
    if not doi:
        return ""
    doi = doi.strip().lower()
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi)
    return doi

def deduplicate_papers(papers: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Deduplicates a list of paper objects based on normalized DOI and normalized title.

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (unique_papers, duplicate_papers)
    """
    seen_dois = set()
    seen_titles = set()
    unique_papers = []
    duplicate_papers = []

    for paper in papers:
        doi = normalize_doi(paper.get("doi", ""))
        title = normalize_string(paper.get("title", ""))

        is_duplicate = False
        if doi and doi in seen_dois:
            is_duplicate = True
        elif title and title in seen_titles:
            is_duplicate = True

        if is_duplicate:
            duplicate_papers.append(paper)
        else:
            if doi:
                seen_dois.add(doi)
            if title:
                seen_titles.add(title)
            unique_papers.append(paper)

    return unique_papers, duplicate_papers
