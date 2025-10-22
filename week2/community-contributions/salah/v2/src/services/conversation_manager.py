from models.message import Message

class ConversationManager:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.messages = []
        
    def add_user_message(self, content):
        print(f"[Conversation] Adding user message: {content[:100]}...")
        print(f"[Conversation] Message length: {len(content)} chars")
        self.messages.append(Message("user", content))
        print(f"[Conversation] Total messages: {len(self.messages)}")
        
    def add_assistant_message(self, content):
        print(f"[Conversation] Adding assistant message: {content[:100]}...")
        print(f"[Conversation] Message length: {len(content)} chars")
        self.messages.append(Message("assistant", content))
        print(f"[Conversation] Total messages: {len(self.messages)}")
        
    def get_api_messages(self):
        # Convert to format expected by APIs
        api_messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.messages:
            api_messages.append({"role": msg.role, "content": msg.content})
        
        # Calculate total context size
        total_chars = sum(len(msg["content"]) for msg in api_messages)
        estimated_tokens = total_chars // 4  # Rough estimate
        
        print(f"[Conversation] API messages prepared:")
        print(f"  - Total messages: {len(api_messages)} (including system)")
        print(f"  - Total characters: {total_chars}")
        print(f"  - Estimated tokens: {estimated_tokens}")
        
        return api_messages