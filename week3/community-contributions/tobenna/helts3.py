# Human English Language Testing System 3

# AI System that tests humans English language reading and writing skills.
#
# In this version,

# HuggingFace pipelines are used to run sentiment analysis and NER on the essay
# Analysis is displayed as a footer beneath the essay after it is generated


import json
import os
import random

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from transformers import pipeline

OPENROUTER_MODEL = "gpt-5-nano"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


load_dotenv(override=True)
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY not found in environment. Check your .env file."
    )


openrouter = OpenAI(api_key=API_KEY, base_url=OPENROUTER_BASE_URL)


SYSTEM_PROMPT = [
    {
        "role": "system",
        "content": """
    You are an English language examiner who tests humans on their reading skills. Difficulty level is how hard
    the essay comprehension is and how hard the questions are. It is from 1 to 4, 1 being the easiest and 4 being the hardest.
    The essay can be structured as title and body. Only paragraphs allowed, no headers or subheaders. Answers must be from the essay.
    Correct answers that are not in the essay should be marked as incorrect.
    """,
    },
]

RESPONSE_FORMAT = """then return the essay and questions in this json format: 
      {
        "essay": "essay text in markdown format",
        "questions": ["question 1", "question 2", "question 3"]
      }
      """

TOPICS = [
    "AI",
    "Technology",
    "Science",
    "History",
    "Art",
    "Culture",
    "Sports",
    "Politics",
    "Economy",
    "Environment",
]
LEVELS = [("Easy", "1"), ("Intermediate", "2"), ("Advanced", "3"), ("Expert", "4")]

DEFAULT_NUM_QUESTIONS = 5


def get_question(difficulty=1, topic=None, num_questions=DEFAULT_NUM_QUESTIONS):
    return f"""Generate an essay in with difficulty level {difficulty} on {topic if topic else random.choice(TOPICS)}.
    Ask {num_questions} questions from the essay."""


_sentiment_pipeline = None
_ner_pipeline = None

ENTITY_LABELS = {
    "PER": "Person",
    "ORG": "Organization",
    "LOC": "Location",
    "MISC": "Miscellaneous",
}


def get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline("sentiment-analysis")
    return _sentiment_pipeline


def get_ner_pipeline():
    global _ner_pipeline
    if _ner_pipeline is None:
        _ner_pipeline = pipeline("ner", aggregation_strategy="simple")
    return _ner_pipeline


def analyze_essay(text):
    plain = text.replace("#", "").replace("*", "").replace("_", "").strip()

    sentiment = get_sentiment_pipeline()(plain, truncation=True, max_length=512)[0]
    sentiment_label = sentiment["label"].capitalize()
    sentiment_score = sentiment["score"] * 100

    entities = get_ner_pipeline()(plain[:2000])

    lines = [
        f"**Sentiment:** {sentiment_label} ({sentiment_score:.1f}%)",
        "",
        "**Named Entities:**",
    ]
    seen = set()
    for ent in entities:
        key = (ent["word"], ent["entity_group"])
        if key not in seen:
            seen.add(key)
            label = ENTITY_LABELS.get(ent["entity_group"], ent["entity_group"])
            lines.append(f"- {ent['word']} ({label})")
    if not entities:
        lines.append("- None detected")

    return "\n".join(lines)


def new_state():
    return {
        "messages": list(SYSTEM_PROMPT),
        "current_question": 0,
        "essay_text": "",
        "questions": [],
        "answers": [],
        "analysis": "",
    }


def submit_answers(final_answer, state):
    if not state["questions"]:
        return "*Start the examination first.*", state

    if state["current_question"] != len(state["questions"]) - 1:
        return "*Please answer all questions before submitting.*", state

    if final_answer.strip():
        state["answers"][state["current_question"]] = final_answer

    for i in range(len(state["questions"])):
        state["messages"].append(
            {"role": "assistant", "content": state["questions"][i]}
        )
        state["messages"].append({"role": "user", "content": state["answers"][i]})

    state["messages"].append(
        {
            "role": "user",
            "content": "Please grade the essay. 70+ A, 60-69 B, 50-59 C, 40-49 D, 0-39 F. After \
              show review as thus: the question, user answer, correct answer if wrong. format as \
                markdown in the form of a result sheet and Dont include extranous info",
        }
    )
    response = openrouter.chat.completions.create(
        model=OPENROUTER_MODEL, messages=state["messages"]
    )
    return response.choices[0].message.content, state


def next_question(answer, state):
    if not state["questions"]:
        return (
            "*Essay will appear here...*",
            "*Start the examination first.*",
            "",
            state,
        )

    has_next_question = (
        state["current_question"] < len(state["questions"]) - 1 and answer.strip()
    )

    if answer.strip():
        state["answers"][state["current_question"]] = answer

    if has_next_question:
        state["current_question"] += 1

    return (
        state["essay_text"],
        state["questions"][state["current_question"]],
        "" if has_next_question else state["answers"][-1],
        state,
    )


def start_examination(difficulty, topic, num_questions, state):
    if state["essay_text"]:
        return (
            state["essay_text"],
            state["questions"][state["current_question"]],
            "*Analyzing...*",
            state,
        )

    state["messages"].append(
        {
            "role": "user",
            "content": get_question(difficulty, topic, num_questions) + RESPONSE_FORMAT,
        }
    )

    try:
        response = openrouter.chat.completions.create(
            model=OPENROUTER_MODEL, messages=state["messages"]
        )
        response_text = response.choices[0].message.content
        response_json = json.loads(response_text)
    except json.JSONDecodeError:
        return (
            "*Error: The AI returned malformed JSON. Please try again.*",
            "*-*",
            "",
            state,
        )

    state["essay_text"] = response_json["essay"]
    state["questions"] = response_json["questions"]
    state["answers"] = [""] * len(state["questions"])
    state["current_question"] = 0
    state["analysis"] = ""

    return (
        state["essay_text"],
        state["questions"][state["current_question"]],
        "*Analyzing...*",
        state,
    )


def run_analysis(state):
    if not state["essay_text"]:
        return "*Analysis will appear here...*", state
    if not state["analysis"]:
        state["analysis"] = analyze_essay(state["essay_text"])
    return state["analysis"], state


def reset_examination(state):
    state = new_state()
    return (
        "*Essay will appear here...*",
        "*Question will appear here...*",
        "",
        "*Feedback will appear here...*",
        "*Analysis will appear here...*",
        state,
    )


with gr.Blocks() as ui:
    exam_state = gr.State(value=new_state())

    with gr.Row():
        with gr.Column():
            difficulty = gr.Dropdown(choices=LEVELS, value="1", label="Difficulty")
        with gr.Column():
            topic = gr.Dropdown(choices=TOPICS, value=None, label="Topic")
    with gr.Row():
        with gr.Column():
            essay_text_container = gr.Markdown("*Essay will appear here...*")
            gr.Markdown("---\n**Essay Analysis**")
            analysis_container = gr.Markdown("*Analysis will appear here...*")
        with gr.Column():
            question_text_container = gr.Markdown("*Question will appear here...*")
            answer_text = gr.Textbox(
                value="",
                container=False,
                interactive=True,
                placeholder="Type your answer here",
                lines=10,
            )
            with gr.Row():
                next_btn = gr.Button("Next Question")
                submit_btn = gr.Button("Submit")
            next_btn.click(
                next_question,
                inputs=[answer_text, exam_state],
                outputs=[
                    essay_text_container,
                    question_text_container,
                    answer_text,
                    exam_state,
                ],
            )
    with gr.Row():
        start_btn = gr.Button("Start Examination")
        reset_btn = gr.Button("Reset")
    with gr.Row():
        feedback_container = gr.Markdown("*Feedback will appear here...*")

    submit_btn.click(
        submit_answers,
        inputs=[answer_text, exam_state],
        outputs=[feedback_container, exam_state],
    )

    start_btn.click(
        start_examination,
        inputs=[difficulty, topic, gr.State(value=4), exam_state],
        outputs=[
            essay_text_container,
            question_text_container,
            analysis_container,
            exam_state,
        ],
    ).then(
        run_analysis,
        inputs=[exam_state],
        outputs=[analysis_container, exam_state],
    )

    reset_btn.click(
        reset_examination,
        inputs=[exam_state],
        outputs=[
            essay_text_container,
            question_text_container,
            answer_text,
            feedback_container,
            analysis_container,
            exam_state,
        ],
    )

ui.launch(inbrowser=True)
