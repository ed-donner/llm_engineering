from typing import List, Dict, Any
from src.core_base.code.code_model import CodeItem
from src.core_base.agents.base_agents import BaseCodeGenerationAgent

async def generate_outputs_for_items(
    agent: BaseCodeGenerationAgent,
    items: List[CodeItem]
) -> List[Dict[str, Any]]:
    """
    Generate structured outputs (e.g., docstrings, unit tests) for a list of CodeItem objects
    using the provided BaseCodeGenerationAgent.

    Each resulting dictionary includes:
      - All generated attributes from the agent
      - Original fields of the CodeItem 'name', 'file_path', and 'source'

    Args:
        agent (BaseCodeGenerationAgent): The agent responsible for generating structured outputs.
        items (List[CodeItem]): List of CodeItem instances to process.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each containing
        the full merged data for each CodeItem.
    """

    generated = await agent.generate(items)
    results = []

    for out_item in generated:
        # Find matching generated item
        match = next((item for item in items if item.name == out_item.name), None)
        if match:
            out_item_dict = out_item.__dict__.copy()

            # Add or override key metadata
            out_item_dict["file_path"] = str(match.file_path)
            out_item_dict["source"] = match.source
            out_item_dict["original_docstring"] = match.docstring

            results.append(out_item_dict)

    return results
