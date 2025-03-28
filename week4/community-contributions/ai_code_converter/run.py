"""Runner script for the CodeXchange AI."""
import sys
from pathlib import Path
from setuptools import setup, find_packages

# Add src to Python path
src_path = Path(__file__).parent
sys.path.append(str(src_path))

from src.ai_code_converter.main import main
from src.ai_code_converter.models.ai_streaming import AIModelStreamer
from src.ai_code_converter.core.code_execution import CodeExecutor
from src.ai_code_converter.core.language_detection import LanguageDetector
from src.ai_code_converter.core.file_utils import FileHandler
from src.ai_code_converter.config import (
    CUSTOM_CSS,
    LANGUAGE_MAPPING,
    MODELS,
    SUPPORTED_LANGUAGES,
    OPENAI_MODEL,
    CLAUDE_MODEL,
    DEEPSEEK_MODEL,
    GEMINI_MODEL,
    GROQ_MODEL
)

if __name__ == "__main__":
    main()

setup(
    name="ai_code_converter",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "gradio>=4.0.0",
        "openai>=1.0.0",
        "anthropic>=0.3.0",
        "google-generativeai>=0.1.0",
        "python-dotenv>=1.0.0",
        "jinja2>=3.0.0"
    ],
    python_requires=">=3.8",
) 