import os
import json
import datetime
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class UnderstandingAgent:
    def __init__(self, model_name: str = "gemini-3.6-flash"):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model_name = model_name

    def parse_problem(self, problem_description: str) -> dict:
        prompt = (
            "You are an expert mathematical biology assistant.\n"
            "Analyze the following natural-language problem description of an ecological predator-prey dynamics problem:\n\n"
            f'"{problem_description}"\n\n'
            "Extract the following information and respond with a JSON object containing these exact keys:\n"
            '- "species_prey": string representing the prey species (or null if not mentioned)\n'
            '- "species_predator": string representing the predator species (or null if not mentioned)\n'
            '- "initial_prey": float number representing initial prey population (or null if not mentioned)\n'
            '- "initial_predator": float number representing initial predator population (or null if not mentioned)\n'
            '- "time_span_years": float number representing time span in years (default to 50.0 if not specified)\n'
            '- "has_real_data": boolean (true if user mentions having actual historical dataset to fit against, false otherwise)\n'
            '- "missing_info": list of strings describing any missing parameters or clarification needed\n\n'
            "Return ONLY a valid JSON object matching these keys."
        )

        model = genai.GenerativeModel(
            self.model_name,
            generation_config={"response_mime_type": "application/json"}
        )

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Clean potential markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        parsed_dict = json.loads(response_text)

        # Ensure time_span_years default
        if parsed_dict.get("time_span_years") is None:
            parsed_dict["time_span_years"] = 50.0

        missing_info = parsed_dict.get("missing_info", [])
        if missing_info:
            print("[UnderstandingAgent] Notice: Missing information detected in problem description:")
            for info in missing_info:
                print(f"  - {info}")
            print("[UnderstandingAgent] Suggestion: Assuming standard Lotka-Volterra parameters as starting point.\n")

        return parsed_dict


class ModelSelectionAgent:
    def __init__(self, model_name: str = "gemini-3.6-flash"):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model_name = model_name

    def select_model(self, understanding_result: dict) -> dict:
        species_prey = understanding_result.get("species_prey", "prey")
        species_predator = understanding_result.get("species_predator", "predator")
        initial_prey = understanding_result.get("initial_prey")
        initial_predator = understanding_result.get("initial_predator")
        time_span_years = understanding_result.get("time_span_years", 50.0)
        has_real_data = understanding_result.get("has_real_data", False)

        prompt = (
            "You are an expert mathematical biology assistant specializing in model structure selection.\n"
            "Analyze the extracted predator-prey problem details:\n"
            f"- Prey Species: {species_prey}\n"
            f"- Predator Species: {species_predator}\n"
            f"- Initial Prey Population: {initial_prey}\n"
            f"- Initial Predator Population: {initial_predator}\n"
            f"- Time Span (Years): {time_span_years}\n"
            f"- Has Real Data: {has_real_data}\n\n"
            "Choose between these TWO candidate model structures:\n"
            '1. "base Lotka-Volterra" (unbounded exponential prey growth): appropriate for classic empirical predator-prey cycle datasets (such as Hudson\'s Bay hare-lynx data), unconstrained population cycles, or fitting real population time series where carrying capacity is not specified.\n'
            '2. "logistic-extended Lotka-Volterra" (dx/dt = alpha*x*(1-x/K) - beta*x*y): appropriate when the problem context implies a bounded/limited environment (e.g., "region", "island", "farm") or long exploratory timeframes where carrying capacity constraints are explicitly assumed.\n\n'
            "Return ONLY a valid JSON object with these exact keys:\n"
            '- "model_name": string (must be either "base Lotka-Volterra" or "logistic-extended Lotka-Volterra")\n'
            '- "reasoning": string (1-2 sentences citing WHY this specific problem context suggests this choice)\n'
            '- "parameters": object containing initial parameter values. Include "K" (carrying capacity) ONLY if "logistic-extended Lotka-Volterra" is selected.'
        )

        model = genai.GenerativeModel(
            self.model_name,
            generation_config={"response_mime_type": "application/json"}
        )

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        parsed_dict = json.loads(response_text)

        # Mode determination based on has_real_data
        parsed_dict["mode"] = "fitting" if has_real_data else "exploratory"

        # Literature-informed parameter defaults
        selected_model = parsed_dict.get("model_name", "base Lotka-Volterra")
        if selected_model == "logistic-extended Lotka-Volterra":
            parsed_dict["parameters"] = {
                "alpha": 1.0,
                "beta": 0.1,
                "delta": 0.075,
                "gamma": 1.5,
                "K": 100.0
            }
        else:
            parsed_dict["parameters"] = {
                "alpha": 1.0,
                "beta": 0.1,
                "delta": 0.075,
                "gamma": 1.5
            }

        return parsed_dict


class FittingAgent:
    def fit(self, understanding_result: dict, model_choice: dict, real_data: dict) -> dict:
        t_data = np.array(real_data["t"], dtype=float)
        prey_data = np.array(real_data["prey"], dtype=float)
        pred_data = np.array(real_data["predator"], dtype=float)

        init_prey = prey_data[0] if len(prey_data) > 0 else understanding_result.get("initial_prey", 10.0)
        init_pred = pred_data[0] if len(pred_data) > 0 else understanding_result.get("initial_predator", 5.0)

        model_name = model_choice.get("model_name", "base Lotka-Volterra")
        default_params = model_choice.get("parameters", {})

        param_names = ["alpha", "beta", "delta", "gamma"]
        initial_guess = [
            float(default_params.get("alpha", 1.0)),
            float(default_params.get("beta", 0.1)),
            float(default_params.get("delta", 0.075)),
            float(default_params.get("gamma", 1.5))
        ]

        if model_name == "logistic-extended Lotka-Volterra":
            param_names.append("K")
            initial_guess.append(float(default_params.get("K", 100.0)))

        def loss(p):
            if any(val <= 0 for val in p):
                return 1e9

            alpha = p[0]
            beta = p[1]
            delta = p[2]
            gamma = p[3]
            K = p[4] if len(p) > 4 else 100.0

            def ode(t, state):
                x, y = state
                if model_name == "logistic-extended Lotka-Volterra":
                    dxdt = alpha * x * (1.0 - x / K) - beta * x * y
                else:
                    dxdt = alpha * x - beta * x * y
                dydt = delta * x * y - gamma * y
                return [dxdt, dydt]

            try:
                sol = solve_ivp(
                    ode,
                    (t_data[0], t_data[-1]),
                    [init_prey, init_pred],
                    t_eval=t_data,
                    max_step=1.0
                )
                if sol.status != 0 or sol.y.shape[1] != len(t_data):
                    return 1e9
                pred_x, pred_y = sol.y[0], sol.y[1]
                if np.any(np.isnan(pred_x)) or np.any(np.isnan(pred_y)):
                    return 1e9
                return float(np.sum((pred_x - prey_data) ** 2 + (pred_y - pred_data) ** 2))
            except Exception:
                return 1e9

        res = minimize(loss, initial_guess, method="Nelder-Mead")
        fitted_p_vals = res.x

        fitted_parameters = {name: float(val) for name, val in zip(param_names, fitted_p_vals)}

        # Evaluate fitted ODE to compute RMSE
        alpha = fitted_parameters.get("alpha", 1.0)
        beta = fitted_parameters.get("beta", 0.1)
        delta = fitted_parameters.get("delta", 0.075)
        gamma = fitted_parameters.get("gamma", 1.5)
        K = fitted_parameters.get("K", 100.0)

        def fitted_ode(t, state):
            x, y = state
            if model_name == "logistic-extended Lotka-Volterra":
                dxdt = alpha * x * (1.0 - x / K) - beta * x * y
            else:
                dxdt = alpha * x - beta * x * y
            dydt = delta * x * y - gamma * y
            return [dxdt, dydt]

        sol_fit = solve_ivp(
            fitted_ode,
            (t_data[0], t_data[-1]),
            [init_prey, init_pred],
            t_eval=t_data
        )

        fitted_prey = sol_fit.y[0]
        fitted_predator = sol_fit.y[1]

        rmse_prey = float(np.sqrt(np.mean((fitted_prey - prey_data) ** 2)))
        rmse_predator = float(np.sqrt(np.mean((fitted_predator - pred_data) ** 2)))

        avg_rmse = (rmse_prey + rmse_predator) / 2.0
        prey_range = float(np.max(prey_data) - np.min(prey_data))
        pred_range = float(np.max(pred_data) - np.min(pred_data))
        avg_data_range = (prey_range + pred_range) / 2.0

        fit_quality = "good" if avg_rmse < 0.15 * avg_data_range else "poor"

        return {
            "fitted_parameters": fitted_parameters,
            "rmse_prey": rmse_prey,
            "rmse_predator": rmse_predator,
            "fit_quality": fit_quality
        }


class SimulationAgent:
    def simulate(self, understanding_result: dict, model_choice: dict) -> dict:
        initial_prey = understanding_result.get("initial_prey")
        if initial_prey is None:
            initial_prey = 10.0
        initial_predator = understanding_result.get("initial_predator")
        if initial_predator is None:
            initial_predator = 5.0
        time_span_years = understanding_result.get("time_span_years", 50.0)

        model_name = model_choice.get("model_name", "base Lotka-Volterra")
        params = model_choice.get("parameters", {})
        alpha = params.get("alpha", 1.0)
        beta = params.get("beta", 0.1)
        delta = params.get("delta", 0.075)
        gamma = params.get("gamma", 1.5)
        K = params.get("K", 100.0)

        def ode_system(t, state):
            x, y = state
            if model_name == "logistic-extended Lotka-Volterra":
                dxdt = alpha * x * (1.0 - x / K) - beta * x * y
                dydt = delta * x * y - gamma * y
            else:
                dxdt = alpha * x - beta * x * y
                dydt = delta * x * y - gamma * y
            return [dxdt, dydt]

        t_eval = np.linspace(0.0, time_span_years, 200)
        sol = solve_ivp(
            ode_system,
            (0.0, time_span_years),
            [float(initial_prey), float(initial_predator)],
            t_eval=t_eval
        )

        prey_pop = sol.y[0]
        pred_pop = sol.y[1]

        went_extinct = bool(np.any(prey_pop < 0.5) or np.any(pred_pop < 0.5))

        plot_path = os.path.abspath("simulation_result.png")
        plt.figure(figsize=(10, 6))
        prey_name = understanding_result.get("species_prey") or "Prey"
        pred_name = understanding_result.get("species_predator") or "Predator"
        plt.plot(sol.t, prey_pop, label=f"Prey ({prey_name})", color="royalblue", linewidth=2)
        plt.plot(sol.t, pred_pop, label=f"Predator ({pred_name})", color="crimson", linewidth=2)
        plt.title(f"Predator-Prey Simulation ({model_name})", fontsize=14, fontweight="bold")
        plt.xlabel("Time (Years)", fontsize=12)
        plt.ylabel("Population", fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300)
        plt.close()

        return {
            "t": sol.t.tolist(),
            "prey_population": prey_pop.tolist(),
            "predator_population": pred_pop.tolist(),
            "plot_path": plot_path,
            "final_prey": float(prey_pop[-1]),
            "final_predator": float(pred_pop[-1]),
            "went_extinct": went_extinct
        }


class CritiqueAgent:
    def __init__(self, model_name: str = "gemini-3.6-flash"):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model_name = model_name

    def critique(self, understanding_result: dict, model_choice: dict, sim_result: dict) -> dict:
        mode = model_choice.get("mode", "exploratory")
        model_name_chosen = model_choice.get("model_name", "base Lotka-Volterra")
        reasoning = model_choice.get("reasoning", "")
        final_prey = sim_result.get("final_prey")
        final_predator = sim_result.get("final_predator")
        went_extinct = sim_result.get("went_extinct")
        prey_species = understanding_result.get("species_prey") or "prey"
        predator_species = understanding_result.get("species_predator") or "predator"

        validation_status = "unvalidated - exploratory" if mode == "exploratory" else "validated against real data"

        prompt = (
            "You are an expert wildlife management advisor and mathematical biology reviewer.\n"
            "Analyze the ecological model choice and simulation results provided below:\n"
            f"- Model Chosen: {model_name_chosen}\n"
            f"- Model Selection Reasoning: {reasoning}\n"
            f"- Simulation Mode: {mode}\n"
            f"- Final {prey_species} (Prey) Population: {final_prey}\n"
            f"- Final {predator_species} (Predator) Population: {final_predator}\n"
            f"- Extinction Occurred: {went_extinct}\n\n"
            "Instructions:\n"
            "1. Write a natural-language explanation (3 to 4 sentences) designed for a non-technical decision-maker (such as a wildlife management policymaker).\n"
            "   Your explanation MUST summarize:\n"
            "   a) What the simulation model predicts for the population dynamics over time.\n"
            "   b) Why this specific model structure was chosen.\n"
            "   c) An important caveat regarding its validation status.\n"
            "2. If mode is 'exploratory' (no real data was fitted), the critique MUST explicitly state that this is a projection based on literature-standard parameters, NOT validated against real population data for THIS specific case, and recommend what real data would be needed to validate it (e.g., historical population counts for this specific region).\n"
            "3. Formulate a concise recommended next step string outlining data collection or validation actions needed.\n\n"
            "Respond ONLY with a JSON object containing these exact keys:\n"
            '- "explanation": string (3-4 sentences for a non-technical decision-maker summarizing predictions, model choice rationale, and validation status caveat)\n'
            f'- "validation_status": string (must be exactly "{validation_status}")\n'
            '- "recommended_next_step": string (describing what real data is needed to validate or refine the model)'
        )

        model = genai.GenerativeModel(
            self.model_name,
            generation_config={"response_mime_type": "application/json"}
        )

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        parsed_dict = json.loads(response_text)

        parsed_dict["validation_status"] = validation_status

        return {
            "explanation": parsed_dict.get("explanation", ""),
            "validation_status": parsed_dict["validation_status"],
            "recommended_next_step": parsed_dict.get("recommended_next_step", "")
        }


class TechnicalAILoopAgent:
    def __init__(self, understanding_result: dict, data_file: str = "population_data.json"):
        self.understanding_result = understanding_result
        self.data_file = data_file
        self.history_file = "fit_history.json"
        self.report_file = "field_update_report.txt"

    def run_cycle(self) -> dict:
        if not os.path.exists(self.data_file):
            print(f"[TechnicalAILoopAgent] Error: Data file '{self.data_file}' not found.")
            return {"status": "error", "message": f"Data file '{self.data_file}' not found."}

        with open(self.data_file, "r") as f:
            real_data = json.load(f)

        t_data = real_data.get("t", [])
        data_point_count = len(t_data)

        history = None
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    history = json.load(f)
            except Exception:
                history = None

        last_data_point_count = history.get("data_point_count", 0) if history else 0

        if history and data_point_count <= last_data_point_count:
            print("No new census data - skipping re-fit")
            return {
                "status": "skipped",
                "reason": "No new census data",
                "data_point_count": data_point_count
            }

        new_data_points_added = data_point_count - last_data_point_count
        print(f"[TechnicalAILoopAgent] New census data detected ({new_data_points_added} new data points, total {data_point_count}). Running pipeline...")

        # 1. Model Selection Agent
        model_choice = ModelSelectionAgent().select_model(self.understanding_result)
        print(f"[TechnicalAILoopAgent] Model Selected: {model_choice.get('model_name')}")

        # 2. Fitting Agent
        fit_result = FittingAgent().fit(self.understanding_result, model_choice, real_data)
        print(f"[TechnicalAILoopAgent] Fitted Parameters: {fit_result['fitted_parameters']}")
        print(f"[TechnicalAILoopAgent] Prey RMSE: {fit_result['rmse_prey']:.4f}, Predator RMSE: {fit_result['rmse_predator']:.4f}")

        # 3. Simulation Agent using fitted parameters
        model_choice_fitted = dict(model_choice)
        model_choice_fitted["parameters"] = fit_result["fitted_parameters"]
        sim_result = SimulationAgent().simulate(self.understanding_result, model_choice_fitted)

        # 4. Critique Agent
        critique_result = CritiqueAgent().critique(self.understanding_result, model_choice_fitted, sim_result)

        # RMSE Comparison
        new_rmse_prey = fit_result["rmse_prey"]
        new_rmse_predator = fit_result["rmse_predator"]
        new_avg_rmse = (new_rmse_prey + new_rmse_predator) / 2.0

        rmse_comparison_str = ""
        if history and "last_avg_rmse" in history:
            last_avg_rmse = history["last_avg_rmse"]
            if new_avg_rmse < last_avg_rmse:
                rmse_comparison_str = "Fit quality improved with new data"
                print(rmse_comparison_str)
            elif new_avg_rmse > 1.2 * last_avg_rmse:
                rmse_comparison_str = "WARNING: fit quality degraded - possible data anomaly, review recommended"
                print(rmse_comparison_str)
            else:
                rmse_comparison_str = f"Fit quality stable (avg RMSE changed from {last_avg_rmse:.4f} to {new_avg_rmse:.4f})"
                print(rmse_comparison_str)
        else:
            rmse_comparison_str = f"First fit run (Initial avg RMSE: {new_avg_rmse:.4f})"
            print(rmse_comparison_str)

        # Save fit_history.json
        timestamp_str = datetime.datetime.now().isoformat()
        updated_history = {
            "last_run_timestamp": timestamp_str,
            "last_rmse_prey": new_rmse_prey,
            "last_rmse_predator": new_rmse_predator,
            "last_avg_rmse": new_avg_rmse,
            "last_fitted_parameters": fit_result["fitted_parameters"],
            "data_point_count": data_point_count,
            "fit_quality": fit_result["fit_quality"],
            "model_name": model_choice.get("model_name")
        }
        with open(self.history_file, "w") as f:
            json.dump(updated_history, f, indent=4)

        # Generate field_update_report.txt
        report_content = (
            "==================================================\n"
            "FIELD UPDATE REPORT - TECHNICAL AI LOOP\n"
            "==================================================\n"
            f"Timestamp: {timestamp_str}\n"
            f"Total Data Points: {data_point_count}\n"
            f"New Data Points Added: {new_data_points_added if history else data_point_count}\n"
            f"Model Chosen: {model_choice.get('model_name')}\n"
            f"Model Selection Reasoning: {model_choice.get('reasoning')}\n\n"
            "--- FITTED PARAMETERS ---\n"
            f"{json.dumps(fit_result['fitted_parameters'], indent=2)}\n\n"
            "--- RMSE COMPARISON ---\n"
            f"New Prey RMSE: {new_rmse_prey:.4f}\n"
            f"New Predator RMSE: {new_rmse_predator:.4f}\n"
            f"New Average RMSE: {new_avg_rmse:.4f}\n"
            f"Previous Average RMSE: {history.get('last_avg_rmse', 'N/A') if history else 'N/A'}\n"
            f"Comparison Result: {rmse_comparison_str}\n"
            f"Fit Quality Rating: {fit_result['fit_quality']}\n\n"
            "--- CRITIQUE EXPLANATION ---\n"
            f"Validation Status: {critique_result.get('validation_status')}\n"
            f"Explanation: {critique_result.get('explanation')}\n"
            f"Recommended Next Step: {critique_result.get('recommended_next_step')}\n"
            "==================================================\n"
        )
        with open(self.report_file, "w") as f:
            f.write(report_content)

        return {
            "status": "completed",
            "model_choice": model_choice,
            "fit_result": fit_result,
            "sim_result": sim_result,
            "critique_result": critique_result,
            "rmse_comparison": rmse_comparison_str
        }




