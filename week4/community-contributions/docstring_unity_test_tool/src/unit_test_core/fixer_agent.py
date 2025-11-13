from src.core_base.agents.base_agents import BaseCodeAgent

class UnitTestFixerAgent(BaseCodeAgent):
    """
    Agent that takes generated pytest code and fixes any syntax errors, missing imports, or other issues, returning corrected, runnable code.
    """

    async def fix_tests(self, test_code: str, project_path: str, original_path: str) -> str:
        """
        Review and correct the generated pytest code.
        
        This method reviews the provided test code, correcting any syntax errors and ensuring the code is runnable with pytest.
        
        Args:
          test_code (str): The generated pytest code to review/fix.
          project_path (str): The absolute path to the project, used for inferring correct import statements.
          original_path (str): The absolute path to the original test file, used for context.
        
        Returns:
          str: The corrected pytest code.
        """
        prompt = f"""
                    You are an expert Python developer.

                    Review the following pytest code. 
                    Your task is to correct any syntax errors, fix or add missing imports, 
                    and ensure that all tests are runnable with pytest.

                    ⚠️ Important constraints:
                    - Remove innecesary imports.
                    - Do NOT use sys.path manipulations (e.g. `sys.path.append`, `os.chdir`, etc.).
                    - Do NOT use relative path hacks with `Path(__file__)`.
                    - All imports must be written as clean runable for the prject path (DON'T include the project path in the imports).
                    - Use the provided project path and file path to infer the correct import statements.
                    - Do NOT remove or rename any test functions.
                    - Return only the corrected Python code, fully runnable with pytest.

                    Project path: {project_path}

                    Test made for the file in the path: {original_path}

                    Pytest code to fix:
                    {test_code}
                    """


        fixed_code = await self.run(prompt)
        return fixed_code