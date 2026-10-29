import subprocess
import tempfile
import os
from dataclasses import dataclass

@dataclass
class TestResult:
    passed: bool
    output: str
    errors: str
    attempts: int = 0

def run_pytest(source_code: str, test_code: str) -> TestResult:
    """
    Run the source code and test code using `pytest`.
    Use a temporary directory (`tempdir`) to avoid cluttering the project folder.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # write source code
        source_path = os.path.join(tmpdir, "source.py")
        with open(source_path, "w") as f:
            f.write(source_code)

        # Write test code — automatically inject imports if they are missing
        if "from source import" not in test_code and "import source" not in test_code:
            test_code = "from source import *\n\n" + test_code
        
        test_path = os.path.join(tmpdir, "test_source.py")
        with open(test_path, "w") as f:
            f.write(test_code)

        # run pytest
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=tmpdir
        )

        passed = result.returncode == 0
        return TestResult(
            passed=passed,
            output=result.stdout,
            errors=result.stderr if not passed else ""
        )
