import gradio as gr
import requests
import pandas as pd

API_BASE = "http://localhost:8000"


# -------------------------------
# API CALLS
# -------------------------------
def search(query):
    try:
        res = requests.get(f"{API_BASE}/search", params={"query": query})
        data = res.json()

        results = data.get("results", [])

        mapping_rows = []
        other_rows = []

        for item in results:
            if isinstance(item, dict) and "metadata" in item:
                meta = item["metadata"]

                if meta.get("type") == "mapping":
                    mapping_rows.append(meta)
                else:
                    other_rows.append(meta)

        df_mapping = pd.DataFrame(mapping_rows) if mapping_rows else pd.DataFrame({"Message": ["No mapping data"]})
        df_other = pd.DataFrame(other_rows) if other_rows else pd.DataFrame({"Message": ["No other data"]})

        return df_mapping, df_other

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]}), pd.DataFrame({"Error": [str(e)]})


def lineage(query):
    try:
        res = requests.get(f"{API_BASE}/lineage", params={"column": query})
        data = res.json()

        if data.get("status") != "found":
            return data.get("message", "No lineage found")

        upstream = "\n".join(data.get("upstream", []))
        downstream = "\n".join(data.get("downstream", []))

        return f"🔼 Upstream:\n{upstream}\n\n🔽 Downstream:\n{downstream}"

    except Exception as e:
        return f"Error: {str(e)}"


def explain(query):
    try:
        res = requests.post(f"{API_BASE}/explain", params={"query": query})
        data = res.json()

        explanation = data.get("explanation", "")
        return explanation if explanation else "No explanation found"

    except Exception as e:
        return f"Error: {str(e)}"


# -------------------------------
# UI (ChatGPT Style Layout)
# -------------------------------
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="yellow"),
    title="Data Lineage Explorer"
) as app:

    gr.Markdown("# 🔎 Data Lineage Explorer")

    with gr.Row():

        # -------------------------------
        # LEFT PANEL (Controls)
        # -------------------------------
        with gr.Column(scale=1, min_width=300):

            gr.Markdown("## ⚙️ Controls")

            # Search
            query_search = gr.Textbox(
                label="Search Column",
                placeholder="e.g. customer_id"
            )
            search_btn = gr.Button("🔍 Search", variant="primary")

            gr.Markdown("---")

            # Lineage
            query_lineage = gr.Textbox(
                label="Column Lineage",
                placeholder="e.g. account_id"
            )
            lineage_btn = gr.Button("🔗 Get Lineage", variant="primary")

            gr.Markdown("---")

            # Explain
            query_explain = gr.Textbox(
                label="Explain Query",
                placeholder="Explain customer_id"
            )
            explain_btn = gr.Button("🤖 Explain", variant="primary")

        # -------------------------------
        # RIGHT PANEL (Results)
        # -------------------------------
        with gr.Column(scale=3):

            gr.Markdown("## 📊 Results")

            with gr.Tabs():

                with gr.Tab("🔍 Search Results"):

                    gr.Markdown("### 📌 Mapping Type = 'mapping'")
                    mapping_output = gr.Dataframe(
                    label="Mapping Data",
                    interactive=False
                    )

                    gr.Markdown("### 📌 SQL Types")
                    other_output = gr.Dataframe(
                    label="Other Data",
                    interactive=False
                    )

                with gr.Tab("🔗 Lineage"):
                    lineage_output = gr.Textbox(
                        label="Lineage Output",
                        lines=12
                    )

                with gr.Tab("🤖 Explanation"):
                    explain_output = gr.Textbox(
                        label="Explanation Output",
                        lines=12
                    )

        # -------------------------------
        # ACTIONS
        # -------------------------------
        search_btn.click(
            fn=search,
            inputs=query_search,
            outputs=[mapping_output,other_output]
        )

        lineage_btn.click(
            fn=lineage,
            inputs=query_lineage,
            outputs=lineage_output
        )

        explain_btn.click(
            fn=explain,
            inputs=query_explain,
            outputs=explain_output
        )


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    app.launch(inbrowser=True)