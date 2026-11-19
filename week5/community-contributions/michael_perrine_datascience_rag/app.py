"""Streamlit chat UI for the Data Science RAG. All retrieval and answer logic lives in rag.py.

Run from the datascience_rag folder:
    streamlit run app.py
"""
import os
from itertools import chain

import streamlit as st

import rag

st.set_page_config(page_title="Data Science Docs Assistant", layout="centered")

# Streamlit secrets (Community Cloud, or .streamlit/secrets.toml locally) override .env.
# rag.py's load_dotenv() has already run at import, so copy them in explicitly.
try:
    for k in rag.REQUIRED_ENV:
        if k in st.secrets:
            os.environ[k] = str(st.secrets[k])
except Exception:   # no secrets file: fall back to .env
    pass


# --- Clients: built once per process; a missing key stops the app with a clear message ---
@st.cache_resource(show_spinner="Connecting to OpenAI and Supabase…")
def init_clients() -> bool:
    rag.get_embeddings()
    rag.get_supabase()
    rag.get_stream_llm()
    return True


try:
    init_clients()
except RuntimeError as e:   # raised by rag._check_env()
    st.error(f"Configuration error: {e}. Add them to `.env` (local) or Streamlit secrets (deploy).")
    st.stop()

st.session_state.setdefault("messages", [])     # [{"role": "user", "content": str} | {"role": "assistant", "result": dict}]
st.session_state.setdefault("total_cost", 0.0)


# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    library = st.selectbox("Library", ["All", *rag.LIBRARIES],
                           help="Search one library's docs only, or all six.")
    show_details = st.toggle("Show details", help="Refusal layer, tokens and cost per answer.")
    cost_box = st.empty()                       # filled at the end of the script, after any new answer
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.total_cost = 0.0
        st.rerun()
    st.caption("Answers come only from the reference PDFs for pandas, NumPy, SciPy, scikit-learn, "
               "matplotlib and Plotly. Each question is answered on its own (no follow-up memory).")


# --- Rendering ---
def render_sources(sources: list[dict], heading: str) -> None:
    st.caption(heading)
    for s in sources:
        with st.container(border=True):
            link = f" · [docs]({s['url']})" if s.get("url") else ""
            st.markdown(f"**{s['library']} {s['version']}** · {s['section']} · p. {s['pages']}{link}")
            st.caption(f"similarity {s['sim']:.3f}")


def render_result(r: dict, details: bool) -> None:
    """Everything after the answer text: citations, or the refusal state."""
    if r["confident"]:
        if r["sources"]:
            render_sources(r["sources"], "Sources")
    else:
        st.warning(rag.REFUSAL)
        if r.get("llm_note"):                   # layer 2: the LLM says what the docs cover instead
            st.caption(r["llm_note"])
        if r["sources"]:
            render_sources(r["sources"], "Closest matches")
    if details:
        st.caption(f"refused_by: {r['refused_by']} · {r['input_tokens']:,} in / "
                   f"{r['output_tokens']:,} out tokens · ${r['cost']:.5f}")


# --- Chat ---
st.title("Data Science Docs Assistant")
st.caption("Ask about pandas, NumPy, SciPy, scikit-learn, matplotlib or Plotly. Answers cite the reference docs.")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m["role"] == "user":
            st.markdown(m["content"])
        else:
            if m["result"]["confident"]:
                st.markdown(m["result"]["answer"])
            render_result(m["result"], show_details)

if question := st.chat_input("Ask a question about the docs…"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    filters = {} if library == "All" else {"library": library}
    with st.chat_message("assistant"):
        final: dict = {}

        def tokens():
            """Pass answer tokens to the screen; keep the final result (done or refused)."""
            for kind, x in rag.ask_stream(question, **filters):
                if kind == "token":
                    yield x
                else:
                    final["result"] = x

        try:
            stream = tokens()
            with st.spinner("Searching the docs…"):   # retrieval + gate + time to first token
                first = next(stream, None)
            if first is not None:
                st.write_stream(chain([first], stream))
            r = final["result"]
            if r["confident"] and first is None:      # defensive: answered but nothing streamed
                st.markdown(r["answer"])
            render_result(r, show_details)
            st.session_state.messages.append({"role": "assistant", "result": r})
            st.session_state.total_cost += r["cost"]
        except Exception as e:                        # network / API errors: keep the chat usable
            st.error(f"Something went wrong: {e}")

cost_box.metric("Session cost", f"${st.session_state.total_cost:.4f}")
