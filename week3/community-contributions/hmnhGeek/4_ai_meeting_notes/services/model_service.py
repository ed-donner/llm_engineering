from services.environment_service import EnvironmentService
from services.prompt_service import PromptService
from services.speech_to_text_service import SpeechToTextService


class ModelService:
    def __init__(self, audio_file_path):
        self.environment = EnvironmentService()
        self.client = self.environment.get_client()
        self.model = self.environment.get_model()
        self.speech_to_text_service = SpeechToTextService()
        self.transcript = self.speech_to_text_service.transcribe(
            audio_file_path)
        self.system_prompt = PromptService.get_system_prompt(self.transcript)

    def chat(self, message, history):
        messages = [{"role": "system", "content": PromptService.get_system_prompt(
            self.transcript)}] + history + [{"role": "user", "content": message}]
        stream = self.client.chat.completions.create(
            model=self.model, messages=messages, stream=True)
        response = ""
        for chunk in stream:
            response += chunk.choices[0].delta.content or ''
            yield response

    def summarize(self):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Please summarize the following transcript: {self.transcript}"}
        ]
        stream = self.client.chat.completions.create(
            model=self.model, messages=messages, stream=True)
        response = ""
        for chunk in stream:
            response += chunk.choices[0].delta.content or ''
            yield response
