import gradio as gr
import asyncio
import json
import logging
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

from pharma_agents import (
    triage_agent,
    interaction_agent,
    allergy_agent,
    dosage_agent,
    contraindication_agent,
    verdict_agent,
)
from schemas import Drug, PatientProfile, PrescriptionInput, Finding, AgentReport, FinalVerdict

# Thread pool for running blocking agent.run() calls concurrently
_executor = ThreadPoolExecutor(max_workers=4)


# ── Formatting functions ───────────────────────────────────────────────────────────────

def format_finding(f: Finding) -> str:
    icons = {"SAFE": "✅", "WARNING": "⚠️", "CRITICAL": "❌", "ERROR": "🚫"}
    icon = icons.get(f.severity.upper(), "❓")
    return f"{icon} **{f.severity}**  \n{f.message.strip()}"


def format_agent_report(r: AgentReport) -> str:
    icons  = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}
    colors = {"GREEN": "green", "YELLOW": "#d97706", "RED": "crimson"}
    icon  = icons.get(r.status, "⚪")
    color = colors.get(r.status, "gray")

    lines = [f"### {icon} {r.agent_name} — **{r.status}**"]

    if not r.findings:
        lines.append("→ No issues detected.")
    else:
        lines.extend(format_finding(f) for f in r.findings)

    return "\n".join(lines)


def format_verdict(v: FinalVerdict) -> str:
    icons  = {
        "GREEN":  "✅ SAFE TO DISPENSE",
        "YELLOW": "⚠️ CAUTION",
        "RED":    "🚫 DO NOT DISPENSE"
    }
    colors = {"GREEN": "green", "YELLOW": "#d97706", "RED": "crimson"}

    icon  = icons.get(v.status, "❓")
    color = colors.get(v.status, "gray")

    lines = [
        f"# {icon}",
        f"**Status:** <span style='color:{color}; font-weight:bold;'>{v.status}</span>\n",
        f"**Summary**  \n{v.summary.strip()}"
    ]

    if v.required_actions:
        lines.append("\n**Required Actions**")
        lines.extend(f"- {action.strip()}" for action in v.required_actions)

    return "\n".join(lines)


def format_complete_output(reports: List[AgentReport], verdict: FinalVerdict) -> Tuple[str, str, str]:
    verdict_md = format_verdict(verdict)

    reports_md = ["# Agent Reports\n"]
    if reports:
        reports_md.extend(format_agent_report(r) for r in reports)
    else:
        reports_md.append("No agent reports available.")

    raw_json = json.dumps({
        "verdict": verdict.model_dump() if hasattr(verdict, "model_dump") else vars(verdict),
        "reports": [r.model_dump() if hasattr(r, "model_dump") else vars(r) for r in reports]
    }, indent=2)

    return verdict_md, "\n".join(reports_md), raw_json


# ── Core analysis logic ──────────────────────────────────────────────────────────────

def safe_json(obj) -> str:
    if hasattr(obj, "model_dump_json"):
        return obj.model_dump_json(indent=2)
    if hasattr(obj, "dict"):
        return json.dumps(obj.dict(), indent=2)
    return json.dumps(obj, indent=2, default=str)


async def analyse_prescription(
    patient: PatientProfile,
    drugs: List[Drug]
) -> Tuple[str, str, str]:
    input_data = PrescriptionInput(patient=patient, drugs=drugs)

    # Triage: extract structured data from raw input
    triage_output = triage_agent.run(input_data.model_dump_json())
    context_str = safe_json(triage_output)

    # Run 4 specialist agents concurrently via thread pool (they use blocking OpenAI calls)
    loop = asyncio.get_event_loop()
    results = await asyncio.gather(
        loop.run_in_executor(_executor, interaction_agent.run, context_str),
        loop.run_in_executor(_executor, allergy_agent.run, context_str),
        loop.run_in_executor(_executor, dosage_agent.run, context_str),
        loop.run_in_executor(_executor, contraindication_agent.run, context_str),
    )

    reports: List[AgentReport] = list(results)

    # Verdict: synthesise all reports
    verdict: FinalVerdict = verdict_agent.run(safe_json(reports))

    return format_complete_output(reports, verdict)


# ── Input parsing & test data ─────────────────────────────────────────────────────────

async def run_analysis(
    age: float | int | None,
    weight: float | None,
    allergies_raw: str,
    conditions_raw: str,
    drugs_raw: str
) -> Tuple[str, str, str]:
    try:
        age    = int(age)    if age is not None else 40
        weight = float(weight) if weight is not None else 70.0

        allergies  = [a.strip() for a in allergies_raw.split(",")  if a.strip()]
        conditions = [c.strip() for c in conditions_raw.split(",") if c.strip()]

        drug_lines = [line.strip() for line in drugs_raw.split("\n") if line.strip()]
        drugs = []

        for line in drug_lines:
            parts = line.split(maxsplit=2)
            if len(parts) < 2: continue
            drugs.append(Drug(
                name=parts[0].strip(),
                dosage=parts[1].strip(),
                frequency=parts[2].strip() if len(parts) > 2 else "—"
            ))

        if not drugs:
            err = "**Error**: Please enter at least one medication."
            return err, err, err

        patient = PatientProfile(
            age=age,
            weight_kg=weight,
            allergies=allergies,
            conditions=conditions
        )

        return await analyse_prescription(patient, drugs)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        err_msg = f"**Processing error**\n\n{str(e)}\n\n```python\n{tb[-800:]}```"
        return err_msg, err_msg, err_msg


def load_test_case_1():
    return (
        42,
        68.0,
        "penicillin, shellfish",
        "hypertension, type 2 diabetes",
        "Amoxicillin 500mg\nMetformin 850mg\nRamipril 10mg"
    )


def load_test_case_2():
    return (
        78,
        59.5,
        "aspirin, codeine",
        "atrial fibrillation, CKD stage 3, history of GI bleed",
        "Apixaban 5mg 12-hourly\nParacetamol 1g QID prn\nIbuprofen 400mg TDS"
    )


def load_test_case_3():
    return (
        31,
        88.0,
        "",
        "epilepsy, depression",
        "Carbamazepine 400mg BD\nSertraline 100mg daily\nParacetamol 1g QID prn"
    )


def clear_form():
    return (
        48, "", "", "", "",
        "Waiting for prescription data...",
        "Waiting for prescription data...",
        "Waiting for prescription data...",
    )

# ── Gradio UI ──────────────────────────────────────────────────────────────────────────

with gr.Blocks() as demo:

    gr.Markdown("""
    # Prescription Safety Review

    Enter patient details and medications → multi-agent safety check.
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Patient")
            age_in       = gr.Number(label="Age (years)", value=48, minimum=0, maximum=120)
            weight_in    = gr.Number(label="Weight (kg)", value=72.5, minimum=10, maximum=300)
            allergies_in = gr.Textbox(label="Allergies (comma separated)", lines=2,
                                      placeholder="penicillin, sulfa, latex")
            conditions_in = gr.Textbox(label="Medical conditions", lines=3,
                                       placeholder="type 2 diabetes, hypertension, CKD stage 3")

        with gr.Column(scale=1):
            gr.Markdown("### Medications")
            drugs_in = gr.Textbox(
                label="One medication per line (name dosage frequency)",
                lines=9,
                max_lines=14,
                placeholder="Amoxicillin 500mg 8-hourly\nWarfarin 5mg daily\n..."
            )

    with gr.Row():
        gr.Markdown("**Quick test cases:**")
        btn_test1 = gr.Button("Case 1 – Middle-aged, common drugs", size="sm")
        btn_test2 = gr.Button("Case 2 – Elderly + high risk", size="sm")
        btn_test3 = gr.Button("Case 3 – Young adult + psych drugs", size="sm")

    with gr.Row():
        btn_analyze = gr.Button("Run Safety Check", variant="primary", scale=2)
        btn_clear   = gr.Button("Clear All", variant="secondary")

    with gr.Tabs() as tabs:
        with gr.TabItem("Final Verdict", elem_id="verdict-tab"):
            result_verdict = gr.Markdown(
                value="Waiting for input...",
                label="Final Recommendation",
                line_breaks=True,
                height=520
            )

        with gr.TabItem("Agent Reports"):
            result_reports = gr.Markdown(
                value="Waiting for analysis...",
                line_breaks=True,
                height=520
            )

        with gr.TabItem("Raw JSON"):
            result_json = gr.Code(
                value="{}",
                language="json",
                lines=24,
                interactive=False
            )

    # ── Event handlers ────────────────────────────────────────────────────────────────

    btn_analyze.click(
        fn=run_analysis,
        inputs=[age_in, weight_in, allergies_in, conditions_in, drugs_in],
        outputs=[result_verdict, result_reports, result_json]
    )

    btn_test1.click(
        fn=load_test_case_1,
        outputs=[age_in, weight_in, allergies_in, conditions_in, drugs_in]
    )

    btn_test2.click(
        fn=load_test_case_2,
        outputs=[age_in, weight_in, allergies_in, conditions_in, drugs_in]
    )

    btn_test3.click(
        fn=load_test_case_3,
        outputs=[age_in, weight_in, allergies_in, conditions_in, drugs_in]
    )

    btn_clear.click(
        fn=clear_form,
        outputs=[age_in, weight_in, allergies_in, conditions_in, drugs_in,
                 result_verdict, result_reports, result_json]
    )

if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="slate",
            font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"]
        )
    )