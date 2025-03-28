"""Module for handling file operations."""

import logging
import tempfile
import zipfile
import platform
from pathlib import Path
from typing import Optional, Tuple
import os
import shutil
import gradio as gr
from datetime import datetime

from src.ai_code_converter.utils.logger import setup_logger

logger = setup_logger(__name__)

class FileHandler:
    """Class for handling file operations."""
    
    def create_readme(self, language: str, files: list[str]) -> str:
        """Create a README file with compilation instructions."""
        system_info = platform.uname()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        readme = f"""# {language} Code Compilation Instructions

Generated on: {timestamp}

## Compilation Environment
- OS: {system_info.system}
- Architecture: {system_info.machine}
- Platform: {system_info.version}

## Files Included
{chr(10).join(f"- {file}" for file in files)}

## Compilation Instructions

"""
        if language == "C++":
            readme += """### Windows
1. Install MinGW or Visual Studio with C++ support
2. Open command prompt in this directory
3. Run: `g++ main.cpp -o program.exe`
4. Execute: `program.exe`

### Linux
1. Install GCC: `sudo apt-get install build-essential` (Ubuntu/Debian)
2. Open terminal in this directory
3. Run: `g++ main.cpp -o program`
4. Execute: `./program`

### macOS
1. Install Xcode Command Line Tools: `xcode-select --install`
2. Open terminal in this directory
3. Run: `g++ main.cpp -o program`
4. Execute: `./program`
"""
        elif language == "Java":
            readme += """### All Platforms (Windows/Linux/macOS)
1. Install JDK 11 or later
2. Open terminal/command prompt in this directory
3. Compile: `javac Main.java`
4. Run: `java Main`

Note: The class name in the Java file must be 'Main' for these instructions.
"""
        elif language == "Go":
            readme += """### Windows
1. Install Go from https://golang.org/
2. Open command prompt in this directory
3. Run: `go build main.go`
4. Execute: `main.exe`

### Linux/macOS
1. Install Go: 
   - Linux: `sudo apt-get install golang` (Ubuntu/Debian)
   - macOS: `brew install go` (using Homebrew)
2. Open terminal in this directory
3. Run: `go build main.go`
4. Execute: `./main`
"""
        return readme

    def create_compilation_zip(self, code: str, language: str, compiled_code: Optional[bytes] = None) -> Tuple[Optional[str], Optional[str]]:
        """Create a zip file containing source, compiled files, and README."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"ai_code_converter_{language.lower()}_{timestamp}"
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                files_included = []

                # Write source code with standardized names
                if language == "C++":
                    source_file = temp_dir_path / "main.cpp"
                    compiled_file = temp_dir_path / ("main.exe" if os.name == 'nt' else "main")
                    files_included.extend(["main.cpp", "main.exe" if os.name == 'nt' else "main"])
                elif language == "Java":
                    source_file = temp_dir_path / "Main.java"
                    compiled_file = temp_dir_path / "Main.class"
                    files_included.extend(["Main.java", "Main.class"])
                elif language == "Go":
                    source_file = temp_dir_path / "main.go"
                    compiled_file = temp_dir_path / ("main.exe" if os.name == 'nt' else "main")
                    files_included.extend(["main.go", "main.exe" if os.name == 'nt' else "main"])
                else:
                    return None, None

                # Write source code
                source_file.write_text(code)
                
                # Write compiled code if available
                if compiled_code:
                    logger.info(f"Writing compiled binary: {compiled_file}")
                    try:
                        # Ensure the file is writable
                        compiled_file.parent.mkdir(parents=True, exist_ok=True)
                        compiled_file.write_bytes(compiled_code)
                        logger.info(f"Successfully wrote compiled binary: {compiled_file}")
                    except Exception as e:
                        logger.error(f"Error writing compiled binary: {e}", exc_info=True)
                else:
                    logger.warning("No compiled code available")

                # Create README
                readme_path = temp_dir_path / "README.md"
                readme_content = self.create_readme(language, files_included)
                readme_path.write_text(readme_content)
                files_included.append("README.md")

                # Create zip file with descriptive name
                zip_filename = f"{project_name}.zip"
                zip_path = temp_dir_path / zip_filename
                
                # Create zip file
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    for file in files_included:
                        file_path = temp_dir_path / file
                        if file_path.exists():
                            logger.info(f"Adding to zip: {file}")
                            zf.write(file_path, file_path.name)
                        else:
                            logger.warning(f"File not found for zip: {file}")

                # Create a permanent location for the zip file
                downloads_dir = Path("downloads")
                downloads_dir.mkdir(exist_ok=True)
                
                final_zip_path = downloads_dir / zip_filename
                shutil.copy2(zip_path, final_zip_path)
                
                # Verify zip contents
                with zipfile.ZipFile(final_zip_path, 'r') as zf:
                    logger.info(f"Zip file contents: {zf.namelist()}")
                
                return str(final_zip_path), zip_filename

        except Exception as e:
            logger.error(f"Error creating compilation zip: {str(e)}", exc_info=True)
            return None, None

    def prepare_download(self, code: str, language: str, compiled_code: Optional[bytes] = None) -> Tuple[Optional[str], Optional[str]]:
        """Prepare code for download with consistent naming."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)
            
            # For compiled languages, create a zip with source and instructions
            if language in ["C++", "Java", "Go"]:
                logger.info(f"Creating compilation zip for {language}")
                # Pass compiled_code directly as bytes
                return self.create_compilation_zip(
                    code=code,
                    language=language,
                    compiled_code=compiled_code if isinstance(compiled_code, bytes) else None
                )
            
            # For interpreted languages, create a single file with timestamp
            extension = self._get_file_extension(language)
            filename = f"ai_code_converter_{language.lower()}_{timestamp}{extension}"
            file_path = downloads_dir / filename
            
            # Write the file
            file_path.write_text(code)
            return str(file_path), filename
                
        except Exception as e:
            logger.error(f"Error preparing download: {str(e)}", exc_info=True)
            return None, None

    def load_file(self, file_path: str) -> str:
        """Load code from a file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading file: {str(e)}", exc_info=True)
            raise

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for a language."""
        extensions = {
            "Python": ".py",
            "JavaScript": ".js",
            "Java": ".java",
            "C++": ".cpp",
            "Julia": ".jl",
            "Go": ".go"
        }
        return extensions.get(language, ".txt")

    def handle_file_upload(self, file: gr.File) -> tuple[str, str]:
        """Handle file upload with detailed logging."""
        logger = logging.getLogger(__name__)
        
        if not file:
            logger.warning("File upload attempted but no file was provided")
            return "", "No file uploaded"
        
        try:
            logger.info(f"Processing uploaded file: {file.name}")
            logger.info(f"File size: {os.path.getsize(file.name)} bytes")
            
            # Create downloads directory if it doesn't exist
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)
            
            # Copy uploaded file to downloads with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            _, ext = os.path.splitext(file.name)
            new_filename = f"ai_code_converter_upload_{timestamp}{ext}"
            new_path = downloads_dir / new_filename
            
            with open(file.name, 'r') as src, open(new_path, 'w') as dst:
                content = src.read()
                dst.write(content)
            
            logger.info(f"File saved as: {new_path}")
            logger.info(f"Content length: {len(content)} characters")
            return content, None
            
        except Exception as e:
            error_msg = f"Error loading file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return "", error_msg 