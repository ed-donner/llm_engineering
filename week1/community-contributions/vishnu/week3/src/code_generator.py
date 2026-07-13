import re
import time
from typing import Dict, Any, Tuple
from src.factory import ProviderFactory
from src.models import ModelManager

class CodeGenerator:
    SYSTEM_PROMPT = """You are a high-performance C++ compiler assistant and systems programmer.
Your task is to translate Python code to clean, optimized, and modern C++17 code.

Rules:
1. Respond ONLY with the converted C++ code wrapped in a ```cpp block.
2. Include all necessary C++ standard library headers (e.g. <iostream>, <vector>, <string>, <algorithm>, <numeric>).
3. Do not include any explanations, notes, markdown outside the code block, or general conversational text.
4. Ensure the output has a main() entrypoint if the Python code has executable statements.
5. Keep names consistent and optimize for C++ performance standards (prefer reference parameters, const, reserve capacity for vectors, etc.)."""

    def __init__(self, provider_name: str, model_id: str):
        self.provider_name = provider_name
        self.model_id = model_id
        self.provider = ProviderFactory.get_provider(provider_name)

    def translate(self, python_code: str) -> Tuple[str, float]:
        """
        Translate Python code to C++17. Returns (cpp_code, latency).
        """
        prompt = f"Please translate this Python code to optimized C++17:\n\n{python_code}"
        
        start_time = time.time()
        success = False
        error_msg = ""
        cpp_output = ""
        
        try:
            raw_response, latency = self.provider.generate(
                model_id=self.model_id,
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            # Extract content between ```cpp and ```
            cpp_match = re.search(r"```cpp(.*?)```", raw_response, re.DOTALL | re.IGNORECASE)
            if cpp_match:
                cpp_output = cpp_match.group(1).strip()
            else:
                # Secondary check for plain ``` code block
                generic_match = re.search(r"```(.*?)```", raw_response, re.DOTALL)
                if generic_match:
                    cpp_output = generic_match.group(1).strip()
                else:
                    cpp_output = raw_response.strip()
            
            success = True
            return cpp_output, latency
        except Exception as e:
            error_msg = str(e)
            cpp_output = f"// Translation failed: {error_msg}"
            latency = time.time() - start_time
            raise e
        finally:
            ModelManager.log_interaction(
                provider=self.provider_name,
                model=self.model_id,
                latency=latency,
                success=success,
                error=error_msg
            )
