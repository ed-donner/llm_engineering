"""
LLM interaction module for parsing decision cases into BN structures.
"""
import json
import os
from typing import Dict, Optional
from litellm import completion
from dotenv import load_dotenv


class CaseParser:
    """Parse natural language decision cases into BN JSON structures using LLM."""
    
    def __init__(self, models: Optional[list] = None):
        """
        Initialize the parser.
        
        Args:
            models: List of model configurations to try in order
        """
        load_dotenv()
        self.models = models or []
        
        if not self.models:
            raise ValueError("No models configured. Provide models list in config.")
    
    def parse_case(self, case_text: str, system_prompt: str) -> Dict:
        """
        Parse a case description into BN JSON structure.
        Attempts models in order from the models list, falling back to the next on failure.
        
        Args:
            case_text: Natural language case description
            system_prompt: System prompt defining output format
            
        Returns:
            Dictionary with 'bn-data' key containing BN structure
            
        Raises:
            RuntimeError: If all models fail
        """
        errors = []
        
        # Try each model in order
        for i, model_config in enumerate(self.models):
            model_name = model_config.get("model_name", "unknown")
            try:
                print(f"[Model {i+1}/{len(self.models)}] Attempting with {model_name}...")
                return self._try_parse(case_text, system_prompt, model_config)
            except Exception as e:
                error_msg = f"{model_name}: {str(e)}"
                errors.append(error_msg)
                print(f"[Model {i+1}/{len(self.models)}] {model_name} failed. Attempting next model...")
        
        # All models failed
        raise RuntimeError(
            f"All {len(self.models)} models failed to parse the case.\n" +
            "\n".join([f"  • {err}" for err in errors])
        )
    
    def _try_parse(self, case_text: str, system_prompt: str, model_config: Dict) -> Dict:
        """
        Attempt to parse a case with a specific model.
        
        Args:
            case_text: Natural language case description
            system_prompt: System prompt defining output format
            model_config: Model configuration dict with model_name and litellm_params
            
        Returns:
            Dictionary with 'bn-data' key containing BN structure
        """
        model_name = model_config.get("model_name")
        litellm_params = model_config.get("litellm_params", {})
        
        # Get API key from environment variable specified in config
        env_key = litellm_params.get("env_key", "OPENAI_API_KEY")
        api_key = os.getenv(env_key)
        
        if not api_key:
            raise ValueError(f"No API key found for {model_name}. Set {env_key} in .env file.")
        
        # Build completion kwargs
        completion_kwargs = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"The case is: {case_text}"}
            ],
            "response_format": {"type": "json_object"},
            "api_key": api_key
        }
        
        # Add litellm parameters if provided (excluding env_key)
        if litellm_params:
            params_to_add = {k: v for k, v in litellm_params.items() if k != "env_key"}
            completion_kwargs.update(params_to_add)
        
        response = completion(**completion_kwargs)
        
        result = response.choices[0].message.content
        parsed = json.loads(result)
        
        # Validate basic structure
        self._validate_bn_data(parsed)
        
        return parsed
    
    def _validate_bn_data(self, data: Dict):
        """
        Validate the parsed BN data structure.
        
        Args:
            data: Parsed JSON data
            
        Raises:
            ValueError: If structure is invalid
        """
        if "bn-data" not in data:
            raise ValueError("Parsed data missing 'bn-data' key")
        
        bn_data = data["bn-data"]
        required_keys = ["variables", "edges", "cpts"]
        
        for key in required_keys:
            if key not in bn_data:
                raise ValueError(f"BN data missing required key: {key}")
        
        # Validate variables
        if not bn_data["variables"]:
            raise ValueError("No variables defined in BN")
        
        for var in bn_data["variables"]:
            if "name" not in var or "states" not in var:
                raise ValueError(f"Variable missing 'name' or 'states': {var}")
            if len(var["states"]) < 2:
                raise ValueError(f"Variable {var['name']} must have at least 2 states")
        
        # Check that all edge references exist
        var_names = {v["name"] for v in bn_data["variables"]}
        for parent, child in bn_data["edges"]:
            if parent not in var_names:
                raise ValueError(f"Edge references unknown parent: {parent}")
            if child not in var_names:
                raise ValueError(f"Edge references unknown child: {child}")
        
        # Check that all CPT variables exist
        for var_name in bn_data["cpts"]:
            if var_name not in var_names:
                raise ValueError(f"CPT defined for unknown variable: {var_name}")
