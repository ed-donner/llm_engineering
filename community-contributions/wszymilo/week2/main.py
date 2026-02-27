"""
Streaming variant of the Call Assistant Bot.
All required code is grouped here; only botsql and primitives are imported (unchanged).
"""

### 0. Audio Processing part
import os

from typing import Any
from dataclasses import dataclass, field
from dotenv import find_dotenv, load_dotenv
import gradio as gr
import groq
import soundfile as sf
import spaces
import xxhash

_ = load_dotenv(find_dotenv(), override=True)

groq_api_key = os.environ.get("GROQ_API_KEY")
groq_client = groq.Client(api_key=groq_api_key)



@dataclass
class AppState:
    conversation: list = field(default_factory=list)
    stopped: bool = False
    model_outs: Any = None

def process_audio(audio: tuple, state: AppState):
    return audio, state

js = """
async function main() {
  const script1 = document.createElement("script");
  script1.src = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.14.0/dist/ort.js";
  document.head.appendChild(script1)
  const script2 = document.createElement("script");
  script2.onload = async () =>  {
    console.log("vad loaded") ;
    var record = document.querySelector('.record-button');
    record.textContent = "Just Start Talking!"
    record.style = "width: fit-content; padding-right: 0.5vw;"
    const myvad = await vad.MicVAD.new({
      onSpeechStart: () => {
        var record = document.querySelector('.record-button');
        var player = document.querySelector('#streaming-out')
        if (record != null && (player == null || player.paused)) {
          console.log(record);
          record.click();
        }
      },
      onSpeechEnd: (audio) => {
        var stop = document.querySelector('.stop-button');
        if (stop != null) {
          console.log(stop);
          stop.click();
        }
      }
    })
    myvad.start()
  }
  script2.src = "https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.7/dist/bundle.min.js";
  script1.onload = () =>  {
    console.log("onnx loaded") 
    document.head.appendChild(script2)
  };
}
"""

js_reset = """
() => {
  var record = document.querySelector('.record-button');
  record.textContent = "Just Start Talking!"
  record.style = "width: fit-content; padding-right: 0.5vw;"
}
"""


def transcribe_audio(client, file_name):
    if file_name is None:
        return None

    try:
        with open(file_name, "rb") as audio_file:
            response = client.audio.transcriptions.with_raw_response.create(
                model="whisper-large-v3-turbo",
                file=("audio.wav", audio_file),
                response_format="verbose_json",
            )
            completion = process_whisper_response(response.parse())
            return completion
    except Exception as e:
        print(f"Error in transcription: {e}")
        return f"Error in transcription: {str(e)}"

def process_whisper_response(completion):
    """
    Process Whisper transcription response and return text or null based on no_speech_prob
    
    Args:
        completion: Whisper transcription response object
        
    Returns:
        str or None: Transcribed text if no_speech_prob <= 0.7, otherwise None
    """
    if completion.segments and len(completion.segments) > 0:
        no_speech_prob = completion.segments[0].get('no_speech_prob', 0)
        print("No speech prob:", no_speech_prob)

        if no_speech_prob > 0.7:
            return None
            
        return completion.text.strip()
    
    return None

@spaces.GPU(duration=40, progress=gr.Progress(track_tqdm=True))
def response(state: AppState, audio: tuple):
    if not audio:
        return AppState()

    file_name = f"/tmp/{xxhash.xxh32(bytes(audio[1])).hexdigest()}.wav"

    sf.write(file_name, audio[1], audio[0], format="wav")

    # Initialize Groq client
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Please set the GROQ_API_KEY environment variable.")
    client = groq.Client(api_key=api_key)

    # Transcribe the audio file
    transcription = transcribe_audio(client, file_name)
    if transcription:
        if transcription.startswith("Error"):
            transcription = "Error in audio transcription."

        # Append the user's message in the proper format
        state.conversation.append({"role": "user", "content": transcription})

        # Optionally, remove the temporary file
        os.remove(file_name)

    return state, transcription

    
def start_recording_user(state: AppState):
    return None

##### End of Audio Processing part


# -----------------------------------------------------------------------------
# 1. Imports & env
# -----------------------------------------------------------------------------
from enum import StrEnum
from types import SimpleNamespace
from typing import Any, Generator

from dotenv import find_dotenv, load_dotenv
import gradio as gr
from openai import OpenAI
from pydantic import BaseModel, Field

from botsql import DB
import primitives


# -----------------------------------------------------------------------------
# 2. Config
# -----------------------------------------------------------------------------
client = OpenAI()
MODEL = "gpt-4o-mini"
db = DB()
db.setup()


# -----------------------------------------------------------------------------
# 3. Enums
# -----------------------------------------------------------------------------
class UserType(StrEnum):
    PARTICIPANT = "participant"
    SPEAKER = "speaker"


# -----------------------------------------------------------------------------
# 4. Tool definitions (Pydantic models + handlers)
# -----------------------------------------------------------------------------
class AddCall(BaseModel):
    name: str = Field(..., description="The name of the call")


def add_call(name: str) -> None:
    db.add_call(name.lower())


class GetAllCalls(BaseModel):
    pass


def get_all_calls() -> list[dict]:
    return db.get_calls()


class AddQuestion(BaseModel):
    call_name: str = Field(..., description="The name of the call")
    question: str = Field(..., description="The question to add")
    username: str = Field(..., description="The username of the participant")


def add_question(call_name: str, question: str, username: str) -> None:
    db.add_question(call_name.lower(), question, username)


class GetQuestionsByUsername(BaseModel):
    username: str = Field(..., description="The username of the participant")


def get_questions_by_username(username: str) -> list[dict]:
    return db.get_questions_by_username(username)


class MarkQuestionAnswered(BaseModel):
    question_id: str = Field(..., description="The id of the question to mark as answered")


def mark_question_answered(question_id: str) -> None:
    db.mark_question_answered(int(question_id))


class GetNonAnsweredQuestions(BaseModel):
    name: str = Field(..., description="The name of the call")


def get_non_answered_questions(name: str) -> list[dict]:
    return db.get_non_answered_questions(name.lower())


# -----------------------------------------------------------------------------
# 5. Tool registry & API tools (from primitives)
# -----------------------------------------------------------------------------
TOOL_REGISTRY: primitives.ToolRegistry = {
    "add_call": (AddCall, add_call),
    "get_all_calls": (GetAllCalls, get_all_calls),
    "add_question": (AddQuestion, add_question),
    "mark_question_answered": (MarkQuestionAnswered, mark_question_answered),
    "get_non_answered_questions": (GetNonAnsweredQuestions, get_non_answered_questions),
    "get_questions_by_username": (GetQuestionsByUsername, get_questions_by_username),
}

tools = primitives.registry_tools(TOOL_REGISTRY)


# -----------------------------------------------------------------------------
# 6. Prompts
# -----------------------------------------------------------------------------
prompts = {
    UserType.PARTICIPANT.value: {
        "system": """You are agent supporting call in progress. The user may raise a question at any time.
        Respond in concise manner without any preamble.

        Your tasks:
        - If user posts a question: Store each question in the database using provided tools
        - if user marks a question as answered: Find question with the provided ID and mark it as answered using provided tools
        - if user ask about their own questions: Retrieve the questions from the database using provided tools
        - if user ask about all calls: Retrieve all the calls from the database using provided tools

        # Data
        - username: {username}
        - call_id: {call_id}
        """
    },
    UserType.SPEAKER.value: {
        "system": """You are agent supporting Speaker during a call in progress. Respond in concise manner without any preamble.
        Do NOT alter the text of any question

        Your tasks:
        - upon reveiving a request to start a call, you will:
            - create a new call in the database using provided tools
        - upon receiving a request for a digest from the Speaker, you will:
            - retrieve all unanswered questions from the database for the call
            - analyze the questions and group them by similarity
            - for each group, count the number of questions
            - select top {k} groups with the most questions
            - for each group, select a single question to represent the group
            - return a digest to the Speaker with the top {k} groups and the selected question from each group
        - upon receiving a request for stats from the Speaker, you will:
            - retrieve the total number of unaswered questions from the database for the call
            - return that number to the Speaker
        - upon receiving a request for all calls: Retrieve all the calls from the database using provided tools
        - upon receiving a request for a drill-down to a specific group of questions, you will:
            - retrieve the questions from the database for the provided group
            - return the questions to the Speaker

        Use provided tools to get required information.
        """
    },
}


# -----------------------------------------------------------------------------
# 7. Streaming completion with tool-call accumulation
# -----------------------------------------------------------------------------
def _accumulated_tool_calls_to_message(tool_calls_by_index: dict[int, dict[str, Any]]) -> Any:
    """Build a message-like object with .tool_calls for primitives.handle_tool_calls."""
    out = []
    for idx in sorted(tool_calls_by_index.keys()):
        tc = tool_calls_by_index[idx]
        out.append(
            SimpleNamespace(
                id=tc.get("id") or "",
                type="function",
                function=SimpleNamespace(
                    name=tc.get("name") or "",
                    arguments=tc.get("arguments") or "{}",
                ),
            )
        )
    return SimpleNamespace(tool_calls=out)


def _stream_completion_with_tools(
    client: OpenAI,
    model: str,
    messages: list[dict[str, Any]],
    tools_list: list[dict],
) -> Generator[tuple[str | None, Any | None], None, None]:
    """
    Stream a completion that may include tool calls.
    Yields (content_delta, None) for each content chunk.
    When stream ends with tool_calls, yields (None, message_with_tool_calls).
    When stream ends with stop, yields (None, None) and the accumulated content is complete.
    """
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        tools=tools_list,
    )

    tool_calls_by_index: dict[int, dict[str, Any]] = {}
    finish_reason = None

    for chunk in stream:
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        delta = choice.delta
        if choice.finish_reason is not None:
            finish_reason = choice.finish_reason

        if delta.content is not None and delta.content:
            yield (delta.content, None)

        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_by_index:
                    tool_calls_by_index[idx] = {"id": "", "name": "", "arguments": ""}
                acc = tool_calls_by_index[idx]
                if tc.id is not None:
                    acc["id"] = tc.id
                if tc.function:
                    if tc.function.name is not None:
                        acc["name"] = tc.function.name
                    if tc.function.arguments is not None:
                        acc["arguments"] = acc.get("arguments", "") + tc.function.arguments

    if finish_reason == "tool_calls" and tool_calls_by_index:
        msg = _accumulated_tool_calls_to_message(tool_calls_by_index)
        yield (None, msg)
    else:
        yield (None, None)


# -----------------------------------------------------------------------------
# 8. Chat generator (streaming): yields partial history for UI
# -----------------------------------------------------------------------------
def chat_stream(
    history: list[dict[str, str]],
    role: UserType,
    **kwargs: Any,
) -> Generator[list[dict[str, str]], None, None]:
    """
    Generator that yields updated history each time new content is streamed.
    Handles tool-call rounds internally; only the final text reply is streamed to the user.
    """
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    if role == UserType.PARTICIPANT:
        system = prompts[UserType.PARTICIPANT.value]["system"].format(**kwargs)
    else:
        system = prompts[UserType.SPEAKER.value]["system"].format(**kwargs)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        *history,
    ]

    current_reply = ""

    while True:
        for content_delta, tool_calls_message in _stream_completion_with_tools(
            client, MODEL, messages, tools
        ):
            if content_delta is not None:
                current_reply += content_delta
                stream_history = history + [{"role": "assistant", "content": current_reply}]
                yield stream_history

            if tool_calls_message is not None:
                responses = primitives.handle_tool_calls(tool_calls_message, TOOL_REGISTRY)
                assistant_msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls_message.tool_calls
                    ],
                }
                messages.append(assistant_msg)
                for resp in responses:
                    messages.append(resp)
                current_reply = ""
                break
        else:
            break

    history += [{"role": "assistant", "content": current_reply}]
    yield history


# -----------------------------------------------------------------------------
# 9. UI helpers
# -----------------------------------------------------------------------------
def get_call_ids() -> list[dict[str, Any]]:
    """Get all call IDs for the dropdown."""
    try:
        return [dict(row) for row in db.get_calls()]
    except Exception:
        return []


# -----------------------------------------------------------------------------
# 10. Send handlers (generators for Gradio streaming)
# -----------------------------------------------------------------------------
def participant_send(
    call_id: Any,
    username: str,
    user_input: str,
    history: list[dict[str, str]],
) -> Generator[tuple[str, list[dict[str, str]]], None, None]:
    if not call_id or not username or not user_input:
        yield "", history or []
        return
    history = history or []
    history.append({"role": "user", "content": user_input})
    for updated in chat_stream(history, UserType.PARTICIPANT, username=username, call_id=call_id):
        yield "", updated


def speaker_send(
    user_input: str,
    history: list[dict[str, str]],
) -> Generator[tuple[str, list[dict[str, str]], list[dict[str, str]], Any], None, None]:
    if not user_input:
        yield "", history or [], history or [], gr.update(
            choices=[f'{r["name"]} (ID: {r["id"]})' for r in get_call_ids()],
            elem_id="call-id-dropdown",
        )
        return
    history = history or []
    history.append({"role": "user", "content": user_input})
    for updated in chat_stream(history, UserType.SPEAKER, k=3):
        yield "", updated, updated, gr.update(
            choices=[f'{r["name"]} (ID: {r["id"]})' for r in get_call_ids()],
            elem_id="call-id-dropdown",
        )


# -----------------------------------------------------------------------------
# 11. Gradio Blocks (text-only UI; no audio to keep deps minimal)
# -----------------------------------------------------------------------------
with gr.Blocks(title="Call Assistant Bot (streaming)", js=js) as demo:
    participant_state = gr.State([])
    speaker_state = gr.State([])
    state = gr.State(AppState())
    gr.Markdown("# Call Assistant Bot (streaming)\nChoose your role to begin.")

    with gr.Tabs():
        with gr.Tab("Participant"):
            with gr.Row():
                call_id_dropdown = gr.Dropdown(
                    [f'{row["name"]} (ID: {row["id"]})' for row in get_call_ids()],
                    label="Select Call",
                    interactive=True,
                    elem_id="call-id-dropdown",
                )
                username_input = gr.Textbox(label="Your Name", max_lines=1)

            participant_chatbot = gr.Chatbot(
                label="Chat",
                height=300,
                type="messages",
                allow_tags=False,
            )
            participant_input = gr.Textbox(label="Enter message")

            with gr.Row():
                participant_send_btn = gr.Button("Send", variant="primary")
                gr.Button("Reset Chat").click(
                    lambda: ([], []),
                    outputs=[participant_chatbot, participant_state],
                )

            participant_send_btn.click(
                participant_send,
                inputs=[call_id_dropdown, username_input, participant_input, participant_state],
                outputs=[participant_input, participant_chatbot],
            )

        with gr.Tab("Speaker"):
            speaker_chatbot = gr.Chatbot(
                label="Chat",
                height=300,
                type="messages",
                allow_tags=False,
            )
            speaker_input = gr.Textbox(label="Enter message")

            with gr.Row():
                speaker_send_btn = gr.Button("Send", variant="primary")
                gr.Button("Reset Chat").click(
                    lambda: ([], []),
                    outputs=[speaker_chatbot, speaker_state],
                )

            with gr.Row():
                input_audio = gr.Audio(
                    label="Input Audio",
                    sources=["microphone"],
                    type="numpy",
                    streaming=False,
                    waveform_options=gr.WaveformOptions(waveform_color="#B83A4B"),
                )
                stream = input_audio.start_recording(
                    process_audio,
                    [input_audio, state],
                    [input_audio, state],
                )
                respond = input_audio.stop_recording(
                    response, inputs=[state, input_audio], outputs=[state, speaker_input]
                ).success(
                    speaker_send,
                    inputs=[speaker_input, speaker_state],
                    outputs=[speaker_input, speaker_chatbot, speaker_state, call_id_dropdown],
                )

                restart = respond.then(start_recording_user, inputs=[state], outputs=[input_audio]).then(
                    lambda state: state, inputs=[state], outputs=[state], js=js_reset
                )


            speaker_send_btn.click(
                speaker_send,
                inputs=[speaker_input, speaker_state],
                outputs=[speaker_input, speaker_chatbot, speaker_state, call_id_dropdown],
            )




if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", debug=True, show_error=True)
