from pydantic import BaseModel
from typing import List

class DocstringOutput(BaseModel):
    """
    A model representing the output from the LLM for Python functions and classes.
    
    This model includes the name of the function or class, the suggested docstring text, and the path to the file for unique identification.
    
    Attributes:
      name (str): The name of the function or class.
      docstring (str): The suggested docstring text for the function or class.
      file_path (str): The path of the file containing the function or class.
    """
    name: str
    docstring: str
    file_path: str

class DocstringOutputList(BaseModel):
  items: List[DocstringOutput]

  