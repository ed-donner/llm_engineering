import os
import subprocess
import shutil
import tempfile
import requests
from typing import Dict, Any

class CppCompiler:
    def __init__(self):
        self.compiler_path = None
        self.compiler_type = None
        self.detect_compiler()

    def detect_compiler(self):
        """
        Detect local C++ compiler in path (g++, clang++, or cl).
        """
        if shutil.which("g++"):
            self.compiler_path = "g++"
            self.compiler_type = "g++"
        elif shutil.which("clang++"):
            self.compiler_path = "clang++"
            self.compiler_type = "clang++"
        elif shutil.which("cl"):
            self.compiler_path = "cl"
            self.compiler_type = "msvc"

    @property
    def has_local_compiler(self) -> bool:
        return self.compiler_path is not None

    def compile_and_run(self, cpp_code: str) -> Dict[str, Any]:
        """
        Compile and run C++ code. Falls back to Compiler Explorer API if no local compiler.
        """
        if self.has_local_compiler:
            return self._compile_local(cpp_code)
        else:
            return self._compile_online(cpp_code)

    def _compile_local(self, cpp_code: str) -> Dict[str, Any]:
        """
        Perform local compilation and execution.
        """
        temp_dir = tempfile.mkdtemp()
        src_file = os.path.join(temp_dir, "main.cpp")
        exe_file = os.path.join(temp_dir, "main.exe" if os.name == "nt" else "main")

        try:
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(cpp_code)

            # Build compilation command
            if self.compiler_type in ["g++", "clang++"]:
                cmd = [self.compiler_path, "-std=c++17", "-O2", src_file, "-o", exe_file]
            elif self.compiler_type == "msvc":
                cmd = [self.compiler_path, "/std:c++17", "/EHsc", "/O2", src_file, f"/Fe{exe_file}"]
            else:
                raise ValueError("Unsupported local compiler")

            # Run compilation
            comp_proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if comp_proc.returncode != 0:
                return {
                    "success": False,
                    "method": "local",
                    "compiler": self.compiler_path,
                    "compilation_error": comp_proc.stderr or comp_proc.stdout,
                    "execution_stdout": "",
                    "execution_stderr": "",
                    "assembly": "[Assembly only available in online mode or with compiler flag]"
                }

            # Run executable
            exec_proc = subprocess.run([exe_file], capture_output=True, text=True, timeout=5)
            
            # Simple disassembly attempt using dumpbin/objdump if available, else placeholder
            assembly = "[Assembly output omitted locally. Use online mode to view full interactive assembly]"
            
            return {
                "success": True,
                "method": "local",
                "compiler": self.compiler_path,
                "compilation_error": "",
                "execution_stdout": exec_proc.stdout,
                "execution_stderr": exec_proc.stderr,
                "assembly": assembly
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "method": "local",
                "compiler": self.compiler_path,
                "compilation_error": "Process timed out.",
                "execution_stdout": "",
                "execution_stderr": "",
                "assembly": ""
            }
        except Exception as e:
            return {
                "success": False,
                "method": "local",
                "compiler": self.compiler_path,
                "compilation_error": f"Local compilation error: {str(e)}",
                "execution_stdout": "",
                "execution_stderr": "",
                "assembly": ""
            }
        finally:
            # Clean up temp folder
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    def _compile_online(self, cpp_code: str) -> Dict[str, Any]:
        """
        Compile and run C++ code online using Compiler Explorer (Godbolt) API.
        """
        # We will use GCC 13.2 ('g132') as the default C++17 compiler
        compiler_id = "g132"
        url = f"https://godbolt.org/api/compiler/{compiler_id}/compile"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "source": cpp_code,
            "options": {
                "userArguments": "-std=c++17 -O2",
                "compilerOptions": {
                    "executorRequest": True
                },
                "filters": {
                    "execute": True,
                    "intel": True,
                    "demangle": True,
                    "comments": True,
                    "directives": True
                }
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=12)
            if response.status_code != 200:
                return {
                    "success": False,
                    "method": "online",
                    "compiler": f"Compiler Explorer ({compiler_id})",
                    "compilation_error": f"API error (HTTP {response.status_code}): {response.text}",
                    "execution_stdout": "",
                    "execution_stderr": "",
                    "assembly": ""
                }

            result = response.json()
            
            # Extract compilation errors/warnings
            comp_errors = []
            if "stderr" in result:
                for line in result["stderr"]:
                    comp_errors.append(line.get("text", ""))
            comp_error_str = "\n".join(comp_errors)

            compilation_success = result.get("code", -1) == 0

            # Extract assembly output
            asm_lines = []
            if "asm" in result:
                for line in result["asm"]:
                    asm_lines.append(line.get("text", ""))
            assembly_str = "\n".join(asm_lines)

            # Extract execution results
            exec_stdout = ""
            exec_stderr = ""
            if "execResult" in result and result["execResult"] is not None:
                exec_res = result["execResult"]
                # Collect stdout
                stdout_lines = []
                if "stdout" in exec_res:
                    for line in exec_res["stdout"]:
                        stdout_lines.append(line.get("text", ""))
                exec_stdout = "\n".join(stdout_lines)
                
                # Collect stderr
                stderr_lines = []
                if "stderr" in exec_res:
                    for line in exec_res["stderr"]:
                        stderr_lines.append(line.get("text", ""))
                exec_stderr = "\n".join(stderr_lines)
            else:
                # Fallback: top-level stdout/stderr when direct executor mode is returned
                stdout_lines = []
                if "stdout" in result:
                    for line in result["stdout"]:
                        stdout_lines.append(line.get("text", ""))
                exec_stdout = "\n".join(stdout_lines)

                stderr_lines = []
                if "stderr" in result:
                    for line in result["stderr"]:
                        stderr_lines.append(line.get("text", ""))
                exec_stderr = "\n".join(stderr_lines)

            return {
                "success": compilation_success,
                "method": "online",
                "compiler": f"Compiler Explorer ({compiler_id})",
                "compilation_error": comp_error_str if not compilation_success else "",
                "execution_stdout": exec_stdout,
                "execution_stderr": exec_stderr,
                "assembly": assembly_str
            }

        except requests.Timeout:
            return {
                "success": False,
                "method": "online",
                "compiler": f"Compiler Explorer ({compiler_id})",
                "compilation_error": "Connection timed out. Compiler Explorer API was unreachable.",
                "execution_stdout": "",
                "execution_stderr": "",
                "assembly": ""
            }
        except Exception as e:
            return {
                "success": False,
                "method": "online",
                "compiler": f"Compiler Explorer ({compiler_id})",
                "compilation_error": f"API request error: {str(e)}",
                "execution_stdout": "",
                "execution_stderr": "",
                "assembly": ""
            }
