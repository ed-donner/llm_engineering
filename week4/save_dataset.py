import os
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def get_base_dir(base_dir: str = None) -> str:
    """
    Get the base directory for saving files.
    Works in both notebook and script environments.
    
    Args:
        base_dir (str, optional): Explicitly provided base directory
    
    Returns:
        str: The base directory path
    """
    if base_dir is not None:
        return base_dir
        
    try:
        # Try to get the directory of the current file (works in scripts)
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # If __file__ is not defined (in notebooks), use current working directory
        return os.getcwd()

def save_dataset(df: pd.DataFrame, base_dir: str = None) -> tuple[str, str]:
    """
    Save the dataset to CSV files with timestamp and update the latest version.
    
    Args:
        df (pd.DataFrame): The dataset to save
        base_dir (str, optional): Base directory for saving. Defaults to current directory.
    
    Returns:
        tuple[str, str]: Paths to the timestamped file and latest file
    """
    try:
        # Get the base directory
        base_dir = get_base_dir(base_dir)
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Generate timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ragnarok_items_{timestamp}.csv"
        latest_filename = "ragnarok_items_latest.csv"
        
        # Save to timestamped file
        filepath = os.path.join(data_dir, filename)
        df.to_csv(filepath, index=False)
        logger.info(f"Dataset saved to {filepath}")
        
        # Update latest version
        latest_filepath = os.path.join(data_dir, latest_filename)
        df.to_csv(latest_filepath, index=False)
        logger.info(f"Latest dataset updated at {latest_filepath}")
        
        return filepath, latest_filepath
        
    except Exception as e:
        logger.error(f"Error saving dataset: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    try:
        # Load the latest dataset if it exists
        data_dir = os.path.join(get_base_dir(), "data")
        latest_file = os.path.join(data_dir, "ragnarok_items_latest.csv")
        
        if os.path.exists(latest_file):
            df = pd.read_csv(latest_file)
            logger.info(f"Loaded existing dataset with {len(df)} items")
        else:
            logger.warning("No existing dataset found")
            
    except Exception as e:
        logger.error(f"Error in example usage: {e}") 