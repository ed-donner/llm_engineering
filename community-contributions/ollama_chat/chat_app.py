import streamlit as st
from openai import OpenAI
import requests
import datetime

st.set_page_config(
    page_title="Ollama Chat",
)


def get_ollama_models(ollama_url: str):
    try:
        resp = requests.get(f"{ollama_url.replace('/v1','')}/api/tags")
        if resp.status_code == 200:
            return [m["name"] for m in resp.json()["models"]]
    except Exception:
        pass
    return ["gemma:2b"] 


def get_ai_response(client: OpenAI, model: str, messages: list):
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    reply = response.choices[0].message.content
    usage = response.usage if hasattr(response, "usage") else None
    return reply, usage, response


st.sidebar.header("Settings")

ollama_url = st.sidebar.text_input(
    "Ollama Server URL",
    value="http://localhost:11434/v1",
    help="Enter the Ollama API URL (default is local)"
)

@st.cache_data
def load_models(url):
    return get_ollama_models(url)

available_models = load_models(ollama_url)
selected_model = st.sidebar.selectbox("Choose a model", available_models)

# Clear conversation button
if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []

# Debug toggle
debug = st.sidebar.checkbox("Show raw response")


if "client" not in st.session_state:
    st.session_state.client = OpenAI(base_url=ollama_url, api_key="ollama")

client = st.session_state.client



st.title("Chat with Ollama via OpenAI API")



if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing conversation history with timestamp + tokens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        # Show timestamp and token usage in small grey font
        extra_info = f" {message['time']}"
        if "tokens" in message:
            extra_info += f" | Tokens: {message['tokens']}"
        st.markdown(
            f"<span style='font-size:12px; color:grey;'>{extra_info}</span>",
            unsafe_allow_html=True
        )



user_input = st.chat_input("Type your message...")

if user_input:
    # Save and display user message with timestamp (no tokens for user)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": timestamp
    })
    with st.chat_message("user"):
        st.write(user_input)
        st.markdown(f"<span style='font-size:12px; color:grey;'>🕒 {timestamp}</span>", unsafe_allow_html=True)

    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                ai_reply, usage, response = get_ai_response(client, selected_model, st.session_state.messages)
            except Exception as e:
                ai_reply, usage, response = f" Error: {str(e)}", None, None

        # Save and display assistant reply with timestamp + tokens
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        token_info = None
        if usage:
            # Combine prompt + completion tokens
            token_info = f"in:{usage.prompt_tokens}, out:{usage.completion_tokens}, total:{usage.total_tokens}"

        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_reply,
            "time": timestamp,
            "tokens": token_info
        })

        st.write(ai_reply)
        extra_info = f" {timestamp}"
        if token_info:
            extra_info += f" |  Tokens used : {token_info}"
        st.markdown(f"<span style='font-size:12px; color:grey;'>{extra_info}</span>", unsafe_allow_html=True)

        # Debug mode: show raw response JSON
        if debug and response is not None:
            st.json(response.model_dump())
