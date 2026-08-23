import os
import tempfile

import streamlit as st

from services.model_service import ModelService

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# -----------------------------------------------------------------------------
# Page Config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ AI Meeting Assistant")
st.write(
    "Upload a meeting recording to automatically generate a summary and chat with the transcript."
)

# -----------------------------------------------------------------------------
# Session State
# -----------------------------------------------------------------------------
if "model_service" not in st.session_state:
    st.session_state.model_service = None

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "summary_generated" not in st.session_state:
    st.session_state.summary_generated = False

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:

    st.header("Meeting")

    uploaded_file = st.file_uploader(
        "Upload Audio",
        type=["mp3", "wav", "m4a"],
    )

    if st.session_state.model_service is not None:
        page = st.radio(
            "Navigate",
            [
                "📝 Meeting Summary",
                "💬 Chat with Meeting",
            ],
        )
    else:
        page = None

# -----------------------------------------------------------------------------
# Process Upload
# -----------------------------------------------------------------------------
if uploaded_file is not None:

    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("Please upload an audio file smaller than 100 MB.")
        st.stop()

    filename = uploaded_file.name

    if st.session_state.uploaded_file_name != filename:

        suffix = os.path.splitext(filename)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_file.write(uploaded_file.getbuffer())
            temp_path = temp_file.name

        with st.spinner("Loading meeting..."):

            try:
                model_service = ModelService(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        st.session_state.model_service = model_service
        st.session_state.summary = ""
        st.session_state.summary_generated = False
        st.session_state.uploaded_file_name = filename
        st.session_state.messages = []

        st.rerun()

# -----------------------------------------------------------------------------
# No Upload Yet
# -----------------------------------------------------------------------------
if st.session_state.model_service is None:
    st.info("Upload an audio file from the sidebar to begin.")
    st.stop()

# -----------------------------------------------------------------------------
# Summary Page
# -----------------------------------------------------------------------------
if page == "📝 Meeting Summary":

    st.header("📝 Meeting Summary")

    summary_placeholder = st.empty()

    if not st.session_state.summary_generated:

        with st.spinner("Generating summary..."):

            summary = ""

            for chunk in st.session_state.model_service.summarize():
                summary = chunk
                summary_placeholder.markdown(summary)

            st.session_state.summary = summary
            st.session_state.summary_generated = True

    else:
        summary_placeholder.markdown(st.session_state.summary)

# -----------------------------------------------------------------------------
# Chat Page
# -----------------------------------------------------------------------------
elif page == "💬 Chat with Meeting":

    st.header("💬 Chat with Meeting")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask something about the meeting...")

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            placeholder = st.empty()
            response = ""

            history = st.session_state.messages[:-1]

            for chunk in st.session_state.model_service.chat(
                prompt,
                history,
            ):
                response = chunk
                placeholder.markdown(response)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )
