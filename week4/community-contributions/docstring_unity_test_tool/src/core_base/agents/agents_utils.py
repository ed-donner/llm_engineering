
from typing import Type

def _parse_to_models(OutPutModel: Type, parsed):
    """
    Convert JSON-like data into a list of Pydantic model instances.
    
    This function takes a Pydantic model type and parsed data, and converts the parsed data into instances of the specified model. It attempts to infer the model's item type from its field annotations. If the inference fails or if the parsed data does not match expected formats, it returns an empty list.
    
    Args:
        OutPutModel (Type): The Pydantic model type to instantiate from the parsed data.
        parsed: The JSON-like data to convert, which can be a list or a dictionary containing an 'items' key.
    
    Returns:
        List: A list of instantiated model objects, or an empty list if conversion is not possible.
    """
    try:
        item_type = OutPutModel.model_fields["items"].annotation.__args__[0]
    except Exception:
        print("[WARNING] Could not infer item type from OutputModel, returning empty list")
        return []

    if isinstance(parsed, list):
        return [item_type(**d) for d in parsed if isinstance(d, dict)]
    if isinstance(parsed, dict) and "items" in parsed:
        return [item_type(**d) for d in parsed["items"] if isinstance(d, dict)]
    return []