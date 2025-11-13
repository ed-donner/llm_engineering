from typing import List
from pydantic import BaseModel

class UnitTestOutput(BaseModel):
    """
    A model representing the output from the LLM for generating pytest unit tests.

    Attributes:
        name (str): The name of the function to be tested.
        test_code (str): The complete pytest code as a string that tests the function.
        file_path (str | Path): The path of the Python file containing the function, for uniqueness.
        imports (List[str], optional): Additional import statements required for the test.
    """
    name: str
    test_code: str
    file_path: str
    imports: List[str] = []

class UnitTestOutputList(BaseModel):
  items: List[UnitTestOutput]