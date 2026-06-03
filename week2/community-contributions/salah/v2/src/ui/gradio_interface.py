import gradio as gr

class AssistantUI:
    def __init__(self, ai_client, audio_service, conversation_manager):
        self.ai_client = ai_client
        self.audio_service = audio_service
        self.conversation = conversation_manager
        self.display_history = []
        
    def handle_text_message(self, message):
        if not message.strip():
            return self.display_history, ""
            
        # Add user message
        self.conversation.add_user_message(message)
        self.display_history.append({"role": "user", "content": message})
        
        # Get AI response
        api_messages = self.conversation.get_api_messages()
        response = self.ai_client.chat(api_messages)
        
        # Check if response is an error
        is_error = response.startswith("Error:")
        
        if is_error:
            print(f"AI Client Error: {response}")
            # Show error in chat but don't add to conversation history
            self.display_history.append({"role": "assistant", "content": response})
            return self.display_history, ""
        
        # Add successful response to conversation
        self.conversation.add_assistant_message(response)
        self.display_history.append({"role": "assistant", "content": response})
        
        return self.display_history, ""
    
    def handle_voice_message(self, audio_file):
        if not audio_file:
            return self.display_history, None
            
        # Transcribe audio
        text = self.audio_service.speech_to_text(audio_file)
        if not text:
            return self.display_history, None
            
        # Add transcribed message to display
        self.display_history.append({
            "role": "user", 
            "content": {"path": audio_file, "alt_text": f"Voice: {text}"}
        })
        
        # Process as text message
        self.conversation.add_user_message(text)
        api_messages = self.conversation.get_api_messages()
        response = self.ai_client.chat(api_messages)
        
        # Check if response is an error
        is_error = response.startswith("Error:")
        
        if is_error:
            print(f"AI Client Error: {response}")
            # Show error in chat but don't convert to speech
            self.display_history.append({"role": "assistant", "content": response})
            return self.display_history, None
        
        self.conversation.add_assistant_message(response)
        
        # Generate audio response only for successful responses
        audio_response = self.audio_service.text_to_speech(response)
        
        if audio_response:
            self.display_history.append({
                "role": "assistant",
                "content": {"path": audio_response, "alt_text": response[:100] + "..."}
            })
        else:
            self.display_history.append({"role": "assistant", "content": response})
            
        return self.display_history, None
    
    def analyze_code(self, code, language):
        if not code.strip():
            return self.display_history
            
        result = self.ai_client.analyze_code(code, language)
        
        # Check for errors
        is_error = result.startswith("Error:")
        
        if is_error:
            print(f"Code Analysis Error: {result}")
            self.display_history.append({"role": "user", "content": f"Code analysis ({language})"})
            self.display_history.append({"role": "assistant", "content": result})
            return self.display_history
        
        # Add to conversation only if successful
        self.conversation.add_user_message(f"Analyze {language} code")
        self.conversation.add_assistant_message(result)
        
        # Add to display
        self.display_history.append({"role": "user", "content": f"Code analysis ({language})"})
        self.display_history.append({"role": "assistant", "content": result})
        
        return self.display_history
    
    def generate_linkedin_post(self, topic, tone):
        if not topic.strip():
            return self.display_history
            
        result = self.ai_client.generate_linkedin_post(topic, tone)
        
        # Check for errors
        is_error = result.startswith("Error:")
        
        if is_error:
            print(f"LinkedIn Post Generation Error: {result}")
            self.display_history.append({"role": "user", "content": f"LinkedIn post ({tone}): {topic}"})
            self.display_history.append({"role": "assistant", "content": result})
            return self.display_history
        
        # Add to conversation only if successful
        self.conversation.add_user_message(f"Generate LinkedIn post about: {topic}")
        self.conversation.add_assistant_message(result)
        
        # Add to display
        self.display_history.append({"role": "user", "content": f"LinkedIn post ({tone}): {topic}"})
        self.display_history.append({"role": "assistant", "content": result})
        
        return self.display_history
    
    def create_interface(self):
        with gr.Blocks() as app:
            gr.Markdown("# AI Assistant")
            gr.Markdown("Chat with text or voice")
            
            # Main chat
            chat = gr.Chatbot(type="messages", height=500)
            
            # Input area
            with gr.Row():
                msg = gr.Textbox(
                    label="Message", 
                    placeholder="Type or record...",
                    scale=9,
                    container=False
                )
                mic = gr.Audio(
                    sources=["microphone"],
                    type="filepath", 
                    label="Record",
                    scale=1
                )
            
            # Wire up events
            msg.submit(self.handle_text_message, msg, [chat, msg])
            mic.stop_recording(self.handle_voice_message, mic, [chat, mic])
            
            # Code analysis tool
            with gr.Accordion("Code Analysis", open=False):
                code_input = gr.Textbox(label="Code", lines=8)
                lang_select = gr.Dropdown(
                    choices=["python", "javascript", "java"],
                    value="python",
                    label="Language"
                )
                analyze_btn = gr.Button("Analyze")
                
                analyze_btn.click(
                    self.analyze_code, 
                    [code_input, lang_select], 
                    chat
                )
            
            # LinkedIn post generator
            with gr.Accordion("LinkedIn Post Generator", open=False):
                topic_input = gr.Textbox(
                    label="Topic", 
                    placeholder="What do you want to post about?",
                    lines=2
                )
                tone_select = gr.Dropdown(
                    choices=["professional", "casual", "inspirational", "educational"],
                    value="professional",
                    label="Tone"
                )
                generate_btn = gr.Button("Generate Post")
                
                generate_btn.click(
                    self.generate_linkedin_post,
                    [topic_input, tone_select],
                    chat
                )
        
        return app