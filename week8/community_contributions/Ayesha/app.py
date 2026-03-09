import gradio as gr

from agents.scanner_agent import fetch_papers
from agents.relevance_agent import select_papers
from agents.rag_agent import find_similar
from agents.insight_agent import generate_insight


def run_scan():

    papers = fetch_papers()
    print("Fetched:", len(papers))

    selected = select_papers(papers)
    print("Selected:", len(selected))


    results = []

    for p in selected:

        context = find_similar(p["title"])

        insight = generate_insight(
            p["title"],
            p.get("summary", ""),
            context,
        )

        results.append(
            [p["title"], p["url"], insight[:500]]
        )

    return results


with gr.Blocks() as ui:

    gr.Markdown("# Research Paper Scout Agent")
    gr.Markdown("A multi-agent system that scans the latest research papers and selects the most relevant ones for further analysis.")

    table = gr.Dataframe(
        headers=["Title", "URL", "Insight"],
        row_count=7
    )

    btn = gr.Button("Scan Papers")

    btn.click(run_scan, outputs=table)

ui.launch(share=True)