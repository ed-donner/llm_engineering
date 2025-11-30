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
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the parser.
        
        Args:
            api_key: OpenAI API key (if None, loads from environment)
            model: LLM model to use
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("No API key found. Set OPENAI_API_KEY in .env file.")
    
    def parse_case(self, case_text: str, system_prompt: str) -> Dict:
        """
        Parse a case description into BN JSON structure.
        
        Args:
            case_text: Natural language case description
            system_prompt: System prompt defining output format
            
        Returns:
            Dictionary with 'bn-data' key containing BN structure
        """
        response = completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"The case is: {case_text}"}
            ],
            response_format={"type": "json_object"}
        )
        
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
