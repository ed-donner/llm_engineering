"""
╔══════════════════════════════════════════════════════════╗
║          AI Interview Simulator — Multi-Agent            ║
║                                                          ║
║  3 Agents:  Interviewer · Evaluator · Coach              ║
║  No database required — all state held in memory         ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# ── Initialization ───────────────────────────────────────────────────────────

load_dotenv(override=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set — set OPENAI_API_KEY in .env")

MODEL = "gpt-4.1-mini"
client = OpenAI()

# ── Agent System Prompts ─────────────────────────────────────────────────────

INTERVIEWER_SYSTEM = """
You are a senior technical interviewer at a top tech company.
Your job is to conduct a realistic, adaptive job interview.

Rules:
- Ask ONE question at a time. Never ask two questions together.
- Start with a question appropriate for the role and difficulty level provided.
- After receiving the candidate's answer AND the evaluator's score, adjust the NEXT question:
    * Score 4-5  → increase difficulty or move to a deeper topic
    * Score 2-3  → same difficulty, related topic
    * Score 0-1  → simplify or probe understanding with a follow-up
- Keep each question concise (2-4 sentences max).
- Do NOT evaluate the answer yourself — that is the Evaluator's job.
- Vary question types: conceptual, coding, system-design, behavioral, situational.
- Begin your message with exactly: "QUESTION: " followed by the question text.
- When the interview is complete (after the requested number of questions), begin with: "INTERVIEW COMPLETE"
"""

EVALUATOR_SYSTEM = """
You are an expert technical evaluator assessing interview answers.
Given a question and a candidate's answer, produce a structured evaluation.

Output ONLY valid JSON in this exact format:
{
  "clarity_score": <0-5>,
  "technical_score": <0-5>,
  "overall_score": <0-5>,
  "strengths": "<one concise sentence>",
  "gaps": "<one concise sentence about what was missing or wrong>",
  "keywords_used": ["keyword1", "keyword2"]
}

Scoring guide (0-5):
  5 = Exceptional — thorough, accurate, well-structured
  4 = Good — mostly correct with minor gaps
  3 = Adequate — correct but shallow or incomplete
  2 = Weak — partial understanding, notable errors
  1 = Poor — mostly incorrect or confused
  0 = No meaningful answer

Be strict and honest. Do NOT inflate scores.
"""

COACH_SYSTEM = """
You are a supportive but honest interview coach.
Given a question, a candidate's answer, and an evaluation, provide:

1. A 2-sentence "What went well" observation
2. A 2-sentence "What to improve" recommendation
3. A concise "Model Answer" (4-8 sentences) that would score a 5/5

Format your response with clear headers:
✅ **What Went Well**
<text>

⚠️ **What to Improve**
<text>

💡 **Model Answer**
<text>

Keep your tone encouraging but direct. Focus on actionable improvements.
"""

# ── Agent Call Helpers ───────────────────────────────────────────────────────

def call_interviewer(role: str, difficulty: str, conversation_history: list,
                     last_eval: dict | None, questions_asked: int,
                     total_questions: int) -> str:
    """Ask the Interviewer agent for the next question."""
    context = (
        f"Role being interviewed for: {role}\n"
        f"Starting difficulty: {difficulty}\n"
        f"Questions asked so far: {questions_asked} / {total_questions}\n"
    )
    if last_eval:
        context += f"Last answer's overall score: {last_eval.get('overall_score', 'N/A')}/5\n"
        context += f"Gaps identified: {last_eval.get('gaps', '')}\n"

    messages = [
        {"role": "system", "content": INTERVIEWER_SYSTEM},
        {"role": "user",   "content": context},
    ] + conversation_history

    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content.strip()


def call_evaluator(question: str, answer: str) -> dict:
    """Ask the Evaluator agent to score the answer."""
    prompt = f"Question: {question}\n\nCandidate's Answer: {answer}"
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"clarity_score": 0, "technical_score": 0, "overall_score": 0,
                "strengths": "Parse error", "gaps": raw, "keywords_used": []}


def call_coach(question: str, answer: str, evaluation: dict) -> str:
    """Ask the Coach agent for improvement tips and a model answer."""
    prompt = (
        f"Question: {question}\n\n"
        f"Candidate's Answer: {answer}\n\n"
        f"Evaluation: {json.dumps(evaluation, indent=2)}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": COACH_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


# ── Scoring Summary Helper ───────────────────────────────────────────────────

def build_score_card(scores: list[dict]) -> str:
    if not scores:
        return ""
    avg_clarity   = sum(s["clarity_score"]   for s in scores) / len(scores)
    avg_technical = sum(s["technical_score"] for s in scores) / len(scores)
    avg_overall   = sum(s["overall_score"]   for s in scores) / len(scores)

    bar = lambda v: "█" * round(v) + "░" * (5 - round(v))

    lines = [
        "## 📊 Interview Score Card",
        "",
        f"**Questions Answered:** {len(scores)}",
        "",
        f"| Dimension      | Score | Bar         |",
        f"|----------------|-------|-------------|",
        f"| Clarity        | {avg_clarity:.1f}/5 | {bar(avg_clarity)} |",
        f"| Technical      | {avg_technical:.1f}/5 | {bar(avg_technical)} |",
        f"| **Overall**    | **{avg_overall:.1f}/5** | **{bar(avg_overall)}** |",
    ]
    if avg_overall >= 4:
        lines += ["", "🌟 **Outstanding performance!** You're interview-ready."]
    elif avg_overall >= 3:
        lines += ["", "👍 **Solid performance.** A bit more practice and you'll shine."]
    elif avg_overall >= 2:
        lines += ["", "📚 **Keep practising.** Focus on depth and precision."]
    else:
        lines += ["", "🔄 **Early stage.** Review fundamentals and try again!"]
    return "\n".join(lines)


# ── Core Interview State ─────────────────────────────────────────────────────

def start_interview(role: str, difficulty: str, num_questions: int,
                    history: list, state: dict):
    """Kick off a new interview session."""
    state = {
        "role": role,
        "difficulty": difficulty,
        "total_questions": int(num_questions),
        "questions_asked": 0,
        "current_question": "",
        "scores": [],
        "conversation_history": [],
        "active": True,
    }

    question_msg = call_interviewer(
        role=role, difficulty=difficulty,
        conversation_history=[], last_eval=None,
        questions_asked=0, total_questions=int(num_questions),
    )

    # Extract clean question text
    clean_q = question_msg.replace("QUESTION:", "").strip()
    state["current_question"] = clean_q
    state["questions_asked"] = 1
    state["conversation_history"].append({"role": "assistant", "content": question_msg})

    history = []
    history.append({"role": "assistant", "content": f"**Question 1 of {int(num_questions)}**\n\n{clean_q}"})

    return history, state, gr.update(interactive=True), gr.update(interactive=False), ""


def submit_answer(user_answer: str, history: list, state: dict):
    """Process user's answer through Evaluator → Coach → Interviewer."""
    if not state.get("active"):
        return history, state, "", ""

    if not user_answer.strip():
        return history, state, "", "⚠️ Please type an answer before submitting."

    current_q = state["current_question"]
    history.append({"role": "user", "content": user_answer})
    state["conversation_history"].append({"role": "user", "content": user_answer})

    # ── Evaluator ─────────────────────────────────────────────────────────────
    evaluation = call_evaluator(current_q, user_answer)
    state["scores"].append(evaluation)

    eval_display = (
        f"**📋 Evaluation**\n"
        f"- Clarity: **{evaluation['clarity_score']}/5**  "
        f"Technical: **{evaluation['technical_score']}/5**  "
        f"Overall: **{evaluation['overall_score']}/5**\n"
        f"- ✅ {evaluation.get('strengths','')}\n"
        f"- ⚠️ {evaluation.get('gaps','')}"
    )

    # ── Coach ─────────────────────────────────────────────────────────────────
    coaching = call_coach(current_q, user_answer, evaluation)

    feedback_block = eval_display + "\n\n" + coaching
    history.append({"role": "assistant", "content": feedback_block})

    # ── Check if done ─────────────────────────────────────────────────────────
    if state["questions_asked"] >= state["total_questions"]:
        score_card = build_score_card(state["scores"])
        history.append({"role": "assistant", "content": f"---\n{score_card}"})
        state["active"] = False
        return history, state, "", ""

    # ── Next question ─────────────────────────────────────────────────────────
    next_q_msg = call_interviewer(
        role=state["role"], difficulty=state["difficulty"],
        conversation_history=state["conversation_history"],
        last_eval=evaluation,
        questions_asked=state["questions_asked"],
        total_questions=state["total_questions"],
    )

    if "INTERVIEW COMPLETE" in next_q_msg:
        score_card = build_score_card(state["scores"])
        history.append({"role": "assistant", "content": f"---\n{score_card}"})
        state["active"] = False
        return history, state, "", ""

    clean_nq = next_q_msg.replace("QUESTION:", "").strip()
    state["current_question"] = clean_nq
    state["questions_asked"] += 1
    state["conversation_history"].append({"role": "assistant", "content": next_q_msg})

    q_num = state["questions_asked"]
    total = state["total_questions"]
    history.append({"role": "assistant",
                    "content": f"**Question {q_num} of {total}**\n\n{clean_nq}"})

    return history, state, "", ""


# ── Gradio UI ────────────────────────────────────────────────────────────────

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:        #0d0f14;
    --surface:   #151820;
    --border:    #252a36;
    --accent:    #00e5c3;
    --accent2:   #7b6ff0;
    --danger:    #ff4d6d;
    --text:      #e8eaf0;
    --muted:     #6b7280;
    --radius:    12px;
}

body, .gradio-container { background: var(--bg) !important; font-family: 'Syne', sans-serif !important; color: var(--text) !important; }

h1, h2, h3 { font-family: 'Syne', sans-serif !important; font-weight: 800 !important; }

.panel-title {
    font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px;
    color: var(--accent); margin-bottom: 4px;
}
.panel-sub { font-size: 0.85rem; color: var(--muted); margin-bottom: 20px; }

/* Chatbot */
.chatbot { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; font-family: 'JetBrains Mono', monospace !important; }
.message.user   { background: #1e2433 !important; border-radius: 10px !important; }
.message.bot    { background: #131820 !important; border-left: 3px solid var(--accent) !important; border-radius: 10px !important; }

/* Inputs */
.gr-textbox textarea, .gr-dropdown select, .gr-slider input {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
}
.gr-textbox textarea:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 2px rgba(0,229,195,0.15) !important; }

/* Buttons */
button.primary { background: var(--accent) !important; color: #0d0f14 !important; font-weight: 700 !important; border-radius: 8px !important; font-family: 'Syne', sans-serif !important; transition: all 0.2s !important; }
button.primary:hover { filter: brightness(1.1) !important; transform: translateY(-1px) !important; }
button.secondary { background: transparent !important; border: 1px solid var(--border) !important; color: var(--text) !important; border-radius: 8px !important; font-family: 'Syne', sans-serif !important; }

/* Label */
label { color: var(--muted) !important; font-size: 0.8rem !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; }

.error-msg { color: var(--danger) !important; font-size: 0.85rem !important; padding: 6px 0 !important; }

/* Header banner */
.header-banner {
    background: linear-gradient(135deg, #0d0f14 0%, #151c2e 50%, #0d0f14 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px 32px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.header-banner::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 20% 50%, rgba(0,229,195,0.06) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 50%, rgba(123,111,240,0.06) 0%, transparent 60%);
}
.header-banner h1 { font-size: 2rem; margin: 0; background: linear-gradient(90deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-badge {
    display: inline-block; background: rgba(0,229,195,0.12); color: var(--accent);
    border: 1px solid rgba(0,229,195,0.3); border-radius: 20px;
    padding: 3px 12px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; margin-top: 8px;
}
"""

def build_ui():
    with gr.Blocks(css=CUSTOM_CSS, title="AI Interview Simulator") as demo:

        # ── Header ──────────────────────────────────────────────────────────
        gr.HTML("""
        <div class="header-banner">
            <h1>⚡ AI Interview Simulator</h1>
            <p style="color:#6b7280;margin:6px 0 0;">Three-agent system: Interviewer · Evaluator · Coach</p>
            <span class="header-badge">MULTI-AGENT</span>
        </div>
        """)

        # ── Shared State ────────────────────────────────────────────────────
        state = gr.State({})

        with gr.Row(equal_height=False):

            # ── Left Panel: Config ───────────────────────────────────────────
            with gr.Column(scale=1, min_width=280):
                gr.HTML('<div class="panel-title">🎯 Setup</div><div class="panel-sub">Configure your interview session</div>')

                role_input = gr.Dropdown(
                    label="Role",
                    choices=[
                        "Backend Engineer",
                        "Frontend Engineer",
                        "Full-Stack Engineer",
                        "AI / ML Engineer",
                        "Data Scientist",
                        "DevOps / Platform Engineer",
                        "System Design",
                        "Product Manager",
                        "Custom…",
                    ],
                    value="AI / ML Engineer",
                )
                custom_role = gr.Textbox(label="Custom Role (if selected above)", placeholder="e.g. Robotics Engineer", visible=False)

                difficulty_input = gr.Dropdown(
                    label="Starting Difficulty",
                    choices=["Junior", "Mid-level", "Senior", "Staff / Principal"],
                    value="Mid-level",
                )
                num_q_input = gr.Slider(label="Number of Questions", minimum=3, maximum=10, value=5, step=1)

                start_btn = gr.Button("▶  Start Interview", variant="primary", size="lg")
                gr.HTML('<hr style="border-color:#252a36;margin:16px 0;">')
                gr.HTML('<div style="font-size:0.75rem;color:#6b7280;line-height:1.7;">'
                        '🤖 <b>Interviewer</b> — asks adaptive questions<br>'
                        '📋 <b>Evaluator</b> — scores clarity & technical depth<br>'
                        '💡 <b>Coach</b> — gives model answers & tips'
                        '</div>')

            # ── Right Panel: Chat ────────────────────────────────────────────
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Interview Session",
                    height=560,
                    type="messages",
                    show_copy_button=True,
                    avatar_images=(None, "https://api.dicebear.com/7.x/bottts-neutral/svg?seed=interviewer"),
                )
                error_box = gr.HTML("")

                with gr.Row():
                    answer_input = gr.Textbox(
                        label="Your Answer",
                        placeholder="Type your answer here… (Shift+Enter for new line)",
                        lines=3,
                        interactive=False,
                        scale=5,
                    )
                    submit_btn = gr.Button("Submit →", variant="primary", scale=1, interactive=False)

        # ── Show/hide custom role ────────────────────────────────────────────
        def toggle_custom(val):
            return gr.update(visible=(val == "Custom…"))

        role_input.change(toggle_custom, inputs=role_input, outputs=custom_role)

        # ── Resolve final role ───────────────────────────────────────────────
        def resolve_role(role, custom):
            return custom.strip() if role == "Custom…" and custom.strip() else role

        # ── Start handler ────────────────────────────────────────────────────
        def on_start(role, custom, difficulty, num_q):
            final_role = resolve_role(role, custom)
            hist, st, ans_ui, btn_ui, err = start_interview(final_role, difficulty, num_q, [], {})
            return hist, st, ans_ui, btn_ui, ""

        start_btn.click(
            fn=on_start,
            inputs=[role_input, custom_role, difficulty_input, num_q_input],
            outputs=[chatbot, state, answer_input, start_btn, error_box],
        )

        # ── Submit handler ───────────────────────────────────────────────────
        def on_submit(answer, history, st):
            if not answer.strip():
                return history, st, answer, gr.HTML('<span class="error-msg">⚠️ Please type an answer before submitting.</span>')
            hist, st2, clear_ans, _ = submit_answer(answer, history, st)
            return hist, st2, "", ""

        submit_btn.click(
            fn=on_submit,
            inputs=[answer_input, chatbot, state],
            outputs=[chatbot, state, answer_input, error_box],
        )

        answer_input.submit(
            fn=on_submit,
            inputs=[answer_input, chatbot, state],
            outputs=[chatbot, state, answer_input, error_box],
        )

        # Enable submit button after start
        start_btn.click(
            fn=lambda: (gr.update(interactive=True), gr.update(interactive=True)),
            outputs=[answer_input, submit_btn],
        )

    return demo


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ui = build_ui()
    ui.launch(inbrowser=True)