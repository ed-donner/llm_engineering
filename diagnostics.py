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
