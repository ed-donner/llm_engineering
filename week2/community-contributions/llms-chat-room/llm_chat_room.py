import random
from llm_bot import LLMBot

class LLMChatRoom:
    def __init__(self, llms, subject):
        self.subject = subject
        self.bots = [LLMBot(llm, subject) for llm in llms]
        self.messages = []

    def select_speaker(self):
        if not self.bots:
            return None
        return random.choice(self.bots)

    def next_message(self, speaker, prompt):
        if speaker:
            response = speaker.get_response(prompt)
            self.messages.append({"name": speaker.name, "content": response})

    def get_prompt(self):
        prompt = f"Talk about {self.subject}:\n"
        for message in self.messages:
            prompt += f"{message['name']}: {message['content']}\n"
        return prompt

    def get_last_message(self):
        return self.messages[-1] if self.messages else None

    def talk(self):
        speaker = self.select_speaker()
        prompt = self.get_prompt()
        self.next_message(speaker, prompt)

    def chat(self, num_turns=10):
        self.messages = []
        for _ in range(num_turns):
            self.talk()
            last_message = self.get_last_message()
            print(f"{last_message['name']}: {last_message['content']}")
            print("-"* 80)