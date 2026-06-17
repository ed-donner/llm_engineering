"""
tools.py — Tool Definitions & Handler for Sentinel AI Interview Simulator

Defines tools in OpenAI JSON format and dispatches tool calls.
Follows the exact Day 4 reference pattern.
"""

import json
from db import save_question, end_session, get_session_summary
from scraper import scrape_domain_questions
from svg_gen import generate_svg_question

# ============================================================
# Tool JSON definitions (OpenAI function-calling format)
# ============================================================

score_answer_fn = {
    "name": "score_answer",
    "description": "Score the candidate's answer to an interview question on a scale of 1-10 and provide feedback.",
    "parameters": {
        "type": "object",
        "properties": {
            "score": {
                "type": "integer",
                "description": "Score from 1 to 10 (10 being perfect)"
            },
            "feedback": {
                "type": "string",
                "description": "Brief constructive feedback on the answer"
            },
            "question_text": {
                "type": "string",
                "description": "The question that was asked"
            },
            "answer_text": {
                "type": "string",
                "description": "The candidate's answer"
            }
        },
        "required": ["score", "feedback", "question_text", "answer_text"],
        "additionalProperties": False
    }
}

scrape_questions_fn = {
    "name": "scrape_domain_questions",
    "description": "Scrape interview questions for the candidate's chosen domain (AI or ML). Call this ONCE after the candidate selects their interview domain.",
    "parameters": {
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "enum": ["AI", "ML"],
                "description": "The interview domain chosen by the candidate"
            }
        },
        "required": ["domain"],
        "additionalProperties": False
    }
}

generate_svg_fn = {
    "name": "generate_svg_question",
    "description": "Generate a visual SVG-based interview question (bar chart, shapes, or flowchart). Use this to ask the candidate a visual/analytical question.",
    "parameters": {
        "type": "object",
        "properties": {
            "question_type": {
                "type": "string",
                "enum": ["bar_chart", "shapes", "flowchart"],
                "description": "Type of visual question to generate"
            }
        },
        "required": ["question_type"],
        "additionalProperties": False
    }
}

get_session_stats_fn = {
    "name": "get_session_stats",
    "description": "Get the current interview session statistics and performance summary.",
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "integer",
                "description": "The current session ID"
            }
        },
        "required": ["session_id"],
        "additionalProperties": False
    }
}

end_interview_fn = {
    "name": "end_interview",
    "description": "End the current interview session. Call this when the candidate admits they don't know or after 6 successful questions.",
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "integer",
                "description": "The current session ID"
            },
            "reason": {
                "type": "string",
                "enum": ["completed", "candidate_admitted", "timeout"],
                "description": "Reason for ending the interview"
            }
        },
        "required": ["session_id", "reason"],
        "additionalProperties": False
    }
}

# ============================================================
# All tools bundled for the API call
# ============================================================

TOOL_DEFINITIONS = [
    {"type": "function", "function": score_answer_fn},
    {"type": "function", "function": scrape_questions_fn},
    {"type": "function", "function": generate_svg_fn},
    {"type": "function", "function": get_session_stats_fn},
    {"type": "function", "function": end_interview_fn},
]

# ============================================================
# Tool dispatcher — maps function names to actual callables
# ============================================================

# These will be set from the notebook (session_id is dynamic)
_session_id = None
_question_number = 0


def set_session_context(session_id):
    """Set the current session context for tool calls."""
    global _session_id, _question_number
    _session_id = session_id
    _question_number = 0


def _handle_score_answer(arguments):
    global _question_number
    _question_number += 1
    score = arguments.get("score", 5)
    feedback = arguments.get("feedback", "")
    question_text = arguments.get("question_text", "")
    answer_text = arguments.get("answer_text", "")

    if _session_id:
        save_question(_session_id, question_text, answer_text, score, feedback, _question_number)

    return json.dumps({
        "score": score,
        "feedback": feedback,
        "question_number": _question_number,
        "status": "scored"
    })


def _handle_scrape_questions(arguments):
    domain = arguments.get("domain", "AI")
    return scrape_domain_questions(domain)


LAST_GENERATED_SVG = None

def _handle_generate_svg(arguments):
    global LAST_GENERATED_SVG
    q_type = arguments.get("question_type", "bar_chart")
    svg, question, answer = generate_svg_question(q_type)
    LAST_GENERATED_SVG = svg
    return json.dumps({
        "question_to_ask": question,
        "expected_answer_for_evaluation_later": answer,
        "instruction": "CRITICAL: The visual chart has been automatically shown to the candidate. You MUST ask them the 'question_to_ask' exactly as written. DO NOT answer it yourself. DO NOT describe the chart. Wait for their answer."
    })



def _handle_get_stats(arguments):
    sid = arguments.get("session_id", _session_id)
    if sid:
        return get_session_summary(sid)
    return "No active session."


def _handle_end_interview(arguments):
    sid = arguments.get("session_id", _session_id)
    reason = arguments.get("reason", "completed")
    if sid:
        end_session(sid, status=reason)
    return json.dumps({"status": "ended", "reason": reason, "session_id": sid})


# Function name → handler mapping
TOOL_MAP = {
    "score_answer": _handle_score_answer,
    "scrape_domain_questions": _handle_scrape_questions,
    "generate_svg_question": _handle_generate_svg,
    "get_session_stats": _handle_get_stats,
    "end_interview": _handle_end_interview,
}


def handle_tool_calls(message):
    """
    Process all tool calls from an LLM response.
    Same pattern as Day 4: iterate tool_calls, dispatch, return responses.
    """
    responses = []
    for tool_call in message.tool_calls:
        fn_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"TOOL DISPATCH: {fn_name}({arguments})", flush=True)

        handler = TOOL_MAP.get(fn_name)
        if handler:
            result = handler(arguments)
        else:
            result = json.dumps({"error": f"Unknown tool: {fn_name}"})

        responses.append({
            "role": "tool",
            "content": result,
            "tool_call_id": tool_call.id
        })

    return responses
