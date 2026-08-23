"""
Gradio app for HF Spaces deployment.
Heavy inference runs on Modal (SpecialistAgent) and OpenAI API (RAG + Frontier).
Modal credentials are read from MODAL_TOKEN_ID / MODAL_TOKEN_SECRET env vars (set as Space secrets).
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chromadb
import gradio as gr
from sentence_transformers import SentenceTransformer
from agents.autonomous_agent import AutonomousAgent

VECTOR_DB_PATH = "clinical_vector_db"

GUIDELINES = [
    "IMMEDIATE triage (see now): Cardiac arrest, ventricular fibrillation, pulseless electrical activity. Start CPR immediately. Defibrillate if shockable rhythm.",
    "IMMEDIATE triage (see now): Severe anaphylaxis — angioedema, stridor, hypotension after allergen exposure. Give IM adrenaline 0.5mg immediately.",
    "IMMEDIATE triage (see now): Acute MI with haemodynamic instability — crushing chest pain, diaphoresis, BP <90 systolic, ST elevation. Activate cath lab.",
    "IMMEDIATE triage (see now): Unresponsive patient, GCS ≤8, not protecting airway. Prepare for intubation.",
    "IMMEDIATE triage (see now): Tension pneumothorax — absent breath sounds, tracheal deviation, hypotension, distended neck veins. Needle decompression urgently.",
    "IMMEDIATE triage (see now): Status epilepticus — continuous seizure >5 minutes or recurrent without recovery. IV benzodiazepines.",
    "IMMEDIATE triage (see now): Massive haemorrhage — penetrating trauma, uncontrolled external bleeding, haemodynamic shock. Apply tourniquet/pressure.",
    "URGENT triage (within 30 minutes): High fever in infant <3 months (temp >38°C). Risk of sepsis. Full septic screen and empirical antibiotics.",
    "URGENT triage (within 30 minutes): Moderate chest pain without haemodynamic compromise. 12-lead ECG within 10 minutes. Troponin at 0 and 3 hours.",
    "URGENT triage (within 30 minutes): Acute severe asthma — unable to complete sentences, O2 sat <92%, PEFR <50% predicted. Nebulised salbutamol + oxygen.",
    "URGENT triage (within 30 minutes): Acute confusion/delirium in elderly patient. Assess for infection, metabolic cause, medication effect.",
    "URGENT triage (within 30 minutes): Suspected stroke — FAST positive (facial droop, arm weakness, speech difficulty, time). CT within 25 minutes of arrival.",
    "URGENT triage (within 30 minutes): Severe abdominal pain with peritoneal signs. NPO, IV access, surgical review.",
    "URGENT triage (within 30 minutes): Moderate dyspnoea, O2 sat 90-94%. Supplemental oxygen, identify cause.",
    "SEMI-URGENT triage (within 1 hour): Mild to moderate asthma, O2 sat >95%, able to talk in sentences. Salbutamol inhaler, reassess in 20 minutes.",
    "SEMI-URGENT triage (within 1 hour): Laceration requiring sutures, bleeding controlled, no tendon/nerve injury suspected.",
    "SEMI-URGENT triage (within 1 hour): Urinary tract infection with moderate symptoms. MSU, oral antibiotics if uncomplicated.",
    "SEMI-URGENT triage (within 1 hour): Suspected fracture with intact neurovascular status. X-ray, analgesia.",
    "SEMI-URGENT triage (within 1 hour): Moderate pain (NRS 5-7), vital signs stable. Analgesia, assess cause.",
    "NON-URGENT triage (can wait): Minor upper respiratory tract infection in otherwise well adult. Symptomatic management, no antibiotics.",
    "NON-URGENT triage (can wait): Routine medication query or prescription request. Redirect to GP if possible.",
    "NON-URGENT triage (can wait): Minor skin irritation or rash, stable vital signs, no systemic symptoms.",
    "NON-URGENT triage (can wait): Mild musculoskeletal pain, no trauma, neurovascularly intact. RICE, analgesia.",
]


def build_vector_store():
    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = embedder.encode(GUIDELINES).tolist()
    chroma = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    try:
        chroma.delete_collection("clinical_guidelines")
    except Exception:
        pass
    collection = chroma.create_collection("clinical_guidelines")
    collection.add(
        documents=GUIDELINES,
        embeddings=embeddings,
        ids=[f"guideline_{i}" for i in range(len(GUIDELINES))],
    )
    print(f"Vector store ready: {collection.count()} chunks")


print("Building vector store...")
build_vector_store()

print("Loading agents...")
agent = AutonomousAgent(VECTOR_DB_PATH)

LEVEL_STYLES = {
    "Immediate":   ("#d32f2f", "IMMEDIATE — Life-threatening. See patient NOW."),
    "Urgent":      ("#f57c00", "URGENT — See within 30 minutes."),
    "Semi-urgent": ("#f9a825", "SEMI-URGENT — See within 1 hour."),
    "Non-urgent":  ("#388e3c", "NON-URGENT — Can wait. Manage in order of arrival."),
    "Unknown":     ("#9e9e9e", "Unable to classify. Please review manually."),
}

EXAMPLES = [
    ["72yo male, sudden crushing chest pain, sweating, BP 85/50, pallor"],
    ["4yo female, fever 39.8°C for 2 days, irritable, not eating or drinking"],
    ["28yo male, laceration to right forearm from knife, bleeding now controlled"],
    ["55yo female, mild headache for 3 days, no fever, no neurological symptoms"],
    ["Infant 8 months, found unresponsive by parent, apnoeic"],
    ["35yo male, moderate shortness of breath, O2 sat 93%, audible wheeze"],
]


def triage(presentation: str):
    if not presentation.strip():
        return "Please enter a clinical presentation.", ""
    result = agent.run(presentation.strip())
    level = result["triage_level"]
    votes = result.get("votes", {})
    reasoning = result.get("reasoning", "")
    color, label = LEVEL_STYLES.get(level, LEVEL_STYLES["Unknown"])
    decision_html = f"""
    <div style="background:{color};color:white;padding:20px;border-radius:10px;font-size:20px;font-weight:bold;margin-bottom:12px">
        {label}
    </div>
    <div style="background:#f5f5f5;padding:14px;border-radius:8px;font-family:monospace;font-size:13px">
        <b>Agent votes:</b><br>
        {'<br>'.join(f'• {k}: <b>{v}</b>' for k, v in votes.items())}
    </div>
    """
    return decision_html, reasoning


with gr.Blocks(theme=gr.themes.Soft(), title="Clinical Triage System") as demo:
    gr.Markdown("""
    # Multi-Agent Clinical Triage System
    **Fine-tuned Llama (offline) + RAG over clinical guidelines + GPT-4.1-mini — orchestrated by an autonomous planning agent**

    Enter a brief clinical presentation as a triage nurse would record it.
    """)
    with gr.Row():
        inp = gr.Textbox(
            label="Clinical Presentation",
            placeholder="e.g. 65yo female, sudden onset worst headache of her life, vomiting, neck stiffness...",
            lines=3,
        )
    btn = gr.Button("Triage", variant="primary", size="lg")
    with gr.Row():
        with gr.Column(scale=2):
            decision_out = gr.HTML(label="Triage Decision")
        with gr.Column(scale=1):
            reasoning_out = gr.Textbox(label="Agent Reasoning", lines=6)
    gr.Examples(examples=EXAMPLES, inputs=inp)
    btn.click(triage, inputs=inp, outputs=[decision_out, reasoning_out])

demo.launch()
