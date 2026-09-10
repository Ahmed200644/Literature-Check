class SearchAgent:
    def run(self, queries):
        return []

class ValidationAgent:
    def __init__(self, research_question=None):
        self.research_question = research_question
    def validate_batch(self, papers):
        return papers

class SynthesisAgent:
    def __init__(self, research_question=None):
        self.research_question = research_question
    def synthesize_batch(self, papers):
        return papers

class DocumentAgent:
    def create_document(self, papers, output_path=None):
        pass

from agents.ai_loop_agent import AILoopAgent
import os
import json
import matplotlib.pyplot as plt
try:
    import seaborn as sns
    sns.set_theme(style="whitegrid")
except ImportError:
    sns = None
    plt.style.use('ggplot')

def generate_charts(json_path="final_papers_state.json", output_dir="."):
    """
    Generates and overwrites category_split.png, theme_distribution.png, and year_distribution.png
    using the provided state file (defaults to final_papers_state.json).
    Prints the paper count used and output file paths.
    """
    target_json = json_path
    if not os.path.exists(target_json):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alt1 = os.path.join(base_dir, json_path)
        alt2 = os.path.join(base_dir, "multi_agent_lit_review", json_path)
        if os.path.exists(alt1):
            target_json = alt1
        elif os.path.exists(alt2):
            target_json = alt2

    target_output_dir = output_dir
    if target_output_dir == ".":
        target_output_dir = os.path.dirname(os.path.abspath(target_json))

    with open(target_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    papers = data if isinstance(data, list) else data.get('papers', [])
    paper_count = len(papers)

    cat_path = os.path.abspath(os.path.join(target_output_dir, "category_split.png"))
    theme_path = os.path.abspath(os.path.join(target_output_dir, "theme_distribution.png"))
    year_path = os.path.abspath(os.path.join(target_output_dir, "year_distribution.png"))

    # Style configuration
    if sns:
        sns.set_theme(style="whitegrid")
    plt.rcParams.update({'font.sans-serif': 'Arial', 'font.family': 'sans-serif'})

    # 1. Category Split (Donut Chart)
    cats = {}
    for p in papers:
        c = p.get("category", "Uncategorized")
        cats[c] = cats.get(c, 0) + 1

    fig, ax = plt.subplots(figsize=(7, 7))
    palette = ["#2B5B84", "#3A9B7A", "#E07A5F", "#8D99AE", "#D4A373"]
    wedges, texts, autotexts = ax.pie(
        cats.values(),
        labels=cats.keys(),
        autopct='%1.1f%%',
        startangle=140,
        colors=palette[:len(cats)],
        wedgeprops=dict(width=0.4, edgecolor='w', linewidth=2),
        textprops=dict(size=12)
    )
    for at in autotexts:
        at.set_color('white')
        at.set_weight('bold')
    ax.set_title(f"Paper Category Distribution (N={paper_count})", fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(cat_path, dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Theme Distribution (Horizontal Bar Chart)
    themes = {}
    for p in papers:
        t = p.get("theme", "General")
        themes[t] = themes.get(t, 0) + 1

    sorted_themes = dict(sorted(themes.items(), key=lambda x: x[1], reverse=False))

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(list(sorted_themes.keys()), list(sorted_themes.values()), color="#2B5B84", height=0.6)
    ax.set_title(f"Research Themes Distribution (N={paper_count})", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Number of Papers", fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.15, bar.get_y() + bar.get_height()/2, f"{int(width)}", ha='left', va='center', fontsize=10, fontweight='bold', color='#333333')

    plt.tight_layout()
    plt.savefig(theme_path, dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Year Distribution (Vertical Bar Chart)
    years = {}
    for p in papers:
        y = p.get("year", "Unknown")
        years[y] = years.get(y, 0) + 1

    sorted_years = dict(sorted(years.items(), key=lambda x: str(x[0])))

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar([str(k) for k in sorted_years.keys()], sorted_years.values(), color="#3A9B7A", width=0.55)
    ax.set_title(f"Publication Year Distribution (N={paper_count})", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Publication Year", fontsize=12)
    ax.set_ylabel("Number of Papers", fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.15, f"{int(height)}", ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(year_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Paper count used: {paper_count}")
    print(f"Resulting file paths:\n - {cat_path}\n - {theme_path}\n - {year_path}")
    return paper_count, [cat_path, theme_path, year_path]

__all__ = ["SearchAgent", "ValidationAgent", "SynthesisAgent", "DocumentAgent", "AILoopAgent", "generate_charts"]

# Call generate_charts() using final_papers_state.json
generate_charts()

