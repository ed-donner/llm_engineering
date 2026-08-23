from config.settings import Config
from services.openrouter_client import OpenRouterClient
from services.gemini_audio_service import GeminiAudioService
from services.conversation_manager import ConversationManager
from ui.gradio_interface import AssistantUI

def main():
    print("Starting AI Assistant...")
    
    # Load config
    config = Config()
    config.validate()
    
    # Setup services
    ai_client = OpenRouterClient(config.openrouter_key, config.text_model)
    audio_service = GeminiAudioService(
        config.gemini_key, 
        config.stt_model,
        config.tts_model,
        config.voice_name
    )
    conversation = ConversationManager(config.system_prompt)
    
    # Create UI
    ui = AssistantUI(ai_client, audio_service, conversation)
    app = ui.create_interface()
    
    print(f"Launching on port {config.port}...")
    app.launch(server_port=config.port)

if __name__ == "__main__":
    main()