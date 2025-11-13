from pathlib import Path
from typing import List, Optional, Type
from src.core_base.agents.base_agents import BaseCodeGenerationAgent
from src.core_base.indexer.project_indexer import ProjectIndexer
from src.core_base.generate.generate_utils import generate_outputs_for_items
from src.core_base.code.code_extractor import get_filtered_code_items
import os

class BaseGenerationManager:
    """
    Manager for generating structured code outputs using a specific code generation agent.
    
    This class supports generation per file to control token usage in large projects, ensuring efficient processing of multiple code items.
    
    Attributes:
      agent_class (Type[BaseCodeGenerationAgent]): The class of the agent used for code generation.
    """

    agent_class: Type[BaseCodeGenerationAgent]

    def __init__(self, model_name: str = "gpt-4o-mini", project_path: Optional[Path] = None):
        """
        Initialize the BaseGenerationManager with a specified model name and project path.
        
        Args:
          model_name (str): The name of the model to use for code generation, default is 'gpt-4o-mini'.
          project_path (Optional[Path]): The path to the project for which code items will be indexed.
        """
        self.project_path = project_path
        self.indexer = None

        # Initialize project indexer if path provided
        if project_path:
            self.indexer = ProjectIndexer(project_path)
            self.indexer.load_or_build()

        # Initialize agent
        self.agent = self.agent_class(model_name=model_name, project_path=project_path)

    async def generate_for_file(
        self,
        file_path: str,
        target_names: Optional[List[str]] = None
    ) -> List[dict]:
        """
        Generate structured outputs for all CodeItems in a specified Python file.
        
        Args:
          file_path (str): The path to the Python file to process.
          target_names (Optional[List[str]]): List of function/class names to filter outputs.
        
        Returns:
          List[dict]: A list of dictionaries containing the generated outputs, one for each CodeItem.
        """
        path_obj = Path(file_path).resolve()
        if not path_obj.exists():
            print(f"[WARN] File not found: {path_obj}")
            return []

        items = get_filtered_code_items(path_obj, target_names)
        if not items:
            print(f"[INFO] No code items found in {file_path}")
            return []

        results = await generate_outputs_for_items(self.agent, items)
        return results

    async def generate_for_path(
        self,
        path: str,
        target_names: Optional[List[str]] = None
    ) -> List[dict]:
        """
        Generate structured outputs for all Python files under the specified folder path.
        
        This method iterates through each file to control token usage during the generation process.
        
        Args:
          path (str): The path to the folder containing Python files.
          target_names (Optional[List[str]]): List of function/class names to filter outputs.
        
        Returns:
          List[dict]: A list of dictionaries containing generated outputs from all processed files.
        """
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            print(f"[WARN] Path not found: {path_obj}")
            return []

        all_results: List[dict] = []

        if path_obj.is_file() and path_obj.suffix == ".py":
            # Single file
            results = await self.generate_for_file(str(path_obj), target_names)
            all_results.extend(results)
        else:
            # Folder: iterate over all .py files
            for root, _, files in os.walk(path_obj):
                for f in files:
                    if f.endswith(".py"):
                        file_path = os.path.join(root, f)
                        results = await self.generate_for_file(file_path, target_names)
                        all_results.extend(results)

        print(f"[INFO] Total items processed: {len(all_results)}")
        return all_results