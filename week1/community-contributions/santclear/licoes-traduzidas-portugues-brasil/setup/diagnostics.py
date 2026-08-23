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
        self.log(f"Iniciando diagnósticos às {now}\n")

    def end(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"\n\nDiagnósticos concluídos às {now}\n")
        print("\nEnvie estes diagnósticos para mim em ed@edwarddonner.com")
        print(f"Copie e cole a saída acima em um e-mail ou anexe o arquivo {self.FILENAME} que foi criado neste diretório.")
    

    def _log_error(self, message):
        self.log(f"ERRO: {message}")
        self.errors.append(message)

    def _log_warning(self, message):
        self.log(f"AVISO: {message}")
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
            self.log("\n===== Avisos Encontrados =====")
            self.log("Os avisos abaixo foram identificados. Eles podem não impedir a execução do programa, mas podem provocar comportamentos inesperados:")
            for warning in self.warnings:
                self.log(f"- {warning}")

        if self.errors:
            self.log("\n===== Erros Encontrados =====")
            self.log("Os problemas críticos a seguir foram encontrados. Solucione-os antes de prosseguir:")
            for error in self.errors:
                self.log(f"- {error}")

        if not self.errors and not self.warnings:
            self.log("\n✅ Todos os diagnósticos foram concluídos com êxito!")

        self.end()

    def _step1_system_info(self):
        self.log("===== Informações do Sistema =====")
        try:
            system = platform.system()
            self.log(f"Sistema Operacional: {system}")

            if system == "Windows":
                release, version, csd, ptype = platform.win32_ver()
                self.log(f"Release do Windows: {release}")
                self.log(f"Versão do Windows: {version}")
            elif system == "Darwin":
                release, version, machine = platform.mac_ver()
                self.log(f"Versão do macOS: {release}")
            else:
                self.log(f"Plataforma: {platform.platform()}")

            self.log(f"Arquitetura: {platform.architecture()}")
            self.log(f"Máquina: {platform.machine()}")
            self.log(f"Processador: {platform.processor()}")

            try:
                import psutil
                ram = psutil.virtual_memory()
                total_ram_gb = ram.total / (1024 ** 3)
                available_ram_gb = ram.available / (1024 ** 3)
                self.log(f"RAM total: {total_ram_gb:.2f} GB")
                self.log(f"RAM disponível: {available_ram_gb:.2f} GB")

                if available_ram_gb < 2:
                    self._log_warning(f"RAM disponível baixa: {available_ram_gb:.2f} GB")
            except ImportError:
                self._log_warning("Módulo psutil não encontrado. Não foi possível determinar as informações de RAM.")

            total, used, free = shutil.disk_usage(os.path.expanduser("~"))
            free_gb = free / (1024 ** 3)
            self.log(f"Espaço livre em disco: {free_gb:.2f} GB")

            if free_gb < 5:
                self._log_warning(f"Pouco espaço em disco: {free_gb:.2f} GB livres")

        except Exception as e:
            self._log_error(f"Falha na verificação das informações do sistema: {e}")

    def _step2_check_files(self):
        self.log("\n===== Informações do Sistema de Arquivos =====")
        try:
            current_dir = os.getcwd()
            self.log(f"Diretório atual: {current_dir}")

            # Verifica permissões de escrita
            test_file = Path(current_dir) / ".test_write_permission"
            try:
                test_file.touch(exist_ok=True)
                test_file.unlink()
                self.log("Permissão de escrita: OK")
            except Exception as e:
                self._log_error(f"Sem permissão de escrita no diretório atual: {e}")

            self.log("\nArquivos no diretório atual:")
            try:
                for item in sorted(os.listdir(current_dir)):
                    self.log(f" - {item}")
            except Exception as e:
                self._log_error(f"Não é possível listar o conteúdo do diretório: {e}")

        except Exception as e:
            self._log_error(f"Falha na verificação do sistema de arquivos: {e}")

    def _step3_git_repo(self):
        self.log("\n===== Informações do Repositório Git =====")
        try:
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                git_root = result.stdout.strip()
                self.log(f"Raiz do repositório Git: {git_root}")

                result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.log(f"Commit atual: {result.stdout.strip()}")
                else:
                    self._log_warning(f"Não foi possível obter o commit atual: {result.stderr.strip()}")

                result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.log(f"Remoto 'origin': {result.stdout.strip()}")
                else:
                    self._log_warning("Remoto 'origin' não configurado")
            else:
                self._log_warning("Não é um repositório Git")
        except FileNotFoundError:
            self._log_warning("Git não está instalado ou não está no PATH")
        except Exception as e:
            self._log_error(f"Falha na verificação do Git: {e}")

    def _step4_check_env_file(self):
        self.log("\n===== Verificação do Arquivo .env =====")
        try:
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                git_root = result.stdout.strip()
                env_path = os.path.join(git_root, '.env')

                if os.path.isfile(env_path):
                    self.log(f"Arquivo .env localizado em: {env_path}")
                    try:
                        with open(env_path, 'r') as f:
                            has_api_key = any(line.strip().startswith('OPENAI_API_KEY=') for line in f)
                        if has_api_key:
                            self.log("OPENAI_API_KEY encontrado no arquivo .env")
                        else:
                            self._log_warning("OPENAI_API_KEY não encontrado no arquivo .env")
                    except Exception as e:
                        self._log_error(f"Não é possível ler o arquivo .env: {e}")
                else:
                    self._log_warning("Arquivo .env não encontrado na raiz do projeto")

                # Verifica arquivos .env adicionais
                for root, _, files in os.walk(git_root):
                    if '.env' in files and os.path.join(root, '.env') != env_path:
                        self._log_warning(f"Arquivo .env adicional encontrado em: {os.path.join(root, '.env')}")
            else:
                self._log_warning("Diretório raiz do Git não encontrado. Não é possível realizar a verificação do arquivo .env.")
        except FileNotFoundError:
            self._log_warning("Git não está instalado ou não está no PATH")
        except Exception as e:
            self._log_error(f"Falha na verificação do arquivo .env: {e}")

    def _step5_anaconda_check(self):
        self.log("\n===== Verificação do Ambiente Anaconda =====")
        try:
            conda_prefix = os.environ.get('CONDA_PREFIX')
            if conda_prefix:
                self.log("Ambiente Anaconda ativo:")
                self.log(f"Caminho do ambiente: {conda_prefix}")
                self.log(f"Nome do ambiente: {os.path.basename(conda_prefix)}")

                conda_exe = os.environ.get('CONDA_EXE', 'conda')
                result = subprocess.run([conda_exe, '--version'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.log(f"Versão do Conda: {result.stdout.strip()}")
                else:
                    self._log_warning("Não foi possível determinar a versão do Conda")

                self._check_python_packages()
            else:
                self.log("Nenhum ambiente Anaconda ativo detectado")
        except Exception as e:
            self._log_error(f"Falha na verificação do ambiente Anaconda: {e}")

    def _step6_virtualenv_check(self):
        self.log("\n===== Verificação do Virtualenv =====")
        try:
            virtual_env = os.environ.get('VIRTUAL_ENV')
            if virtual_env:
                self.log("Virtualenv ativo:")
                self.log(f"Caminho do ambiente: {virtual_env}")
                self.log(f"Nome do ambiente: {os.path.basename(virtual_env)}")

                self._check_python_packages()
            else:
                self.log("Nenhum virtualenv ativo detectado")

            if not virtual_env and not os.environ.get('CONDA_PREFIX'):
                self._log_warning("Nem virtualenv nem ambiente Anaconda estão ativos")
        except Exception as e:
            self._log_error(f"Falha na verificação do virtualenv: {e}")

    def _check_python_packages(self):
        self.log("\nAmbiente Python:")
        self.log(f"Versão do Python: {sys.version}")
        self.log(f"Executável do Python: {sys.executable}")

        required_packages = ['openai', 'python-dotenv', 'requests', 'gradio', 'transformers']

        try:
            import pkg_resources
            installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}

            self.log("\nVersões dos pacotes necessários:")
            for package in required_packages:
                if package in installed:
                    self.log(f"{package}: {installed[package]}")
                else:
                    self._log_error(f"Pacote obrigatório '{package}' não está instalado")

            # Verifica pacotes potencialmente conflitantes
            problem_pairs = [
                ('openai', 'openai-python'),
                ('python-dotenv', 'dotenv')
            ]

            for pkg1, pkg2 in problem_pairs:
                if pkg1 in installed and pkg2 in installed:
                    self._log_warning(f"Pacotes potencialmente conflitantes: {pkg1} e {pkg2}")
        except ImportError:
            self._log_error("Não foi possível importar 'pkg_resources' para verificar os pacotes instalados")
        except Exception as e:
            self._log_error(f"Falha na verificação de pacotes: {e}")

    def _step7_network_connectivity(self):
        self.log("\n===== Verificação da Conectividade de Rede =====")
        try:
            self.log(f"Versão do SSL: {ssl.OPENSSL_VERSION}")
    
            import requests
            import speedtest  # Importa a biblioteca speedtest-cli
    
            # Verificação básica de conectividade
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
                    self.log(f"✅ Conectado a {url}")
                    self.log(f"  Tempo de resposta: {elapsed_time:.2f}s")
    
                    if elapsed_time > 2:
                        self._log_warning(f"Resposta lenta de {url}: {elapsed_time:.2f}s")
                    connected = True
                    break
                except requests.exceptions.RequestException as e:
                    self._log_warning(f"Falha ao conectar-se a {url}: {e}")
                else:
                    self.log("Conectividade básica OK")
    
            if not connected:
                self._log_error("Falha ao conectar-se a qualquer URL de teste")
                return
    
            # Teste de largura de banda usando speedtest-cli
            self.log("\nRealizando teste de largura de banda com speedtest-cli...")
            try:
                st = speedtest.Speedtest()
                st.get_best_server()
                download_speed = st.download()  # Bits por segundo
                upload_speed = st.upload()      # Bits por segundo
    
                download_mbps = download_speed / 1e6  # Converte para Mbps
                upload_mbps = upload_speed / 1e6
    
                self.log(f"Velocidade de download: {download_mbps:.2f} Mbps")
                self.log(f"Velocidade de upload: {upload_mbps:.2f} Mbps")
    
                if download_mbps < 1:
                    self._log_warning("Velocidade de download baixa")
                if upload_mbps < 0.5:
                    self._log_warning("Velocidade de upload baixa")
            except speedtest.ConfigRetrievalError:
                self._log_error("Falha ao obter a configuração do speedtest")
            except Exception as e:
                self._log_warning(f"Falha no teste de largura de banda: {e}")
    
        except ImportError:
            self._log_error("Pacotes obrigatórios não estão instalados. Instale-os com 'pip install requests speedtest-cli'")
        except Exception as e:
            self._log_error(f"Falha na verificação da conectividade de rede: {e}")


    def _step8_environment_variables(self):
        self.log("\n===== Verificação das Variáveis de Ambiente =====")
        try:
            # Verifica os caminhos do Python
            pythonpath = os.environ.get('PYTHONPATH')
            if pythonpath:
                self.log("\nPYTHONPATH:")
                for path in pythonpath.split(os.pathsep):
                    self.log(f" - {path}")
            else:
                self.log("\nPYTHONPATH não está definido.")

            self.log("\nsys.path do Python:")
            for path in sys.path:
                self.log(f" - {path}")

            # Verifica OPENAI_API_KEY
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.log("OPENAI_API_KEY definido após chamar load_dotenv()")
                if not api_key.startswith('sk-proj-') or len(api_key) < 12:
                    self._log_warning("Formato de OPENAI_API_KEY parece incorreto após chamar load_dotenv()")
            else:
                self._log_warning("Variável de ambiente OPENAI_API_KEY não está definida após chamar load_dotenv()")
        except Exception as e:
            self._log_error(f"Falha na verificação das variáveis de ambiente: {e}")

    def _step9_additional_diagnostics(self):
        self.log("\n===== Diagnósticos Adicionais =====")
        try:
            # Obtém os caminhos dos diretórios site-packages
            import site
            site_packages_paths = site.getsitepackages()
            if hasattr(site, 'getusersitepackages'):
                site_packages_paths.append(site.getusersitepackages())
    
            # Função que verifica se um caminho está dentro de site-packages
            def is_in_site_packages(path):
                return any(os.path.commonpath([path, sp]) == sp for sp in site_packages_paths)
    
            # Verifica possíveis conflitos de nome no diretório atual e no sys.path
            conflict_names = ['openai.py', 'dotenv.py']
    
            # Verifica o diretório atual
            current_dir = os.getcwd()
            for name in conflict_names:
                conflict_path = os.path.join(current_dir, name)
                if os.path.isfile(conflict_path):
                    self._log_warning(f"Encontrado '{name}' no diretório atual, o que pode causar conflitos de importação: {conflict_path}")
    
            # Verifica os diretórios em sys.path
            for path in sys.path:
                if not path or is_in_site_packages(path):
                    continue  # Ignora site-packages e caminhos vazios
                for name in conflict_names:
                    conflict_file = os.path.join(path, name)
                    if os.path.isfile(conflict_file):
                        self._log_warning(f"Potencial conflito de nomenclatura: {conflict_file}")
    
            # Verifica o diretório temporário
            try:
                with tempfile.NamedTemporaryFile() as tmp:
                    self.log(f"Diretório temporário é gravável: {os.path.dirname(tmp.name)}")
            except Exception as e:
                self._log_error(f"Não é possível gravar no diretório temporário: {e}")
    
        except Exception as e:
            self._log_error(f"Falha na execução dos diagnósticos adicionais: {e}")


if __name__ == "__main__":
    diagnostics = Diagnostics()
    diagnostics.run()

