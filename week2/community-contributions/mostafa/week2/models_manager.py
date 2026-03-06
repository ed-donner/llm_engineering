import os
from dotenv import load_dotenv
from openai import OpenAI


OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
default_remote_models = ['gpt-4o-mini', 'gpt-5-nano', 'gpt-4.1-mini']


class ModelsManager:
    def __init__(self, system_prompt = 'You are a helpful assistant.', remote_models: list[str] = default_remote_models):
        self.local_client = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
        self.system_prompt = system_prompt

        load_dotenv(override=True)
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key and self.api_key.startswith('sk-'):
            self.remote_client = OpenAI(api_key=self.api_key)
        else:
            print(
                'Warning: OPENAI_API_KEY is not set or invalid. Remote models will not be available.')
            self.remote_client = None

        self.remote_models = [{'name': model.lower(), 'type': 'remote'}
                              for model in remote_models]

    def get_models(self):
        local_models = self._get_local_models()
        models_dict = {i+1: model for i,
                       model in enumerate(self.remote_models + local_models)}
        return models_dict

    def stream_model_response(self, prompt, model):

        if model.get('type') == 'remote':
            client: OpenAI = self.remote_client
        else:
            client: OpenAI = self.local_client

        try:
            print(f'Streaming response from model: {model['name']}')
            response = client.chat.completions.create(
                model=model['name'],
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                stream=True
            )
            result = ''
            for chunk in response:
                result += chunk.choices[0].delta.content or ''
                yield result
        except Exception as e:
            print(f'Error streaming model response: {e}')
            yield ''


    def stream_chat_response(self, messages: list[dict], model: dict):
          """Stream response using full conversation history (for chat with context)."""
          if model.get('type') == 'remote':
              client: OpenAI = self.remote_client
          else:
              client: OpenAI = self.local_client

          try:
              print(f'Streaming response from model: {model["name"]}')
              full_messages = [
                  {'role': 'system', 'content': self.system_prompt},
                  *messages
              ]
              response = client.chat.completions.create(
                  model=model['name'],
                  messages=full_messages,
                  stream=True
              )
              result = ''
              for chunk in response:
                  result += chunk.choices[0].delta.content or ''
                  yield result
          except Exception as e:
              print(f'Error streaming model response: {e}')
              yield ''


    def _get_local_models(self):
        try:
            response = self.local_client.models.list()
            return [{'name': model.id, 'type': 'local'} for model in response.data]
        except Exception as e:
            print(f'Error listing models: {e}')
            return []