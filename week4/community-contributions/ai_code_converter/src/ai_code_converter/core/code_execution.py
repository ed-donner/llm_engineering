"""Module for executing code in different programming languages."""

import contextlib
import io
import logging
import os
import re
import subprocess
import tempfile
from typing import Optional
from datetime import datetime
from src.ai_code_converter.utils.logger import setup_logger
from pathlib import Path

# Initialize logger for this module
logger = setup_logger(__name__)

class CodeExecutor:
    """Class for executing code in various programming languages."""
    
    def __init__(self):
        """Initialize the code executor."""
        logger.info("Initializing CodeExecutor")
        self.executors = {
            "Python": self.execute_python,
            "JavaScript": self.execute_javascript,
            "Java": self.execute_java,
            "C++": self.execute_cpp,
            "Julia": self.execute_julia,
            "Go": self.execute_go,
            "Perl": self.execute_perl,
            "Lua": self.execute_lua,
            "PHP": self.execute_php,
            "Kotlin": self.execute_kotlin,
            "SQL": self.execute_sql,
            "R": self.execute_r,
            "Ruby": self.execute_ruby,
            "Swift": self.execute_swift,
            "Rust": self.execute_rust,
            "C#": self.execute_csharp,
            "TypeScript": self.execute_typescript
        }

    def execute(self, code: str, language: str) -> tuple[str, Optional[bytes]]:
        """Execute code with detailed logging."""
        logger.info("="*50)
        logger.info(f"STARTING CODE EXECUTION: {language}")
        logger.info("="*50)
        logger.info(f"Code length: {len(code)} characters")
        
        if not code:
            logger.warning("No code provided for execution")
            return "No code to execute", None
        
        executor = self.executors.get(language)
        if not executor:
            logger.error(f"No executor found for language: {language}")
            return f"Execution not implemented for {language}", None
        
        try:
            logger.info(f"Executing {language} code")
            start_time = datetime.now()
            
            output, binary = executor(code)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Execution completed in {execution_time:.2f} seconds")
            logger.info(f"Output length: {len(output)} characters")
            if binary:
                logger.info(f"Binary size: {len(binary)} bytes")
            logger.info("="*50)
            
            return f"{output}\nExecution completed in {execution_time:.2f} seconds", binary
            
        except Exception as e:
            logger.error(f"Error executing {language} code", exc_info=True)
            logger.info("="*50)
            return f"Error: {str(e)}", None

    def execute_python(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute Python code in a safe environment."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                # Create a shared namespace for globals and locals
                namespace = {}
                
                # Execute the code with shared namespace
                exec(code, namespace, namespace)
                
                # Get any stored output
                execution_output = output.getvalue()
                
                # If there's a result variable, append it to output
                if '_result' in namespace:
                    execution_output += str(namespace['_result'])
                    
                return execution_output, None
            except Exception as e:
                logger.error(f"Python execution error: {str(e)}", exc_info=True)
                return f"Error: {str(e)}", None
            finally:
                output.close()

    def execute_javascript(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute JavaScript code using Node.js."""
        with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as f:
            f.write(code)
            js_file = f.name
            
        try:
            result = subprocess.run(
                ["node", js_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(js_file)

    def execute_julia(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute Julia code."""
        with tempfile.NamedTemporaryFile(suffix='.jl', mode='w', delete=False) as f:
            f.write(code)
            jl_file = f.name
            
        try:
            result = subprocess.run(
                ["julia", jl_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(jl_file)

    def execute_cpp(self, code: str) -> tuple[str, Optional[bytes]]:
        """Compile and execute C++ code."""
        with tempfile.NamedTemporaryFile(suffix='.cpp', mode='w', delete=False) as f:
            f.write(code)
            cpp_file = f.name
            
        try:
            # Compile
            exe_file = cpp_file[:-4]  # Remove .cpp
            if os.name == 'nt':  # Windows
                exe_file += '.exe'
                
            compile_result = subprocess.run(
                ["g++", cpp_file, "-o", exe_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Execute
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Read the compiled binary
            with open(exe_file, 'rb') as f:
                compiled_binary = f.read()
            
            return run_result.stdout, compiled_binary
            
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(cpp_file)
            if os.path.exists(exe_file):
                os.unlink(exe_file)

    def execute_java(self, code: str) -> tuple[str, Optional[bytes]]:
        """Compile and execute Java code."""
        logger.info("Starting Java code execution")
        
        # Create a temporary directory with proper permissions
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Extract class name
                class_match = re.search(r'public\s+class\s+(\w+)', code)
                if not class_match:
                    logger.error("Could not find public class name in Java code")
                    return "Error: Could not find public class name", None
                    
                class_name = class_match.group(1)
                temp_path = Path(temp_dir)
                java_file = temp_path / f"{class_name}.java"
                class_file = temp_path / f"{class_name}.class"
                
                # Write code to file
                java_file.write_text(code)
                logger.info(f"Wrote Java source to {java_file}")
                
                # Compile
                logger.info("Compiling Java code")
                compile_result = subprocess.run(
                    ["javac", str(java_file)],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=temp_dir  # Set working directory to temp_dir
                )
                logger.info("Java compilation successful")
                
                # Verify class file exists
                if not class_file.exists():
                    logger.error(f"Class file {class_file} not found after compilation")
                    return "Error: Compilation failed to produce class file", None
                
                # Read compiled bytecode
                compiled_binary = class_file.read_bytes()
                logger.info(f"Read compiled binary, size: {len(compiled_binary)} bytes")
                
                # Execute
                logger.info("Executing Java code")
                run_result = subprocess.run(
                    ["java", class_name],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=temp_dir  # Set working directory to temp_dir
                )
                logger.info("Java execution successful")
                
                # Return both output and compiled binary
                return run_result.stdout, compiled_binary
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Java compilation/execution error: {e.stderr}")
                return f"Error: {e.stderr}", None
            except Exception as e:
                logger.error(f"Unexpected error in Java execution: {str(e)}", exc_info=True)
                return f"Error: {str(e)}", None

    def execute_go(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute Go code."""
        with tempfile.NamedTemporaryFile(suffix='.go', mode='w', delete=False) as f:
            f.write(code)
            go_file = f.name
            
        try:
            # Compile first
            exe_file = go_file[:-3]  # Remove .go
            if os.name == 'nt':
                exe_file += '.exe'
            
            compile_result = subprocess.run(
                ["go", "build", "-o", exe_file, go_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Read compiled binary
            with open(exe_file, 'rb') as f:
                compiled_binary = f.read()
            
            # Execute
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                check=True
            )
            return run_result.stdout, compiled_binary
            
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(go_file)
            if os.path.exists(exe_file):
                os.unlink(exe_file)
                
    def execute_perl(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute Perl code."""
        with tempfile.NamedTemporaryFile(suffix='.pl', mode='w', delete=False) as f:
            f.write(code)
            pl_file = f.name
            
        try:
            result = subprocess.run(
                ["perl", pl_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(pl_file)
            
    def execute_lua(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute Lua code."""
        with tempfile.NamedTemporaryFile(suffix='.lua', mode='w', delete=False) as f:
            f.write(code)
            lua_file = f.name
            
        try:
            result = subprocess.run(
                ["lua", lua_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(lua_file)
            
    def execute_php(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute PHP code."""
        with tempfile.NamedTemporaryFile(suffix='.php', mode='w', delete=False) as f:
            f.write(code)
            php_file = f.name
            
        try:
            result = subprocess.run(
                ["php", php_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(php_file)
            
    def execute_kotlin(self, code: str) -> tuple[str, Optional[bytes]]:
        """Compile and execute Kotlin code."""
        with tempfile.NamedTemporaryFile(suffix='.kt', mode='w', delete=False) as f:
            f.write(code)
            kt_file = f.name
            
        try:
            # Extract main class name (best effort)
            class_match = re.search(r'class\s+(\w+)', code)
            class_name = class_match.group(1) if class_match else "MainKt"
            
            # Compile
            jar_file = kt_file[:-3] + ".jar"
            compile_result = subprocess.run(
                ["kotlinc", kt_file, "-include-runtime", "-d", jar_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Read compiled bytecode
            with open(jar_file, 'rb') as f:
                compiled_binary = f.read()
            
            # Execute
            run_result = subprocess.run(
                ["java", "-jar", jar_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            return run_result.stdout, compiled_binary
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(kt_file)
            jar_file = kt_file[:-3] + ".jar"
            if os.path.exists(jar_file):
                os.unlink(jar_file)
                
    def execute_sql(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute SQL code using SQLite."""
        # Create a temporary database file
        db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name
            
        try:
            # Write SQL directly to the sqlite3 process via stdin
            process = subprocess.Popen(
                ["sqlite3", db_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send the SQL code to sqlite3
            stdout, stderr = process.communicate(input=code)
            
            if process.returncode != 0:
                return f"Error: {stderr}", None
            
            # For SQL, we'll also run a simple query to show tables
            tables_result = subprocess.run(
                ["sqlite3", db_file, ".tables"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Combine the results
            output = stdout
            if tables_result.returncode == 0 and tables_result.stdout.strip():
                output += "\n\nTables in database:\n" + tables_result.stdout
                
                # For each table, show schema
                for table in tables_result.stdout.split():
                    schema_result = subprocess.run(
                        ["sqlite3", db_file, f".schema {table}"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if schema_result.returncode == 0:
                        output += "\n" + schema_result.stdout
            
            return output, None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            if os.path.exists(db_file):
                os.unlink(db_file)
            
    def execute_r(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute R code."""
        with tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False) as f:
            f.write(code)
            r_file = f.name
            
        try:
            result = subprocess.run(
                ["Rscript", r_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(r_file)
            
    def execute_ruby(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute Ruby code."""
        with tempfile.NamedTemporaryFile(suffix='.rb', mode='w', delete=False) as f:
            f.write(code)
            rb_file = f.name
            
        try:
            result = subprocess.run(
                ["ruby", rb_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(rb_file)
            
    def execute_swift(self, code: str) -> tuple[str, Optional[bytes]]:
        """Execute Swift code."""
        with tempfile.NamedTemporaryFile(suffix='.swift', mode='w', delete=False) as f:
            f.write(code)
            swift_file = f.name
            
        try:
            result = subprocess.run(
                ["swift", swift_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(swift_file)
            
    def execute_rust(self, code: str) -> tuple[str, Optional[bytes]]:
        """Compile and execute Rust code."""
        # Create a temporary directory for Rust project
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.rs file
            main_rs = os.path.join(temp_dir, "main.rs")
            with open(main_rs, 'w') as f:
                f.write(code)
                
            try:
                # Compile
                exe_file = os.path.join(temp_dir, "rustapp")
                compile_result = subprocess.run(
                    ["rustc", main_rs, "-o", exe_file],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Read compiled binary
                with open(exe_file, 'rb') as f:
                    compiled_binary = f.read()
                
                # Execute
                run_result = subprocess.run(
                    [exe_file],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                return run_result.stdout, compiled_binary
            except subprocess.CalledProcessError as e:
                return f"Error: {e.stderr}", None
            except Exception as e:
                return f"Error: {str(e)}", None
                
    def execute_csharp(self, code: str) -> tuple[str, Optional[bytes]]:
        """Compile and execute C# code."""
        with tempfile.NamedTemporaryFile(suffix='.cs', mode='w', delete=False) as f:
            f.write(code)
            cs_file = f.name
            
        try:
            # Compile to executable
            exe_file = cs_file[:-3] + ".exe"
            compile_result = subprocess.run(
                ["mono-csc", cs_file, "-out:" + exe_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Read compiled binary
            with open(exe_file, 'rb') as f:
                compiled_binary = f.read()
            
            # Execute
            if os.name == 'nt':  # Windows
                run_result = subprocess.run(
                    [exe_file],
                    capture_output=True,
                    text=True,
                    check=True
                )
            else:  # Unix-like
                run_result = subprocess.run(
                    ["mono", exe_file],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
            return run_result.stdout, compiled_binary
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(cs_file)
            exe_file = cs_file[:-3] + ".exe"
            if os.path.exists(exe_file):
                os.unlink(exe_file)
                
    def execute_typescript(self, code: str) -> tuple[str, Optional[bytes]]:
        """Compile and execute TypeScript code."""
        with tempfile.NamedTemporaryFile(suffix='.ts', mode='w', delete=False) as f:
            f.write(code)
            ts_file = f.name
            
        try:
            # Compile TypeScript to JavaScript
            js_file = ts_file[:-3] + ".js"
            compile_result = subprocess.run(
                ["tsc", ts_file, "--outFile", js_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Execute the compiled JavaScript
            run_result = subprocess.run(
                ["node", js_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            return run_result.stdout, None
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", None
        except Exception as e:
            return f"Error: {str(e)}", None
        finally:
            os.unlink(ts_file)
            js_file = ts_file[:-3] + ".js"
            if os.path.exists(js_file):
                os.unlink(js_file)