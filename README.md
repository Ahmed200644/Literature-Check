# Literature Agent AI: Autonomous Multi-Agent Literature Review & Technical ODE Discovery

[![Egypt Scholar Lab 12](https://img.shields.io/badge/Egypt%20Scholar-Lab%2012-blue)](https://github.com/Ahmed200644/Literature-Check)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An autonomous multi-agent AI system designed for academic literature monitoring, cross-validation, structured review synthesis, and technical Ordinary Differential Equation (ODE) parameter fitting in ecological and dynamical systems (e.g., Predator–Prey / Lotka–Volterra models).

---

## 1. Research Context & Problem Statement

This project is part of **Egypt Scholar Advanced Lab 12 (Team 7)** under the supervision of **Dr. Omar A. M. Abdelraouf (Ain Shams University)**.

### Research Area:
**Agentic AI for scientific discovery, mathematical discovery, and ODE-based scientific problems, especially dynamical and ecological systems such as Predator–Prey / Lotka–Volterra models.**

---

## 2. System Architecture & Progression (Week 1 → Week 5)

```text
Week 1: AI Roadmap & Harness
Prompt Engineering → Context Engineering → Harness System → AI Loop
        ↓
Week 2: Literature Agent Core
Searcher → Metadata Extractor → Deduplicator → Document Generator (50 Paper Target)
        ↓
Week 3: ReAct & Cross-Validation
Observable ReAct State Machine (Thought-Action-Observation) + Metadata & Relevance Validation
        ↓
Week 4: Genuine Multi-Agent System
SearcherAgent → ValidationAgent → SynthesisAgent → ReviewerAgent → DocumentAgent
        ↓
Week 5: Time-Triggered Loop & Differential Search
Scheduled Execution (--schedule) + Persistent History State Tracking (literature_history.json)
```

---

## 3. Specialist Agents

1. **SearcherAgent**: Executes Scopus API queries or offline fallback datasets. Performs ReAct query refinement (broadens on 0 results, tightens on noisy results).
2. **ValidationAgent**: Performs cross-validation, validates metadata schemas, removes duplicates, and filters previously processed historical papers.
3. **SynthesisAgent**: Categorizes papers into research themes, synthesizes key innovations, and identifies literature gaps.
4. **ReviewerAgent**: Audits synthesis quality against direct ODE representation and candidate ratios; issues `PASS` or `REVISE` verdicts.
5. **DocumentAgent**: Compiles formatted Word (`.docx`) reports (`literature_collection_report.docx` & `review_paper_draft.docx`).
6. **AILoopAgent (Coordinator)**: Central orchestrator managing the state machine, persistent state updates, and scheduled executions.

---

## 4. Technical Agent for Predator–Prey ODE Modeling

The repository also includes a specialized **Technical Agent** for mathematical biology:
- **Mathematical System**: Lotka–Volterra ODEs ($\frac{dx}{dt} = \alpha x - \beta x y$, $\frac{dy}{dt} = \delta x y - \gamma y$).
- **Core Engine**: SciPy numerical ODE integration (`solve_ivp`) and parameter optimization (`minimize`).
- **Outputs**: Parameter trajectories (`fit_history.json`) and plot visualization (`simulation_result.png`).
- **Documentation**:
  - [TECHNICAL_AGENT_ARCHITECTURE.md](file:///d:/Ahmed/study/research/E-labs/Week3/Literature%20Check/multi_agent_lit_review/technical_agent/TECHNICAL_AGENT_ARCHITECTURE.md) (8-Step Framework)
  - [TECHNICAL_AGENT_FACT_SHEET.md](file:///d:/Ahmed/study/research/E-labs/Week3/Literature%20Check/multi_agent_lit_review/technical_agent/TECHNICAL_AGENT_FACT_SHEET.md) (Fact Sheet & Benchmark)

---

## 5. Quick Start & Execution

### Installation
```powershell
pip install -r requirements.txt
```

### Configure API Keys (Optional)
Copy `.env.example` to `.env` and set your Elsevier Scopus API key:
```env
SCOPUS_API_KEY=your_key_here
```
*(If no API key is provided, the agent operates in `OFFLINE / DEMO DATA` mode automatically).*

### Run Literature Agent (Single Execution)
```powershell
python main.py
```

### Run Scheduled Mode (Every Saturday 08:00 AM)
```powershell
python main.py --schedule
```

### Run Technical Agent ODE Fitting
```powershell
python multi_agent_lit_review/technical_agent/main.py
```

### Run Test Suite
```powershell
pytest tests/ -v
```

---

## 6. Project Traceability & Results Documentation

- [WEEK1_WEEK5_AUDIT.md](file:///d:/Ahmed/study/research/E-labs/Week3/Literature%20Check/WEEK1_WEEK5_AUDIT.md): Complete Requirement Traceability Matrix mapping every requirement to code evidence.
- [WEEK1_WEEK5_RESULTS.md](file:///d:/Ahmed/study/research/E-labs/Week3/Literature%20Check/WEEK1_WEEK5_RESULTS.md): Detailed final engineering report.

> [!NOTE]
> **Week 6 RAG Exclusion**: Week 6 Vector RAG functionality is intentionally excluded from this release per design constraints.
