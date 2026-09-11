import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Determine project root dynamically
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_STATE_PATH = PROJECT_ROOT / "multi_agent_lit_review" / "final_papers_state.json"

def search_scopus(query: str, count: int = 25) -> Tuple[Dict[str, Any], str]:
    """
    Executes a search against the Scopus API if credentials exist.
    If SCOPUS_API_KEY is missing or API fails, falls back to offline demo dataset.

    Returns:
        Tuple[Dict[str, Any], str]: (raw_response_or_dict, data_source_label)
    """
    api_key = os.environ.get("SCOPUS_API_KEY")
    if api_key and api_key.strip():
        url = "https://api.elsevier.com/content/search/scopus"
        headers = {
            "X-ELS-APIKey": api_key.strip(),
            "Accept": "application/json"
        }
        params = {
            "query": query,
            "count": count
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json(), "LIVE SCOPUS"
            else:
                print(f"[Scopus Tool Warning] Scopus API returned HTTP {resp.status_code}. Falling back to offline dataset.")
        except Exception as e:
            print(f"[Scopus Tool Error] Scopus API connection failed ({e}). Falling back to offline dataset.")

    # Fallback to offline demo data
    fallback_data = _load_offline_dataset()
    return fallback_data, "OFFLINE / DEMO DATA"

def extract_papers(raw_response: Dict[str, Any], source_label: str = "LIVE SCOPUS") -> List[Dict[str, Any]]:
    """
    Extracts standardized paper dictionary objects from Scopus API JSON or offline fallback JSON.
    """
    papers = []
    
    # Scopus API response structure
    if "search-results" in raw_response and "entry" in raw_response["search-results"]:
        entries = raw_response["search-results"]["entry"]
        for entry in entries:
            title = entry.get("dc:title", "")
            creator = entry.get("dc:creator", "Unknown")
            doi = entry.get("prism:doi", "")
            cover_date = entry.get("prism:coverDate", "")
            year = cover_date.split("-")[0] if cover_date else "Unknown"
            publication = entry.get("prism:publicationName", "Scopus Indexed Source")
            abstract = entry.get("dc:description", "")

            papers.append({
                "title": title,
                "authors": creator,
                "doi": doi,
                "year": year,
                "source_journal": publication,
                "abstract": abstract,
                "data_source": source_label,
                "category": "Uncategorized",
                "theme": "General Literature",
                "summary": abstract or title
            })
        return papers

    # Offline fallback array structure
    if "papers" in raw_response and isinstance(raw_response["papers"], list):
        items = raw_response["papers"]
    elif isinstance(raw_response, list):
        items = raw_response
    else:
        items = []

    for item in items:
        p = dict(item)
        p["data_source"] = source_label
        papers.append(p)

    return papers

def _load_offline_dataset() -> Dict[str, Any]:
    """Loads baseline offline dataset from final_papers_state.json if present."""
    state_file = BASELINE_STATE_PATH
    if not state_file.exists():
        # Look in workspace root
        alt = PROJECT_ROOT / "final_papers_state.json"
        if alt.exists():
            state_file = alt

    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {"papers": data if isinstance(data, list) else data.get("papers", [])}
        except Exception as e:
            print(f"[Scopus Tool Warning] Could not parse offline state file: {e}")

    return {"papers": []}
