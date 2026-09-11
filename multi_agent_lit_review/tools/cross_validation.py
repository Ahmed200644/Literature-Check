import requests
import re
from typing import Dict, Any, List, Tuple
from tools.deduplication import normalize_doi, normalize_string

def _compare_titles(t1: str, t2: str) -> bool:
    n1 = normalize_string(t1)
    n2 = normalize_string(t2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    # Substring match if titles are long enough
    if len(n1) > 20 and len(n2) > 20 and (n1 in n2 or n2 in n1):
        return True
    return False

def verify_paper_cross_validation(paper: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
    """
    Performs independent metadata verification against OpenAlex and Crossref APIs.
    Returns structured cross-validation results with explicit status:
    'verified', 'partially_verified', 'not_verified', 'needs_review', or 'unavailable'.
    """
    doi = normalize_doi(paper.get("doi", ""))
    title = paper.get("title", "")
    authors = paper.get("authors", "")
    year = str(paper.get("year", ""))

    sources_checked = []
    matched_fields = set()
    mismatched_fields = set()
    openalex_matched = False
    crossref_matched = False

    # 1. Query OpenAlex API
    openalex_url = None
    if doi:
        openalex_url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    elif title and len(title.strip()) > 10:
        clean_t = re.sub(r'[^\w\s]', '', title)
        openalex_url = f"https://api.openalex.org/works?search={requests.utils.quote(clean_t)}"

    if openalex_url:
        sources_checked.append("OpenAlex")
        try:
            resp = requests.get(openalex_url, headers={"User-Agent": "LiteratureCheck/1.0"}, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                work = None
                if doi and "id" in data:
                    work = data
                elif "results" in data and len(data["results"]) > 0:
                    work = data["results"][0]

                if work:
                    oa_title = work.get("title", "")
                    if _compare_titles(title, oa_title):
                        openalex_matched = True
                        matched_fields.add("title")
                    
                    oa_doi = normalize_doi(work.get("doi", ""))
                    if doi and oa_doi and doi == oa_doi:
                        matched_fields.add("doi")
                        
                    oa_year = str(work.get("publication_year", ""))
                    if year and oa_year and year == oa_year:
                        matched_fields.add("year")
        except Exception:
            pass

    # 2. Query Crossref API
    crossref_url = None
    if doi:
        crossref_url = f"https://api.crossref.org/works/{doi}"
    elif title and len(title.strip()) > 10:
        crossref_url = f"https://api.crossref.org/works?query.title={requests.utils.quote(title)}&rows=1"

    if crossref_url:
        sources_checked.append("Crossref")
        try:
            resp = requests.get(crossref_url, headers={"User-Agent": "LiteratureCheck/1.0"}, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                msg = data.get("message", {})
                item = None
                if doi and "title" in msg:
                    item = msg
                elif "items" in msg and len(msg["items"]) > 0:
                    item = msg["items"][0]

                if item:
                    cr_titles = item.get("title", [])
                    cr_title = cr_titles[0] if isinstance(cr_titles, list) and cr_titles else str(cr_titles)
                    if _compare_titles(title, cr_title):
                        crossref_matched = True
                        matched_fields.add("title")

                    cr_doi = normalize_doi(item.get("DOI", ""))
                    if doi and cr_doi and doi == cr_doi:
                        matched_fields.add("doi")

                    cr_parts = item.get("published-print", {}).get("date-parts", [[]]) or item.get("published-online", {}).get("date-parts", [[]])
                    if cr_parts and cr_parts[0]:
                        cr_year = str(cr_parts[0][0])
                        if year and year == cr_year:
                            matched_fields.add("year")
        except Exception:
            pass

    # Determine validation status
    if not sources_checked or (not openalex_matched and not crossref_matched and not matched_fields):
        # Could be network unavailable, offline mode, or paper not in indexed databases
        if not sources_checked:
            status = "unavailable"
            reason = "External metadata validation APIs were not queried (missing identifier)."
        else:
            status = "unavailable"
            reason = "Independent metadata sources could not verify the candidate (API timeout, offline, or record not found)."
    elif openalex_matched and crossref_matched:
        status = "verified"
        reason = "Metadata verified across both OpenAlex and Crossref independent sources."
    elif openalex_matched or crossref_matched or len(matched_fields) >= 2:
        status = "partially_verified"
        matched_str = ", ".join(sources_checked)
        reason = f"Metadata matched independent source(s) ({matched_str}) across key fields: {list(matched_fields)}."
    else:
        status = "needs_review"
        reason = "Metadata verification yielded inconsistent or partial matches requiring manual review."

    return {
        "cross_validation_status": status,
        "sources_checked": sources_checked,
        "openalex_validated": openalex_matched,
        "crossref_validated": crossref_matched,
        "matched_fields": sorted(list(matched_fields)),
        "mismatched_fields": sorted(list(mismatched_fields)),
        "reason": reason
    }
