# data_generator_lib.py
"""
Library module for AI-powered synthetic data generation.
Provides robust JSON extraction, error handling, and retry logic.
"""
import json
import re
import time
import pandas as pd
from typing import Optional, Union, Dict, Any


def extract_json_from_text(text: str) -> Optional[Union[Dict, list]]:
    """
    Extract JSON from text that might contain markdown or explanations.
    
    Attempts multiple strategies:
    1. Find JSON between triple backticks (```json ... ```)
    2. Find JSON between curly braces {...}
    3. Try parsing the entire text as JSON
    
    Args:
        text: Raw text response from AI model
        
    Returns:
        Parsed JSON object or None if extraction fails
    """
    if not text or not isinstance(text, str):
        return None
        
    # Strategy 1: Find JSON between triple backticks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Strategy 2: Find JSON array between square brackets
    array_match = re.search(r'(\[[\s\S]*\])', text)
    if array_match:
        try:
            return json.loads(array_match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Strategy 3: Find JSON object between curly braces
    brace_match = re.search(r'(\{[\s\S]*\})', text)
    if brace_match:
        try:
            return json.loads(brace_match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Strategy 4: Try parsing the whole text
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def clean_response_text(text: str) -> str:
    """
    Remove markdown code blocks and clean up the text.
    
    Args:
        text: Raw text response from AI model
        
    Returns:
        Cleaned text with markdown formatting removed
    """
    if not text:
        return ""
    
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = re.sub(r'`{3,}', '', text)  # Remove any remaining backticks
    
    # Remove leading/trailing whitespace
    return text.strip()


def validate_dataframe_structure(df: pd.DataFrame, expected_fields: list = None) -> bool:
    """
    Validate that the DataFrame has the expected structure.
    
    Args:
        df: DataFrame to validate
        expected_fields: List of expected column names (optional)
        
    Returns:
        True if valid, False otherwise
    """
    if df is None or df.empty:
        return False
    
    if expected_fields and not all(field in df.columns for field in expected_fields):
        missing = [f for f in expected_fields if f not in df.columns]
        print(f"Warning: Missing expected fields: {missing}")
        return False
    
    return True


def generate_data(
    client, 
    MODELS: Dict[str, str], 
    build_prompt_func, 
    model_name: str, 
    dataset_type: str, 
    size: int, 
    max_retries: int = 3,
    temperature: float = 0.4,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Generate synthetic data using AI model with robust error handling.
    
    Parameters:
    - client: OpenAI-compatible client instance
    - MODELS: Dictionary mapping model names to model IDs
    - build_prompt_func: Function that builds prompts (takes dataset_type, size)
    - model_name: Key for MODELS dict
    - dataset_type: Type of dataset to generate
    - size: Number of rows to generate
    - max_retries: Maximum retry attempts
    - temperature: Model temperature (0.0-1.0)
    - verbose: Print debug information
    
    Returns:
    - DataFrame with generated data or error information
    """
    # Validate inputs
    if model_name not in MODELS:
        error_msg = f"Model '{model_name}' not found. Available: {list(MODELS.keys())}"
        print(f"Error: {error_msg}")
        return pd.DataFrame({'error': [error_msg]})
    
    prompt = build_prompt_func(dataset_type, size)
    
    for attempt in range(max_retries):
        try:
            if verbose:
                print(f"Attempt {attempt + 1}/{max_retries} for {dataset_type} ({size} records)")
            
            response = client.chat.completions.create(
                model=MODELS[model_name],
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            
            # Extract and clean response
            raw_text = response.choices[0].message.content
            if not raw_text:
                raise ValueError("Empty response from model")
            
            text = raw_text.strip()
            if verbose:
                print(f"Raw response preview: {text[:200]}...")
            
            # Clean the response
            cleaned_text = clean_response_text(text)
            
            # Try parsing as JSON directly
            try:
                data = json.loads(cleaned_text)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict):
                    # If it's a dict with a data key, try that
                    if 'data' in data and isinstance(data['data'], list):
                        return pd.DataFrame(data['data'])
                    elif 'records' in data and isinstance(data['records'], list):
                        return pd.DataFrame(data['records'])
                    else:
                        # Wrap single object in list
                        return pd.DataFrame([data])
                else:
                    raise json.JSONDecodeError("Unexpected data type", str(data), 0)
                    
            except (json.JSONDecodeError, TypeError) as json_err:
                if verbose:
                    print(f"JSON decode failed: {json_err}")
                
                # Try to extract JSON from text
                extracted = extract_json_from_text(text)
                if extracted:
                    if isinstance(extracted, list):
                        return pd.DataFrame(extracted)
                    elif isinstance(extracted, dict):
                        return pd.DataFrame([extracted])
                
                # If we can't extract JSON, raise to trigger retry
                if attempt == max_retries - 1:
                    raise json.JSONDecodeError(f"Could not extract valid JSON after {max_retries} attempts", text[:100], 0)
                continue
                    
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:200]  # Truncate long error messages
            print(f"Attempt {attempt + 1} failed: {error_type} - {error_msg}")
            
            if attempt < max_retries - 1:
                # Exponential backoff
                sleep_time = 2 ** attempt
                if verbose:
                    print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                # Return error DataFrame on final failure
                return pd.DataFrame({
                    'error': [f"Failed after {max_retries} attempts"],
                    'error_type': [error_type],
                    'error_details': [error_msg],
                    'dataset_type': [dataset_type],
                    'model': [model_name]
                })
    
    # Fallback (shouldn't reach here)
    return pd.DataFrame({'error': ['Unexpected error in generate_data']})


# Class-based version for better organization
class DataGenerator:
    """
    A reusable class for generating synthetic data with AI models.
    """
    
    def __init__(self, client, MODELS: Dict[str, str], build_prompt_func):
        """
        Initialize the DataGenerator.
        
        Args:
            client: OpenAI-compatible client
            MODELS: Dictionary of model name -> model ID
            build_prompt_func: Function to build prompts
        """
        self.client = client
        self.MODELS = MODELS
        self.build_prompt = build_prompt_func
        
    def extract_json(self, text: str) -> Optional[Union[Dict, list]]:
        """Extract JSON from text (wrapper for extract_json_from_text)"""
        return extract_json_from_text(text)
    
    def clean_text(self, text: str) -> str:
        """Clean response text (wrapper for clean_response_text)"""
        return clean_response_text(text)
    
    def generate(self, model_name: str, dataset_type: str, size: int, 
                 max_retries: int = 3, temperature: float = 0.4,
                 verbose: bool = False) -> pd.DataFrame:
        """
        Generate synthetic data.
        
        Args:
            model_name: Key for MODELS dict
            dataset_type: Type of dataset to generate
            size: Number of records
            max_retries: Maximum retry attempts
            temperature: Model temperature
            verbose: Print debug info
            
        Returns:
            DataFrame with generated data
        """
        return generate_data(
            self.client, self.MODELS, self.build_prompt,
            model_name, dataset_type, size, max_retries, 
            temperature, verbose
        )
    
    def generate_with_preview(self, model_name: str, dataset_type: str, 
                               size: int, **kwargs) -> tuple:
        """
        Generate data and return both DataFrame and preview info.
        
        Returns:
            Tuple of (DataFrame, preview_info_dict)
        """
        df = self.generate(model_name, dataset_type, size, **kwargs)
        
        preview = {
            'success': 'error' not in df.columns or df['error'].isna().all(),
            'shape': df.shape,
            'columns': list(df.columns),
            'sample': df.head(3).to_dict('records') if not df.empty else []
        }
        
        return df, preview