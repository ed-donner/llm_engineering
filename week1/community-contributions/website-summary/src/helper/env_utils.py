# src/helper/env_utils.py

import os
from pathlib import Path
from dotenv import load_dotenv

def find_and_load_env_file():
    """
    Find and load the .env file from the project structure.
    
    Returns:
        bool: True if a .env file was found and loaded, False otherwise
    """
    # Start with the current file's directory
    current_file = Path(os.path.abspath(__file__))
    
    # Navigate up from helper/env_utils.py:
    # helper/ -> src/ -> website-summary/
    website_summary_dir = current_file.parent.parent.parent
    
    # Check for .env in website-summary/
    project_env_path = website_summary_dir / '.env'
    
    # Check for .env in LLM_NGINEERING/ (much higher up the directory tree)
    llm_engineering_dir = website_summary_dir.parent.parent.parent
    llm_engineering_env_path = llm_engineering_dir / '.env'
    
    # List of potential locations to check for .env file
    potential_paths = [
        project_env_path,             # website-summary/.env
        llm_engineering_env_path,     # LLM_NGINEERING/.env
        Path(os.getcwd()) / '.env',   # Current working directory/.env
    ]
    
    # Search for .env in the potential paths
    for env_path in potential_paths:
        if env_path.exists():
            print(f"✅ Found .env file at: {env_path.absolute()}")
            load_dotenv(env_path, override=True)
            return True
    
    print("❌ No .env file found in any of the checked locations!")
    return False