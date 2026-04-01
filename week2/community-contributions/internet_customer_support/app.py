"""
ISP Internet Customer Support — Gradio chat + SQLite tools + TTS + end-of-session guide image.

Inspired by week2/day5.ipynb (Airline assistant): tool calling, multimodal TTS and DALL-E.

Run:  python app.py
Requires: OPENAI_API_KEY in .env (see course setup).
"""

from __future__ import annotations

import base64
import json
import os
import re
import tempfile
from io import BytesIO
from typing import Any, Optional

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

import db

load_dotenv(override=True)

MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

db.init_db()
db.seed_demo_data()

client = OpenAI()

SYSTEM_MESSAGE = """
You are the senior internet troubleshooting expert for "NetLink ISP", a home broadband provider.

Context you must assume:
- Customers have a modem/router inside the home; issues may be Wi-Fi, LAN, or on NetLink's network.
- Customers can log into the ISP self-service portal to see remaining data (GB), plan name, and line status.
- You do NOT have direct access to their home devices; you guide them step by step and use tools for account/line data when they provide an account ID or phone number.

Behavior:
- Be calm, concise, and practical. Ask one clarifying question at a time when needed.
- Prefer a short checklist: reboot order, cable checks, portal verification, outage checks.
- When the user gives an account id (e.g. NL-10042) or phone, call the account lookup tool.
- When discussing outages/maintenance, call the regional service tool with their region if known.
- If data is exhausted or line is throttled, explain portal usage and upgrade/add-on options clearly.
- Never invent tool results; only state what tools return.
- If you are unsure, say so and suggest contacting a human technician with what to tell them.

Visual troubleshooting guide (important):
- The NetLink support app can render a real guide image (DALL-E) in the right-hand panel when requested.
- If the customer asks for a picture, diagram, infographic, or "draw" the steps, you MUST call the tool
  `generate_troubleshooting_guide_image` (after you have given useful troubleshooting text). Do not say you
  cannot draw or that images are impossible; say the guide is being generated and will appear beside the chat.

Safety:
- Do not ask for passwords or full payment card numbers.
""".strip()


def _tool_specs() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "lookup_account_internet_status",
                "description": (
                    "Look up demo account data: remaining GB, plan, line status, modem last seen, "
                    "and region. Requires either account_id (e.g. NL-10042) or phone number."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Customer account id, e.g. NL-10042",
                        },
                        "phone": {
                            "type": "string",
                            "description": "Phone on file, e.g. +15551234001",
                        },
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_regional_service_events",
                "description": (
                    "Check known maintenance/outage messages for a region (e.g. West Coast) "
                    "or all regions if omitted."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Region name from account lookup, or empty for all",
                        },
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "record_support_note",
                "description": (
                    "Store a short internal support note tied to an account id after key troubleshooting steps."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Account id, e.g. NL-10042",
                        },
                        "note": {
                            "type": "string",
                            "description": "Brief factual note about what was tried or found",
                        },
                    },
                    "required": ["account_id", "note"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_troubleshooting_guide_image",
                "description": (
                    "Request a visual troubleshooting guide image summarizing the chat so far. "
                    "Call when the customer asks for a diagram, picture, infographic, or to 'draw' the steps, "
                    "or when you want to offer a visual recap after explaining fixes."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "focus": {
                            "type": "string",
                            "description": "Optional short hint for the illustration, e.g. 'Wi-Fi reboot order'",
                        },
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
    ]


TOOLS = _tool_specs()


def _format_account_row(row: dict[str, Any]) -> str:
    return json.dumps(
        {
            "account_id": row["account_id"],
            "phone": row["phone"],
            "customer_name": row["customer_name"],
            "plan_name": row["plan_name"],
            "data_remaining_gb": row["data_remaining_gb"],
            "data_cap_gb": row["data_cap_gb"],
            "billing_cycle_end": row["billing_cycle_end"],
            "line_status": row["line_status"],
            "modem_last_seen": row["modem_last_seen"],
            "region": row["region"],
        },
        indent=2,
    )


def _assistant_message_as_api_dict(message: Any) -> dict[str, Any]:
    assistant_msg: dict[str, Any] = {
        "role": "assistant",
        "content": message.content or "",
    }
    if message.tool_calls:
        assistant_msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments or "{}",
                },
            }
            for tc in message.tool_calls
        ]
    return assistant_msg


def handle_tool_calls(message: Any) -> tuple[list[dict[str, Any]], bool]:
    """Returns (tool response messages, whether guide image generation was requested)."""
    responses: list[dict[str, Any]] = []
    requests_guide_image = False
    for tool_call in message.tool_calls or []:
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}

        if name == "lookup_account_internet_status":
            aid = args.get("account_id") or None
            phone = args.get("phone") or None
            if not aid and not phone:
                out = "Error: provide account_id or phone for lookup."
            else:
                row = db.lookup_account(aid, phone)
                out = (
                    _format_account_row(row)
                    if row
                    else "No matching account in demo database. Ask customer to verify id/phone."
                )
        elif name == "get_regional_service_events":
            region = args.get("region") or None
            evs = db.get_events_for_region(region)
            out = json.dumps(evs, indent=2) if evs else "No service events on file."
        elif name == "record_support_note":
            aid = (args.get("account_id") or "").strip()
            note = (args.get("note") or "").strip()
            if not aid or not note:
                out = "Error: account_id and note are required."
            else:
                nid = db.insert_support_note(aid, note)
                out = f"Note saved (id {nid}) for account {aid}."
        elif name == "generate_troubleshooting_guide_image":
            requests_guide_image = True
            focus = (args.get("focus") or "").strip()
            focus_bit = f" (focus: {focus})" if focus else ""
            out = (
                "OK — the app will render a troubleshooting guide image in the right panel"
                f"{focus_bit}, based on this conversation. Tell the customer it should appear shortly."
            )
        else:
            out = f"Unknown tool {name}"

        responses.append(
            {
                "role": "tool",
                "content": out,
                "tool_call_id": tool_call.id,
            }
        )
    return responses, requests_guide_image


def run_chat_completion(messages: list[dict[str, Any]]) -> Any:
    return client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        temperature=0.4,
    )


def assistant_reply(history: list[dict[str, Any]]) -> tuple[str, bool]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_MESSAGE}]
    for h in history:
        messages.append(
            {"role": h["role"], "content": (h.get("content") or "")}
        )

    response = run_chat_completion(messages)
    requested_image = False

    while response.choices[0].finish_reason == "tool_calls":
        msg = response.choices[0].message
        tool_responses, batch_image = handle_tool_calls(msg)
        if batch_image:
            requested_image = True
        messages.append(_assistant_message_as_api_dict(msg))
        messages.extend(tool_responses)
        response = run_chat_completion(messages)

    return response.choices[0].message.content or "", requested_image


def talker_to_file(text: str, voice: str) -> Optional[str]:
    clean = (text or "").strip()
    if len(clean) > 4000:
        clean = clean[:3997] + "..."
    if voice not in ("onyx", "alloy"):
        voice = "onyx"
    response = client.audio.speech.create(
        model=TTS_MODEL,
        voice=voice,
        input=clean,
    )
    data = response.content
    fd, path = tempfile.mkstemp(suffix=".mp3")
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return path


def summarize_for_image(history: list[dict[str, Any]]) -> tuple[str, str]:
    """Return (short summary, image prompt) for DALL-E."""
    transcript = "\n".join(
        f"{m['role']}: {m['content']}" for m in history[-40:]
    )
    user_prompt = f"""
Summarize this NetLink ISP support chat for two outputs:

1) summary: 2-3 sentences: main issue, likely cause, fix steps agreed.
2) image_prompt: One paragraph describing a CLEAR, simple educational illustration
   (flat vector / manual style): home modem/router, cables, optional technician icon.
   No gore, no politics. Minimal readable labels only if any ("modem", "router", "portal").
   Describe layout for someone learning to troubleshoot internet at home.

Transcript:
{transcript}
""".strip()

    r = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Reply ONLY with valid JSON: {\"summary\": \"...\", \"image_prompt\": \"...\"}",
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    raw = (r.choices[0].message.content or "{}").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
        summary = str(data.get("summary", "")).strip()
        img_prompt = str(data.get("image_prompt", "")).strip()
    except json.JSONDecodeError:
        summary = raw[:500]
        img_prompt = (
            "Friendly flat vector infographic: home Wi-Fi router and modem, "
            "simple arrows showing power cycle and checking cables, soft blue and white."
        )
    if not img_prompt:
        img_prompt = (
            "Friendly flat vector infographic: home Wi-Fi router and modem, "
            "simple troubleshooting steps, soft blue and white."
        )
    return summary, img_prompt


def _user_wants_guide_image(text: str) -> bool:
    """Fallback if the model forgets to call the image tool but the user clearly asked."""
    t = text.lower()
    phrases = (
        "guide image",
        "visual guide",
        "picture of",
        "draw a",
        "draw an",
        "diagram",
        "infographic",
        "generate an image",
        "generate a image",
        "create an image",
        "show me a picture",
        "show me an image",
        "can you draw",
        "could you draw",
        "please draw",
        "illustration of",
    )
    if any(p in t for p in phrases):
        return True
    if "image" in t and any(
        w in t for w in ("generate", "create", "draw", "make", "show", "give me")
    ):
        return True
    return False


def generate_guide_for_session(
    history: list[dict[str, Any]], session_id: str
) -> tuple[Image.Image, str]:
    summary, image_prompt = summarize_for_image(history)
    img = render_guide_image(image_prompt)
    db.end_session_record(session_id, summary, image_prompt)
    status = (
        f"Guide image generated.\n\n**Summary:** {summary}\n\n"
        "(Demo: DALL-E charges apply.)"
    )
    return img, status


def render_guide_image(image_prompt: str) -> Image.Image:
    full_prompt = (
        f"{image_prompt} "
        "Professional ISP customer education poster style, clean composition, "
        "no scary imagery, no logos except generic shapes."
    )
    image_response = client.images.generate(
        model=IMAGE_MODEL,
        prompt=full_prompt[:3800],
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    b64 = image_response.data[0].b64_json
    if not b64:
        raise RuntimeError("Image API returned empty payload")
    raw = base64.b64decode(b64)
    return Image.open(BytesIO(raw))


def chat_turn(
    message: str,
    history: list[dict[str, Any]],
    session_id: str,
    voice: str,
):
    if not message or not str(message).strip():
        return (
            history,
            session_id,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    sid = session_id or db.create_session()
    user_text = str(message).strip()
    db.append_message(sid, "user", user_text)

    new_history = history + [{"role": "user", "content": user_text}]

    image_from_tool = False
    try:
        reply, image_from_tool = assistant_reply(new_history)
    except Exception as exc:
        reply = f"Sorry — something went wrong ({exc}). Please try again in a moment."

    new_history = new_history + [{"role": "assistant", "content": reply}]
    db.append_message(sid, "assistant", reply)

    try:
        audio_path = talker_to_file(reply, voice)
    except Exception:
        audio_path = None

    should_generate_image = image_from_tool or _user_wants_guide_image(user_text)
    if should_generate_image:
        try:
            img, status_md = generate_guide_for_session(new_history, sid)
            guide_out = img
            status_out = status_md
        except Exception as exc:
            guide_out = gr.update()
            status_out = f"Could not generate the guide image: {exc}"
    else:
        guide_out = gr.update()
        status_out = gr.update()

    return new_history, sid, audio_path, "", guide_out, status_out


def finish_session(
    history: list[dict[str, Any]],
    session_id: str,
):
    if not history or len(history) < 2:
        return None, "Have a short conversation first, then generate the guide image.", session_id

    sid = session_id or db.create_session()
    try:
        img, status = generate_guide_for_session(history, sid)
        return img, status, sid
    except Exception as exc:
        return None, f"Could not generate image: {exc}", sid


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="NetLink ISP — Internet Support") as ui:
        gr.Markdown(
            """
            ## NetLink ISP — Internet troubleshooting assistant  
            **Demo:** SQLite-backed account/outage lookups, voice reply (**onyx** or **alloy**), and an **end-of-chat visual guide** (DALL-E).  
            Try account **NL-10042** or phone **+15551234001** after describing your issue.
            """
        )
        session_state = gr.State("")
        with gr.Row():
            chatbot = gr.Chatbot(
                label="Chat",
                height=480,
                type="messages",
            )
            guide_image = gr.Image(label="Troubleshooting guide (after session)", height=480)
        with gr.Row():
            audio_out = gr.Audio(label="Voice (TTS)", autoplay=True)
        with gr.Row():
            msg = gr.Textbox(
                label="Describe your internet issue",
                placeholder="e.g. My Wi-Fi drops every hour and the portal shows I still have data…",
                scale=4,
            )
            voice = gr.Dropdown(
                choices=["onyx", "alloy"],
                value="onyx",
                label="Voice",
            )
        with gr.Row():
            clear_btn = gr.Button("Clear chat")
            done_btn = gr.Button("End session & generate guide image", variant="primary")
        status = gr.Markdown()

        msg.submit(
            chat_turn,
            inputs=[msg, chatbot, session_state, voice],
            outputs=[chatbot, session_state, audio_out, msg, guide_image, status],
        )

        clear_btn.click(
            lambda: ([], "", None, "", None, ""),
            outputs=[chatbot, session_state, audio_out, msg, guide_image, status],
        )

        done_btn.click(
            finish_session,
            inputs=[chatbot, session_state],
            outputs=[guide_image, status, session_state],
        )

    return ui


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your environment or .env file.")
    build_ui().launch(inbrowser=True)
