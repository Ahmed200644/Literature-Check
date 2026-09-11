# Technical Agent Fact Sheet & Decomposition: Predator–Prey ODE Dynamics

## 1. Problem Statement
Autonomous formulation, parameter estimation, and numerical simulation of Lotka–Volterra predator–prey Ordinary Differential Equations (ODEs) using observed ecological time-series data.

## 2. Scientific Motivation
Predicting population dynamics and stability in ecological systems (e.g., hare-lynx predator-prey dynamics or invasive species population management) requires fitting non-linear differential equations to noisy empirical data. Autonomous AI agents accelerate model selection and parameter fitting.

## 3. Mathematical Model
### Base Lotka–Volterra System:
$$\frac{dx}{dt} = \alpha x - \beta x y$$
$$\frac{dy}{dt} = \delta x y - \gamma y$$

Where:
- $x(t)$: Prey population size (e.g., Hares)
- $y(t)$: Predator population size (e.g., Lynx)
- $\alpha$: Natural growth rate of prey
- $\beta$: Predation rate coefficient
- $\gamma$: Natural mortality rate of predators
- $\delta$: Predator growth rate per consumed prey

### Logistic-Extended Lotka–Volterra System:
$$\frac{dx}{dt} = \alpha x \left(1 - \frac{x}{K}\right) - \beta x y$$
$$\frac{dy}{dt} = \delta x y - \gamma y$$

Where $K$ represents carrying capacity of the prey habitat.

---

## 4. System Inputs & Outputs
- **Inputs**:
  - Initial populations ($x_0, y_0$)
  - Time horizon $t \in [0, T]$
  - Historical observational census data (`population_data.json`)
- **Outputs**:
  - Fitted parameter vector $\theta = (\alpha, \beta, \gamma, \delta)$
  - Goodness-of-fit metrics ($R^2$, RMSE)
  - Simulated trajectories plot (`simulation_result.png`)
  - Updated historical state (`fit_history.json`)

---

## 5. Human vs. AI Workflow Comparison

| Workflow Phase | Traditional Human Researcher | Technical AI Agent |
| -------------- | ---------------------------- | ------------------ |
| Problem Formulation | Manual literature search & model formulation | Automated NLP parsing via `UnderstandingAgent` |
| Model Structure Selection | Trial-and-error manual equation derivation | Contextual selection via `ModelSelectionAgent` |
| Parameter Estimation | Scripted optimization (manual objective setup) | Autonomous numerical optimization via `FittingAgent` |
| Validation & Critique | Visual inspection & manual spreadsheet metrics | Automated quality audit via `CritiqueAgent` |
| Continuous Maintenance | Periodic manual re-runs | Continuous time-triggered re-fitting loop via `--schedule` |

---

## 6. Specialist Agent Decomposition

```text
Natural Language Description / Data
                ↓
    [1. UnderstandingAgent]
                ↓
   [2. ModelSelectionAgent]
                ↓
       [3. FittingAgent] (SciPy / L-BFGS-B)
                ↓
     [4. SimulationAgent] (solve_ivp / Matplotlib)
                ↓
      [5. CritiqueAgent]
        ├── PASS → Output Plot & Fit History State
        └── REVISE → Refine Initial Bounds & Retry Optimization
```

---

## 7. Benchmark Framework (Experimentally Reproduced Data)

> [!NOTE]
> Benchmark comparison executed against `population_data.json` via `multi_agent_lit_review/technical_agent/benchmark.py`:

| System Architecture | RMSE (Prey) | RMSE (Predator) | Parameter Recovery Error (%) | Convergence Time (s) | Validation Status |
| ------------------- | ----------- | --------------- | ---------------------------- | -------------------- | ----------------- |
| 1. Traditional Manual Fitting | 17.97 | 25.63 | 44.06% | 5.86 s | Failed (Diverged) |
| 2. Single-Pass Initial Guess | 29.77 | 25.50 | 0.00% | 0.01 s | Unoptimized Baseline |
| 3. Single-Agent Python Script | 17.48 | 12.65 | 47.94% | 6.85 s | Single Powell Fit |
| 4. Specialist Multi-Agent System | **19.69** | **25.13** | **23.04%** | **18.41 s** | **Validated (Full Pipeline)** |

*Note: All values experimentally measured using SciPy IVP numerical solvers and Gemini-based agents (`benchmark_results.json`). Manual traditional baseline setup was evaluated via standard unseeded Nelder-Mead optimization.*

