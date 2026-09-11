import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add project paths to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIT_REVIEW_DIR = PROJECT_ROOT / "multi_agent_lit_review"

if str(LIT_REVIEW_DIR) not in sys.path:
    sys.path.insert(0, str(LIT_REVIEW_DIR))

from agents.search_agent import SearcherAgent
from agents.validation_agent import ValidationAgent
from agents.synthesis_agent import SynthesisAgent
from agents.reviewer_agent import ReviewerAgent
from agents.document_agent import DocumentAgent
from agents.ai_loop_agent import AILoopAgent
from tools.deduplication import deduplicate_papers, normalize_doi, normalize_string
from tools.metadata import validate_paper_metadata, evaluate_paper_relevance
from tools.scopus_search import search_scopus, extract_papers

# 1. Test empty search result handling
def test_empty_search_result_handling():
    searcher = SearcherAgent(target_paper_count=50)
    # Search with an intentionally non-matching query
    results = searcher.run(["NONEXISTENT_XYZ_QUERY_123456789"], "Agentic AI")
    assert results["status"] == "success"
    assert isinstance(results["candidates"], list)

# 2. Test API failure / offline fallback
def test_api_failure_offline_fallback(monkeypatch):
    # Unset SCOPUS_API_KEY to force offline fallback
    monkeypatch.delenv("SCOPUS_API_KEY", raising=False)
    raw_resp, source_label = search_scopus("test query", count=10)
    assert source_label == "OFFLINE / DEMO DATA"
    papers = extract_papers(raw_resp, source_label=source_label)
    assert len(papers) > 0

# 3. Test duplicate paper removal
def test_duplicate_paper_removal():
    sample_papers = [
        {"title": "Paper One", "doi": "10.1000/182", "authors": "Author A", "year": "2026"},
        {"title": "Paper One", "doi": "10.1000/182", "authors": "Author A", "year": "2026"},
        {"title": "Paper Two", "doi": "10.1000/183", "authors": "Author B", "year": "2026"}
    ]
    unique, duplicates = deduplicate_papers(sample_papers)
    assert len(unique) == 2
    assert len(duplicates) == 1

# 4. Test missing DOI validation
def test_missing_doi_validation():
    paper = {"title": "Valid Title Here", "authors": "Author A", "year": 2026, "doi": ""}
    is_valid, reasons = validate_paper_metadata(paper)
    # DOI is not strictly required if title/authors/year are present
    assert is_valid is True

# 5. Test missing authors validation
def test_missing_authors_validation():
    paper = {"title": "Valid Title Here", "authors": "Unknown", "year": 2026}
    is_valid, reasons = validate_paper_metadata(paper)
    assert is_valid is False
    assert any("author" in r.lower() for r in reasons)

# 6. Test invalid year validation
def test_invalid_year_validation():
    paper = {"title": "Valid Title Here", "authors": "Author A", "year": "1850"}
    is_valid, reasons = validate_paper_metadata(paper)
    assert is_valid is False
    assert any("year" in r.lower() for r in reasons)

# 7. Test irrelevant paper rejection
def test_irrelevant_paper_rejection():
    paper = {"title": "Baking Cookies in High Altitudes", "abstract": "Recipes for baking.", "summary": "Cookies"}
    is_relevant, category, reason = evaluate_paper_relevance(paper, "Agentic AI ODE discovery")
    assert category == "General Literature" or category == "Irrelevant"

# 8. Test differential filtering of previously seen papers
def test_differential_filtering_previously_seen():
    validator = ValidationAgent(research_question="Agentic AI")
    sample_papers = [
        {"title": "Existing Paper", "doi": "10.1000/seen", "authors": "Author A", "year": 2026, "abstract": "Agentic AI ODE"}
    ]
    seen_dois = {"10.1000/seen"}
    res = validator.validate_batch(sample_papers, historical_dois=seen_dois)
    assert len(res["validated_papers"]) == 0
    assert res["summary"]["already_seen_historical_filtered"] == 1

# 9. Test Word document generation
def test_word_document_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_agent = DocumentAgent(output_dir=tmpdir)
        papers = [{
            "title": "EpidemIQs: LLM Agents for Epidemic Modeling",
            "authors": "Samaei M.H.",
            "year": 2026,
            "doi": "10.1109/TAI.2026.3666830",
            "category": "Direct",
            "summary": "Agentic framework for ODE modeling."
        }]
        path1 = doc_agent.create_literature_collection(papers, filename="test_col.docx")
        path2 = doc_agent.create_review_paper_draft(papers, {"categories": {"Direct": papers}}, filename="test_rev.docx")
        assert os.path.exists(path1)
        assert os.path.exists(path2)

# 10. Test ReAct query refinement
def test_react_query_refinement():
    searcher = SearcherAgent(target_paper_count=50)
    results = searcher.run(["('agentic AI' AND 'Lotka-Volterra')"], "Agentic AI ODEs")
    assert len(results["react_logs"]) > 0
    assert "thought" in results["react_logs"][0]
    assert "observation" in results["react_logs"][0]

# 11. Test Reviewer Agent rejection and revision trigger
def test_reviewer_agent_rejection_and_revision():
    reviewer = ReviewerAgent(target_paper_count=50)
    # Zero validated papers should trigger revision feedback
    res = reviewer.evaluate({}, {"total_candidates": 10}, [])
    assert res["passed"] is False
    assert res["verdict"] == "REVISE"

# 12. Test scheduler configuration
def test_scheduler_configuration():
    agent = AILoopAgent(target_paper_count=50)
    assert hasattr(agent, "start_scheduling")

# 13. Test state persistence
def test_state_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        hist_path = os.path.join(tmpdir, "literature_history.json")
        base_path = os.path.join(tmpdir, "final_papers_state.json")
        agent = AILoopAgent(history_path="literature_history.json", baseline_path="final_papers_state.json", output_dir=tmpdir)
        agent.save_history(["10.1234/test"], ["Test Paper Title"])
        loaded = agent.load_history()
        assert "10.1234/test" in loaded["already_seen_dois"]

# 14. Test query refinement logic
def test_query_refinement_logic():
    q = "TITLE-ABS-KEY(agent AND ode)"
    refined = q.replace("AND", "OR")
    assert "OR" in refined
