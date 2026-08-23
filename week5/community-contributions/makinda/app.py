"""
Gradio UI for KUCCPS cluster calculator + RAG university/guidance advisor.
Students enter grades and course of interest; system shows cluster points and up to 4 universities with expert guidance.
"""
from pathlib import Path
import sys

MAKINDA_DIR = Path(__file__).resolve().parent
if str(MAKINDA_DIR) not in sys.path:
    sys.path.insert(0, str(MAKINDA_DIR))

# Load .env from project root (llm_engineering)
PROJECT_ROOT = MAKINDA_DIR.parent.parent.parent
DOTENV = PROJECT_ROOT / ".env"
if DOTENV.exists():
    from dotenv import load_dotenv
    load_dotenv(DOTENV, override=True)

import gradio as gr

from clusters import (
    KUCCPS_CLUSTERS,
    GRADE_POINTS,
    calculate_cluster_points,
    get_cluster_by_id,
)
from answer import answer_question

# Subject codes and labels for the form (common KCSE subjects)
SUBJECT_INPUTS = [
    ("English", "ENG"),
    ("Kiswahili", "KIS"),
    ("Mathematics", "MAT A"),
    ("Biology", "BIO"),
    ("Physics", "PHY"),
    ("Chemistry", "CHE"),
    ("Geography", "GEO"),
    ("History", "HIS"),
    ("CRE", "CRE"),
    ("Business Studies", "BST"),
]
GRADES = list(GRADE_POINTS.keys())


def run_calculator(
    eng, kis, mat, bio, phy, che, geo, his, cre, bst,
    cluster_id,
    course_interest,
):
    """Build subject_grades from dropdowns, compute cluster, then RAG for universities and guidance."""
    subject_grades = {
        "ENG": eng,
        "KIS": kis,
        "MAT A": mat,
        "BIO": bio,
        "PHY": phy,
        "CHE": che,
        "GEO": geo,
        "HIS": his,
        "CRE": cre,
        "BST": bst,
    }
    # Filter out empty (Gradio can send None)
    subject_grades = {k: (v or "E") for k, v in subject_grades.items()}

    result = calculate_cluster_points(cluster_id, subject_grades)
    if result.get("error"):
        return (
            f"**Error:** {result['error']}",
            "",
            "",
        )

    weighted = result["weighted"]
    raw = result["raw_cluster"]
    agg = result["aggregate"]
    cluster_name = result["cluster_name"]

    # Build cluster summary for display
    best7_str = ", ".join(
        f"{s['code']} {s['grade']}({s['points']})" for s in result["best7"]
    )
    cluster_subj_str = ", ".join(
        f"{s['name']} {s['grade']}({s['points']})" for s in result["cluster_subjects"]
    )
    summary_md = f"""
### Cluster result: {cluster_name}
- **Weighted cluster points:** {weighted}
- **Raw cluster:** {raw}/48 · **Aggregate:** {agg}/84
- **Top 4 cluster subjects:** {cluster_subj_str}
- **Best 7 (aggregate):** {best7_str}
"""
    if weighted >= 40:
        interp = "Excellent — you qualify for most competitive programmes in this cluster."
    elif weighted >= 30:
        interp = "Good — you qualify for many programmes."
    elif weighted >= 20:
        interp = "Moderate — you may qualify for some programmes; check cut-offs."
    else:
        interp = "Consider improving grades or exploring other clusters/courses."
    summary_md += f"\n**Interpretation:** {interp}\n"

    # RAG: ask for universities (at most 4) and expert guidance
    question = (
        f"My weighted cluster points for {cluster_name} are {weighted}. "
        f"My course or programme of interest is: {course_interest or 'any in this cluster'}. "
        f"Which universities do I qualify for? List at most four universities and give brief expert guidance."
    )
    try:
        guidance = answer_question(question, cluster_summary=summary_md)
    except Exception as e:
        guidance = f"Could not load guidance (check OPENROUTER_API_KEY in .env): {e}"

    return summary_md, guidance, course_interest or "(none)"


def build_ui():
    with gr.Blocks(title="KUCCPS Cluster & University Advisor", theme=gr.themes.Soft()) as ui:
        gr.Markdown(
            "# KUCCPS Cluster & University Advisor\n"
            "Enter your KCSE grades, select your target cluster, and your course of interest. "
            "We'll compute your cluster points and suggest **at most 4 universities** with expert guidance."
        )
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Your grades (select per subject)")
                inputs = {}
                for label, code in SUBJECT_INPUTS:
                    inputs[code] = gr.Dropdown(
                        choices=GRADES,
                        value="C",
                        label=label,
                    )
                gr.Markdown("### Target cluster & course")
                cluster_id = gr.Dropdown(
                    choices=[(c["name"], c["id"]) for c in KUCCPS_CLUSTERS],
                    value=KUCCPS_CLUSTERS[0]["id"],
                    label="Cluster",
                )
                cluster_info = gr.Markdown(
                    f"*{KUCCPS_CLUSTERS[0]['description']}*"
                )
                course_interest = gr.Textbox(
                    label="Course or programme of interest",
                    placeholder="e.g. Medicine, B.Sc. Computer Science, B.Com",
                )

                def update_cluster_info(cid):
                    c = get_cluster_by_id(cid)
                    if c:
                        return f"*{c['description']}*"
                    return ""

                cluster_id.change(
                    update_cluster_info,
                    inputs=[cluster_id],
                    outputs=[cluster_info],
                )

                btn = gr.Button("Calculate & Get University Recommendations", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown("### Your cluster result")
                result_md = gr.Markdown(value="*Results will appear here.*")
                gr.Markdown("### Universities & expert guidance (at most 4)")
                guidance_tb = gr.Markdown(value="*Guidance will appear here.*")
                course_used = gr.Textbox(label="Course interest used", interactive=False)

        btn.click(
            run_calculator,
            inputs=[
                inputs["ENG"], inputs["KIS"], inputs["MAT A"], inputs["BIO"],
                inputs["PHY"], inputs["CHE"], inputs["GEO"], inputs["HIS"],
                inputs["CRE"], inputs["BST"],
                cluster_id,
                course_interest,
            ],
            outputs=[result_md, guidance_tb, course_used],
        )
    return ui


def main():
    ui = build_ui()
    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
