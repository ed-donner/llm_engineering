import streamlit as st
import requests
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

API_BASE = "http://localhost:8000"

st.set_page_config(layout="wide")

# -------------------------------
# LAYOUT
# -------------------------------
left, right = st.columns([1, 3])

# -------------------------------
# LEFT PANEL (CONTROLS)
# -------------------------------
with left:
    st.title("🔎 Explorer")

    query = st.text_input("Search")

    st.markdown("### Actions")
    search_btn = st.button("🔍 Search")
    lineage_btn = st.button("🔗 Column Lineage")
    explain_btn = st.button("🤖 Explain")

    st.markdown("---")
    st.markdown("### Column Explorer")
    column_input = st.text_input("table.column")

    explore_btn = st.button("Explore Column")


# -------------------------------
# HELPER
# -------------------------------
def call_api(method, endpoint, params=None):
    try:
        url = f"{API_BASE}{endpoint}"

        if method.upper() == "GET":
            res = requests.get(url, params=params)
        else:
            # ✅ Send JSON payload properly
            res = requests.post(url, params=params)

        # ✅ Raise error for bad responses (VERY IMPORTANT for debugging)
        res.raise_for_status()

        return res.json(), None

    except requests.exceptions.HTTPError:
        # ✅ Capture FastAPI validation errors (422 etc.)
        try:
            return None, res.json()
        except Exception:
            return None, res.text

    except Exception as e:
        return None, str(e)


# -------------------------------
# RIGHT PANEL (RESULTS)
# -------------------------------
with right:

    # -------------------------------
    # SEARCH RESULTS
    # -------------------------------
    if search_btn and query:
        data, err = call_api("GET", "/search", {"query": query})

        if err:
            st.error(err)
        else:
            results = data.get("results", [])

            mapping_rows = []
            sql_rows = []

            for r in results:
                m = r.get("metadata", {})

                if m.get("type") == "mapping":
                    mapping_rows.append({
                        "Gold Table": m.get("gold_table"),
                        "Gold Column": m.get("gold_column"),
                        "Source Table": m.get("source_table"),
                        "Source Column": m.get("source_column"),
                    })

                elif m.get("type") == "sql":
                    sql_rows.append({
                        "Table": m.get("table"),
                        "Target": m.get("target"),
                        "Sources": m.get("sources"),
                    })

            st.subheader("📋 Results")

            if mapping_rows:
                st.markdown("#### 🔵 Mapping")
                st.dataframe(pd.DataFrame(mapping_rows), width='stretch')

            if sql_rows:
                st.markdown("#### 🟣 SQL")
                st.dataframe(pd.DataFrame(sql_rows), width='stretch')

    # -------------------------------
    # LINEAGE GRAPH
    # -------------------------------
    if lineage_btn and query:
        data, err = call_api("GET", "/lineage", {"column": query})

        if err:
            st.error(err)
        else:
            up = data.get("upstream", [])
            down = data.get("downstream", [])

            G = nx.DiGraph()

            for u in up:
                G.add_edge(u, query)

            for d in down:
                G.add_edge(query, d)

            if G.nodes:
                st.subheader("🔗 Lineage Graph")

                fig = plt.figure(figsize=(10, 6))
                pos = nx.kamada_kawai_layout(G)

                nx.draw(
                    G,
                    pos,
                    with_labels=True,
                    node_size=2500,
                    font_size=8
                )

                st.pyplot(fig)

    # -------------------------------
    # COLUMN EXPLORER
    # -------------------------------
    if explore_btn and column_input:
        data, err = call_api("GET", "/lineage", {"column": column_input})

        if err:
            st.error(err)
        else:
            st.subheader("🎯 Column Lineage")

            st.write("🔼 Upstream:", data.get("upstream", []))
            st.write("🔽 Downstream:", data.get("downstream", []))

    # -------------------------------
    # EXPLANATION
    # -------------------------------
    if explain_btn and query:
        data, err = call_api("POST", "/explain", {"query": query})

        if err:
            st.error(err)
        else:
            st.subheader("🧠 Explanation")
            st.write(data.get("explanation"))