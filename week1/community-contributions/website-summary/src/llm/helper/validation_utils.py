# src/llm/helper/validation_utils.py

"""
Validation utilities for LLM clients
"""

class LLMValidator:
    """Helper class for validating LLM client credentials and connections."""
    
    @staticmethod
    def validate_openai_key(api_key):
        """
        Validate OpenAI API key format.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            tuple: (is_valid, message)
        """
        if not api_key:
            return False, "No OpenAI API key was found - please add OPENAI_API_KEY to your .env file"
        elif not api_key.startswith("sk-"):
            return False, "An OpenAI API key was found, but it doesn't start with sk-; please check you're using the right key"
        elif api_key.strip() != api_key:
            return False, "An OpenAI API key was found, but it looks like it might have space or tab characters at the start or end"
        return True, "OpenAI API key found and looks good so far!"
    
    @staticmethod
    def validate_ollama_models(models_data, target_model):
        """
        Validate Ollama models response contains the target model.
        
        Args:
            models_data: The response from ollama.list()
            target_model: The model name we're looking for (or prefix)
            
        Returns:
            tuple: (found_model, is_valid, message)
        """
        model_found = False
        found_model = target_model
        
        # Handle the various response formats from ollama
        if hasattr(models_data, 'models'):
            # For newer versions of ollama client that return objects
            for model in models_data.models:
                if hasattr(model, 'model') and target_model.split(':')[0] in model.model:
                    found_model = model.model  # Use the actual name
                    model_found = True
                    break
        elif isinstance(models_data, dict) and 'models' in models_data:
            # For older versions that return dictionaries
            for model in models_data.get('models', []):
                if 'name' in model and target_model.split(':')[0] in model['name']:
                    found_model = model['name']  # Use the actual name
                    model_found = True
                    break
        
        if model_found:
            return found_model, True, f"Found model {found_model}"
        else:
            return target_model, False, f"No matching model found for {target_model}"