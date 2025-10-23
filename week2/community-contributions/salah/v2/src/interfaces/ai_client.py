from abc import ABC, abstractmethod

class AIClient(ABC):
    @abstractmethod
    def chat(self, messages):
        pass
    
    @abstractmethod
    def analyze_code(self, code, language):
        pass
    
    @abstractmethod
    def generate_linkedin_post(self, topic, tone="professional"):
        pass

class AudioService(ABC):
    @abstractmethod
    def speech_to_text(self, audio_file):
        pass
    
    @abstractmethod
    def text_to_speech(self, text):
        pass