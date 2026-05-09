"""
Simple Multi-Agent Medical Assistant UI
3 Agents: Clinical, Drug Info, Interaction
"""

import os
import gradio as gr
from pathlib import Path
from dotenv import load_dotenv

from answer import vectorstore, llm, MultiAgentMedicalAssistant

# Load environment
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Initialize assistant
assistant = MultiAgentMedicalAssistant(vectorstore, llm, api_key)

# Agent colors and emojis
AGENT_COLORS = {
    "clinical": "#4ecdc4",
    "drug_info": "#45b7d1",
    "interaction": "#dc3545"
}

AGENT_EMOJIS = {
    "clinical": "🏥",
    "drug_info": "💊",
    "interaction": "⚠️"
}


def format_drug_card(drug_info):
    """Format drug information card"""
    return f"""
<div style='background: #f8f9fa; border: 2px solid #4ecdc4; padding: 15px; border-radius: 10px; margin: 10px 0;'>
    <div style='display: flex; gap: 20px; flex-wrap: wrap;'>
        <img src='{drug_info["image_url"]}' style='width: 120px; height: 120px; object-fit: contain; border-radius: 8px;' />
        <div style='flex: 1; min-width: 250px;'>
            <h3 style='margin-top: 0; color: #4ecdc4;'>{drug_info["medicine_name"]}</h3>
            <p><strong>Composition:</strong> {drug_info["composition"][:150]}...</p>
            <p><strong>Uses:</strong> {drug_info["uses"][:200]}...</p>
            <p><strong>Side Effects:</strong> {drug_info["side_effects"][:200]}...</p>
            <div style='margin-top: 8px;'>
                <span style='background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 3px; font-size: 12px;'>
                    Excellent: {drug_info["reviews"]["excellent"]}%
                </span>
                <span style='background: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; margin-right: 3px; font-size: 12px;'>
                    Average: {drug_info["reviews"]["average"]}%
                </span>
                <span style='background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px;'>
                    Poor: {drug_info["reviews"]["poor"]}%
                </span>
            </div>
        </div>
    </div>
</div>
"""


def format_interaction_warning(interaction_result):
    """Format drug interaction warnings"""
    if not interaction_result.get("has_interactions", False):
        return ""

    warning = """<div style='background: #fff3cd; border: 2px solid #dc3545; padding: 15px; border-radius: 10px; margin: 10px 0;'>
<h4 style='color: #dc3545; margin-top: 0;'>⚠️ DRUG INTERACTION DETECTED</h4>
"""

    for interaction in interaction_result["interactions"]:
        warning += f"""
<div style='background: white; padding: 10px; border-radius: 5px; margin: 10px 0;'>
    <p><strong>Drugs:</strong> {interaction['drug1']} ↔ {interaction['drug2']}</p>
    <p><strong>Description:</strong> {interaction['description']}</p>
    <div style='background: #f8d7da; padding: 10px; border-radius: 5px; margin-top: 8px;'>
        {interaction['analysis']}
    </div>
</div>
"""

    warning += """
<p style='font-weight: bold; color: #dc3545; margin-top: 10px;'>
⚠️ IMPORTANT: Consult your healthcare provider before taking these medications together.
</p>
</div>
"""
    return warning


def format_context(sources, agent_type):
    """Format retrieved context"""
    color = AGENT_COLORS.get(agent_type, "#95a5a6")
    emoji = AGENT_EMOJIS.get(agent_type, "🏥")

    agent_names = {
        "clinical": "Clinical Knowledge",
        "drug_info": "Drug Information",
        "interaction": "Drug Interaction"
    }
    agent_name = agent_names.get(agent_type, "Medical")

    result = f"""<div style="background: {color}20; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
<h3 style="color: {color}; margin: 0;">{emoji} {agent_name} Agent</h3>
</div>

<h4 style='color: #1f77b4;'>Retrieved Documents</h4>
"""

    for i, doc in enumerate(sources[:3], 1):  # Limit to 3 docs for display
        source = doc.metadata.get("source", "Unknown")
        content = doc.page_content[:300]  # Limit display

        result += f"""<div style="background: #f8f9fa; padding: 10px; border-left: 3px solid {color}; margin-bottom: 10px; border-radius: 5px;">
<p style="margin: 0; font-size: 11px; color: #666;"><b>Document {i}</b> | Source: {source}</p>
<p style="margin: 5px 0 0 0; font-size: 13px;">{content}...</p>
</div>
"""

    return result


def chat(history):
    """Handle chat with multi-agent system"""
    last_message = history[-1]["content"]
    prior_history = history[:-1]

    try:
        # Call multi-agent system
        result = assistant.answer(last_message, prior_history)

        answer = result.get("answer", "")
        agent_type = result.get("agent_type", "clinical")
        sources = result.get("sources", [])
        drug_info = result.get("drug_info", {})
        interactions = result.get("interactions", {})

        # Build response components
        emoji = AGENT_EMOJIS.get(agent_type, "🏥")
        color = AGENT_COLORS.get(agent_type, "#95a5a6")

        agent_names = {
            "clinical": "Clinical Knowledge",
            "drug_info": "Drug Information",
            "interaction": "Drug Interaction"
        }
        agent_name = agent_names.get(agent_type, "Medical")

        # Agent badge
        agent_badge = f"""<div style="display: inline-block; background: {color}; color: white; padding: 6px 12px; border-radius: 12px; font-size: 13px; margin-bottom: 8px; font-weight: 500;">
{emoji} {agent_name}
</div>

"""

        # Build drug cards if found
        drug_cards = ""
        if drug_info.get("found_drugs", False):
            for drug in drug_info["drugs"]:
                drug_cards += format_drug_card(drug)

        # Build interaction warnings if found
        interaction_warnings = format_interaction_warning(interactions)

        # Combine all
        formatted_answer = agent_badge + drug_cards + interaction_warnings + answer

    except Exception as e:
        formatted_answer = f"<b>Error:</b> {str(e)}"
        sources = []
        agent_type = "clinical"

    # Add to history
    history.append({"role": "assistant", "content": formatted_answer})

    # Format context
    context_html = format_context(sources, agent_type)

    return history, context_html


def main():

    def put_message_in_chatbot(message, history):
        """Add user message to chat"""
        return "", history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Medical Assistant", theme=theme) as ui:

        gr.Markdown(
            """# 🏥 Multi-Agent Medical Assistant

Ask medical questions and get answers from specialized agents:
- 🏥 **Clinical Knowledge** - General medical information, diseases, symptoms
- 💊 **Drug Information** - Medication details, uses, side effects
- ⚠️ **Drug Interactions** - Safety checks for multiple medications

Your question is automatically routed to the right agent!
            """
        )

        with gr.Row():

            with gr.Column(scale=1):

                chatbot = gr.Chatbot(
                    label="Medical Assistant Chat",
                    height=600,
                    type="messages",
                    show_copy_button=True,
                )

                message = gr.Textbox(
                    placeholder="Ask a medical question (e.g., 'What causes diabetes?' or 'What is Augmentin used for?')",
                    show_label=False,
                )

                gr.Markdown(
                    """
**Example questions:**
- What are symptoms of heart failure? (Clinical)
- What is Azithral 500 used for? (Drug Info)
- Can I take aspirin with warfarin? (Interaction Check)
                    """,
                    elem_classes="examples"
                )

            with gr.Column(scale=1):

                context_markdown = gr.HTML(
                    value="<p style='color: #666; text-align: center; padding: 50px;'>Retrieved context will appear here.</p>",
                )

        # Connect events
        message.submit(
            put_message_in_chatbot,
            inputs=[message, chatbot],
            outputs=[message, chatbot],
        ).then(
            chat,
            inputs=chatbot,
            outputs=[chatbot, context_markdown]
        )

        gr.Markdown(
            """
---
**⚠️ Medical Disclaimer:** This is an AI assistant for educational purposes only.
Always consult qualified healthcare professionals for medical advice, diagnosis, or treatment.
            """,
            elem_classes="disclaimer"
        )

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
