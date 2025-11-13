from pathlib import Path
from typing import List, Optional, Union


class CodeItem:
    """
    Represents a code entity (function or class) extracted from a Python file.
    
    Attributes:
        name (str): The name of the code item.
        type (str): The type of the code item; can be 'function', 'method', or 'class'.
        source (str): The source code of the item.
        docstring (str): The documentation string of the code item.
        file_path (Union[str, Path]): The file path where the code item is located.
        imports (Optional[List[str]]): A list of imported modules or functions used by the code item.
        signature (Optional[str]): The function or class signature (e.g., 'def foo(x, y):').
        args (Optional[List[str]]): A list of argument names if the item is a function or method.
    """

    def __init__(
        self, 
        name: str, 
        type: str, 
        source: str, 
        docstring: Optional[str], 
        file_path: Union[str, Path], 
        imports: Optional[List[str]] = None,
        signature: Optional[str] = None,
        args: Optional[List[str]] = None,
    ):
        """
        Initializes a CodeItem instance with the specified attributes.
        
        Args:
          name (str): The name of the code item.
          type (str): The type of the code item; can be 'function', 'method', or 'class'.
          source (str): The source code of the item.
          docstring (Optional[str]): The documentation string of the code item.
          file_path (Union[str, Path]): The file path where the code item is located.
          imports (Optional[List[str]]): A list of imported modules or functions used by the code item.
          signature (Optional[str]): The function or class signature.
          args (Optional[List[str]]): A list of argument names if the item is a function or method.
        """
        self.name = name
        self.type = type  # "function", "method", or "class"
        self.source = source
        self.docstring = docstring
        self.file_path = Path(file_path)
        self.imports = imports or []
        self.signature = signature
        self.args = args or []

    def __repr__(self):
        """
        Returns a string representation of the CodeItem instance, displaying its attributes in a structured format.
        """
        attrs = {
            "name": self.name,
            "type": self.type,
            "signature": self.signature,
            "args": self.args,
            "file_path": str(self.file_path),
        }
        return f"CodeItem({attrs})"