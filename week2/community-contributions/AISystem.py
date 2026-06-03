
from enum import Enum, auto
from openai import OpenAI
import anthropic

def formatPrompt(role, content):
    return {"role": role, "content": content}
    
class AI(Enum):
    OPEN_AI = "OPEN_AI"
    CLAUDE = "CLAUDE"
    GEMINI = "GEMINI"
    OLLAMA = "OLLAMA"
    
class AISystem:
    def __init__(self, processor, system_string="", model="", type=AI.OPEN_AI):
        """
        Initialize the ChatSystem with a system string and empty messages list.
        
        :param system_string: Optional initial system string description
        """
        self.processor = processor
        self.system = system_string
        self.model = model
        self.messages = []
        self.type = type
        
    def call(self, message):
        self.messages.append(message)
        toSend = self.messages
      
        if self.type == AI.CLAUDE:
            message = self.processor.messages.create(
                model=self.model,
                system=self.system,
                messages=self.messages,
                max_tokens=500
            )
            return message.content[0].text
        else:
            toSend.insert(0,self.system)
            completion = self.processor.chat.completions.create(
                model=self.model,
                messages= toSend
            )
            return completion.choices[0].message.content

    def stream(self, message, usingGradio=False):
        self.messages.append(message)
      
        if self.type == AI.CLAUDE:
            result  = self.processor.messages.stream(
                        model=self.model,
                        system=self.system,
                        messages=self.messages,
                        temperature=0.7,
                        max_tokens=500
                        )
            response_chunks = ""
            with result as stream:
                for text in stream.text_stream:
                    if usingGradio:
                        response_chunks += text or ""
                        yield response_chunks
                    else: 
                        yield text
        else:
            toSend = self.messages
            toSend.insert(0,self.system)
            stream = self.processor.chat.completions.create(
                model=self.model,
                messages= toSend,
                stream=True
            )
            response_chunks = ""
            for chunk in stream:
                if usingGradio:
                    response_chunks += chunk.choices[0].delta.content or "" # need to yield the total cumulative results to gradio and not chunk by chunk
                    yield response_chunks
                else:
                    yield chunk.choices[0].delta.content
