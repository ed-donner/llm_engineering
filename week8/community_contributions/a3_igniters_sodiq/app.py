import gradio as gr
from agents import router_agent, billing_agent, technical_agent, knowledge_agent


def support_chat(message, history):
    openai_history = []
    for user_msg, assistant_msg in history:
        openai_history.append({"role": "user", "content": user_msg})
        if assistant_msg:
            openai_history.append({"role": "assistant", "content": assistant_msg})

    agent_name = router_agent(message, history=openai_history)
    print(f"Router Agent selected: {agent_name}")

    agent_map = {
        "billing_agent": billing_agent,
        "technical_agent": technical_agent,
        "knowledge_agent": knowledge_agent,
    }

    agent_function = agent_map.get(agent_name, knowledge_agent)
    response = agent_function(message, history=openai_history)

    return str(response)


with gr.Blocks() as demo:

    gr.Markdown("# Multi-Agent Customer Support System")

    gr.Markdown(
        "Router Agent directs questions to Billing, Technical, or Knowledge agents."
    )

    gr.ChatInterface(
        fn=support_chat,
        title="AI Support Assistant"
    )

demo.launch()