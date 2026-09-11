# Technical Agent Architecture: Autonomous ODE Discovery & Parameter Estimation

This document specifies the 8-Step technical architecture for the **Technical Agent** designed for autonomous Ordinary Differential Equation (ODE) modeling and parameter estimation in dynamical and ecological systems (Predator–Prey / Lotka–Volterra models).

---

## 1. Purpose & Scope
The Technical Agent automates scientific model discovery for non-linear dynamical systems governed by ODEs.
- **Scope**: Formulation, parameter estimation, numerical simulation, and critique of ecological predator–prey interactions (e.g., Hudson's Bay Lynx-Hare dynamics).
- **Goal**: Transition from natural language problem descriptions to numerical ODE solutions and parameter fitting.

---

## 2. System Prompt Design
The system prompts establish domain role definitions, mathematical safety boundaries, and structured JSON output constraints.
- **Understanding Prompt**: Identifies prey/predator species, initial conditions, time horizon, and data availability.
- **Model Selection Prompt**: Evaluates model structure trade-offs (Base Lotka–Volterra vs. Logistic-extended Lotka–Volterra).
- **Critique Prompt**: Assesses parameter biological plausibility, goodness of fit ($R^2$, RMSE), and convergence.

---

## 3. Choose LLM
- **Primary LLM**: Gemini 3.6 Flash / GPT-4.1.
- **Function**: Natural language parsing, model structure selection, and qualitative reflection.
- **Deterministic Core**: Python execution harness (`scipy.integrate.solve_ivp`, `scipy.optimize.minimize`) for exact numerical integration and optimization.

---

## 4. Tools & Integrations
- **SciPy (`solve_ivp`, `minimize`)**: Explicit RK45 ODE solver and L-BFGS-B / Nelder-Mead parameter optimization.
- **NumPy & Pandas**: Data ingestion, normalization, and residual calculations.
- **Matplotlib / Seaborn**: Trajectory visualization (`simulation_result.png`).
- **State Store (`fit_history.json`)**: Persistent tracking of fitted parameters ($\alpha, \beta, \gamma, \delta$) over time.

---

## 5. Memory Systems
- **Short-Term Memory**: Conversation context and transient optimization iteration metrics.
- **Long-Term State Memory**: `fit_history.json` storing historical re-fitting runs, timestamps, RMSE trends, and fitted parameter trajectories.

---

## 6. Orchestration / Loop Engineering
- **State Machine**: `UnderstandingAgent` -> `ModelSelectionAgent` -> `FittingAgent` -> `SimulationAgent` -> `CritiqueAgent`.
- **Re-fit Trigger**: Time-triggered monthly schedule (`--schedule` CLI option) checking for field update data.
- **AI Loop**: If `CritiqueAgent` detects $R^2 < 0.70$ or unrealistic parameter values, it triggers model structure revision (e.g., switching from base Lotka-Volterra to logistic-extended).

---

## 7. User Interface
- **CLI Interface**: `python main.py` or `python multi_agent_lit_review/technical_agent/main.py --schedule`.
- **Visual Deliverables**: High-resolution population trajectory plots (`simulation_result.png`) and structured text summary reports.

---

## 8. Testing & Evaluation
- **Benchmark Suite**: Synthetic and historical Hudson's Bay data validation.
- **Evaluation Metrics**:
  - Root Mean Square Error (RMSE)
  - Coefficient of Determination ($R^2$)
  - Parameter Recovery Error (%)
  - Execution Latency (seconds)
