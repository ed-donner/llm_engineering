import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)
openai = OpenAI()

tutor_system_prompt = """
You are an expert AI tutor engaged in an ongoing conversation with a student. This is a continuous learning session where you must remember and reference ALL previous topics discussed.

IMPORTANT: Always connect new answers to previous conversation topics. Reference what you've taught before and build upon prior knowledge. If the student asks about something new, relate it to concepts already covered when possible.

Be patient, encouraging, and adapt your teaching style to the student's needs.
Break down complex concepts into simple steps, provide clear examples, and ask questions to check understanding.
Use analogies, encourage critical thinking, and celebrate small victories.
Respond in well-formatted markdown with clear sections, code examples when relevant, and interactive elements.

When appropriate, say things like "Building on what we discussed earlier about [topic]..." or "Remember when we talked about [concept]? Let's apply that here..."
Always end with a question or prompt to continue the learning conversation.
"""

def initialize_session_state():
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0

def get_ai_response(user_input):
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    st.session_state.question_count += 1

    stream = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": tutor_system_prompt}
        ] + st.session_state.conversation_history,
        stream=True
    )

    response = ""
    response_placeholder = st.empty()

    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        response_placeholder.markdown(response)

    st.session_state.conversation_history.append({"role": "assistant", "content": response})

    return response

def main():
    st.set_page_config(
        page_title="AI Tutor",
        layout="wide"
    )

    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        font-size: 2.5em;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 1em;
    }
    .stButton > button {
        background: white !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 1.5em 1em !important;
        margin: 0.5em 0 !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        color: #374151 !important;
        font-size: 1em !important;
        min-height: 60px !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        line-height: 1.4 !important;
    }
    .stButton > button:hover {
        border-color: #3b82f6 !important;
        background: #f0f9ff !important;
        color: #1d4ed8 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1) !important;
    }

    .sidebar-clear-button {
        text-align: center;
        margin-top: 2em;
    }

    .attribution {
        position: fixed;
        bottom: 10px;
        left: 10px;
        font-size: 0.8em;
        color: #6b7280;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">AI Tutor</h1>', unsafe_allow_html=True)

    initialize_session_state()

    with st.sidebar:
        st.header("About")
        st.markdown("An AI tutor that remembers your conversation and builds upon previous knowledge.")

        st.markdown('<div class="sidebar-clear-button">', unsafe_allow_html=True)
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.question_count = 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="attribution">By Umar Javed</div>', unsafe_allow_html=True)

    if not st.session_state.conversation_history:
        st.markdown("""
        <div class="welcome-section">
        <h3 style="text-align: center; color: #1f2937; margin-bottom: 0.5em;">Welcome to AI Tutor</h3>
        <p style="text-align: center; color: #6b7280; margin-bottom: 2em;">Choose a topic to get started, or ask your own question below.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            if st.button("Explain Machine Learning", key="ml", use_container_width=True, type="secondary"):
                st.session_state.suggested_question = "Explain machine learning basics"

        with col2:
            if st.button("Teach Python Programming", key="python", use_container_width=True, type="secondary"):
                st.session_state.suggested_question = "Teach me Python programming fundamentals"

        with col3:
            if st.button("Data Structures & Algorithms", key="dsa", use_container_width=True, type="secondary"):
                st.session_state.suggested_question = "Explain data structures and algorithms"


    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message['content'])
        else:
            with st.chat_message("assistant"):
                st.markdown(message['content'])

    user_input = st.chat_input("What would you like to learn about?")

    suggested_input = getattr(st.session_state, 'suggested_question', None)
    if suggested_input:
        user_input = suggested_input
        del st.session_state.suggested_question

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            get_ai_response(user_input)

        st.empty()



if __name__ == "__main__":
    main()
