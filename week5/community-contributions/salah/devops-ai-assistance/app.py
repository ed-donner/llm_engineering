import os
import gradio as gr
from devops_ai_assistance import create_assistant, DevOpsAIAssistant


assistant = None
status_info = None


def initialize_assistant(kb_path: str):
    """Initialize the assistant with knowledge base"""
    global assistant, status_info

    try:
        kb_path = kb_path.strip()
        if not kb_path:
            return "Error: Please provide a valid knowledge base path"

        print(f"\n🚀 Initializing with knowledge base: {kb_path}")
        assistant = create_assistant(kb_path)
        status_info = assistant.get_status()

        status_message = f"""
✅ **DevOps AI Assistant Initialized Successfully!**

📊 **Knowledge Base Statistics:**
- Documents Loaded: {status_info['documents_loaded']}
- Chunks Created: {status_info['chunks_created']}
- Vectors in Store: {status_info['vectors_in_store']}
- Knowledge Base Path: {status_info['knowledge_base_path']}

🎯 **Ready to Answer Questions About:**
- Kubernetes infrastructure configuration
- ArgoCD deployment manifests
- Helm charts and values
- Infrastructure as Code (IaC)
- DevOps best practices in your environment

Start by asking questions about your k8s cluster infrastructure!
"""
        return status_message

    except Exception as e:
        error_msg = f"Error initializing assistant: {str(e)}"
        print(f"❌ {error_msg}")
        return f"❌ {error_msg}"


def chat_with_assistant(message: str, history):
    """Chat function for the assistant"""
    global assistant

    if not assistant:
        bot_response = "❌ Assistant not initialized. Please provide a knowledge base path first."
        history.append((message, bot_response))
        return history, ""

    if not message.strip():
        bot_response = "Please enter a question about your DevOps infrastructure."
        history.append((message, bot_response))
        return history, ""

    try:
        result = assistant.ask(message)
        answer = result.get('answer', '')

        sources_text = ""
        if result.get('sources'):
            sources_text = "\n\n📚 **Sources:**\n"
            for i, source in enumerate(result['sources'], 1):
                source_file = source.get('source', 'Unknown')
                file_type = source.get('file_type', 'Unknown')
                sources_text += f"\n{i}. **{source_file}** ({file_type})"

        bot_response = answer + sources_text if sources_text else answer

    except Exception as e:
        bot_response = f"Error processing question: {str(e)}"

    history.append((message, bot_response))
    return history, ""


def create_interface():
    """Create the Gradio interface"""
    global assistant

    with gr.Blocks(title="DevOps AI Assistant") as interface:

        gr.Markdown("# 🤖 DevOps AI Assistant")
        gr.Markdown("Intelligent Q&A system for your Kubernetes infrastructure powered by RAG and LLM")

        gr.Markdown("## 🔧 Configuration")
        gr.Markdown("Enter the path to your GitOps repository (knowledge base) to initialize the assistant")

        with gr.Row():
            kb_path_input = gr.Textbox(
                label="Knowledge Base Path",
                placeholder="/workspace/aau/repositories/infra-gitops/",
                lines=1,
                value="/workspace/aau/repositories/infra-gitops/"
            )
            init_button = gr.Button("🚀 Initialize Assistant")

        status_output = gr.Markdown(value="⏳ Waiting for initialization...")

        gr.Markdown("## 💬 Chat Interface")

        chatbot = gr.Chatbot(
            label="Conversation",
            height=500,
            show_copy_button=True,
            avatar_images=("👤", "🤖"),
            bubble_full_width=False
        )

        with gr.Row():
            msg_input = gr.Textbox(
                label="Your Question",
                placeholder="Ask about your k8s infrastructure, ArgoCD, Helm charts, etc...",
                lines=2,
                scale=5
            )
            send_button = gr.Button("Send 💬", scale=1)

        with gr.Row():
            clear_button = gr.Button("🗑️ Clear Chat", scale=2)

        with gr.Accordion("📋 Example Questions", open=False):
            gr.Markdown("""
**Infrastructure & Deployment:**
- How is the Kubernetes cluster configured?
- What ArgoCD applications are deployed?
- Show me the Helm chart values for nginx
- What storage solutions are available?

**Monitoring & Observability:**
- How is Prometheus configured?
- What monitoring exporters are installed?
- Tell me about the metrics server setup

**Security & Access:**
- How are RBAC policies configured?
- What authentication methods are used?
- Explain the network policies

**DevOps Practices:**
- What is the deployment pipeline?
- How are secrets managed?
- Show me the backup strategy
            """)

        init_button.click(
            initialize_assistant,
            inputs=[kb_path_input],
            outputs=[status_output]
        )

        msg_input.submit(
            chat_with_assistant,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )

        send_button.click(
            chat_with_assistant,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )

        clear_button.click(lambda: [], outputs=chatbot)

    return interface


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("🚀 DevOps AI Assistant - RAG System")
    print("=" * 60)
    print("Starting Gradio server...")
    print("\nAccess the application at: http://127.0.0.1:7860")
    print("=" * 60 + "\n")

    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        show_api=False
    )


if __name__ == "__main__":
    main()
