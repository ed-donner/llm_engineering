#!/usr/bin/env python3

import subprocess
import sys
import os
import time
import signal
import psutil
from typing import Dict, List, Optional

class ServiceManager:
    def __init__(self):
        self.services = {
            'scanner': {'port': 8001, 'script': 'services/scanner_agent.py'},
            'specialist': {'port': 8002, 'script': 'services/specialist_agent.py'},
            'frontier': {'port': 8003, 'script': 'services/frontier_agent.py'},
            'random-forest': {'port': 8004, 'script': 'services/random_forest_agent.py'},
            'ensemble': {'port': 8005, 'script': 'services/ensemble_agent.py'},
            'planning': {'port': 8006, 'script': 'services/planning_agent.py'},
            'notification-service': {'port': 8007, 'script': 'services/notification_service.py'},
            'notification-receiver': {'port': 8008, 'script': 'services/notification_receiver.py'},
            'ui': {'port': 7860, 'script': 'services/ui.py'},
        }
        self.processes: Dict[str, subprocess.Popen] = {}
        self.logs_dir = 'logs'
        
        # Create logs directory if it doesn't exist
        os.makedirs(self.logs_dir, exist_ok=True)

    def _find_process_by_port(self, port: int) -> Optional[int]:
        """Find the PID of the process using the specified port"""
        try:
            # Use lsof command as psutil has permission issues on macOS
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split('\n')[0])
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
            pass
        return None

    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use"""
        try:
            # Use lsof command as psutil has permission issues on macOS
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        if service_name not in self.services:
            print(f"Unknown service: {service_name}")
            return False
        
        if service_name in self.processes:
            print(f"Service {service_name} is already running")
            return True
        
        service_info = self.services[service_name]
        script_path = service_info['script']
        port = service_info['port']
        
        if not os.path.exists(script_path):
            print(f"Service script not found: {script_path}")
            return False
        
        if self.is_port_in_use(port):
            print(f"Port {port} is already in use")
            return False
        
        try:
            log_file = open(f"{self.logs_dir}/{service_name}.log", "w")
            # Use virtual environment Python if available
            python_executable = sys.executable
            venv_python = os.path.join(os.getcwd(), '.venv', 'bin', 'python')
            if os.path.exists(venv_python):
                python_executable = venv_python
            
            process = subprocess.Popen(
                [python_executable, script_path],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd(),
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            self.processes[service_name] = process
            print(f"Started {service_name} (PID: {process.pid}) on port {port}")
            return True
        except Exception as e:
            print(f"Failed to start {service_name}: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        if service_name not in self.services:
            print(f"Unknown service: {service_name}")
            return False
        
        service_info = self.services[service_name]
        port = service_info['port']
        
        # First try to stop tracked process
        if service_name in self.processes:
            process = self.processes[service_name]
            try:
                process.terminate()
                process.wait(timeout=5)
                del self.processes[service_name]
                print(f"Stopped {service_name} (tracked process)")
                return True
            except subprocess.TimeoutExpired:
                process.kill()
                del self.processes[service_name]
                print(f"Force killed {service_name} (tracked process)")
                return True
            except Exception as e:
                print(f"Failed to stop tracked process for {service_name}: {e}")
        
        # If no tracked process or it failed, try to find and kill by port
        if self.is_port_in_use(port):
            pid = self._find_process_by_port(port)
            if pid:
                try:
                    # Try graceful termination first
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(2)
                    
                    # Check if still running
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        # Still running, force kill
                        os.kill(pid, signal.SIGKILL)
                        print(f"Force killed {service_name} (PID: {pid})")
                    except ProcessLookupError:
                        # Process already terminated
                        print(f"Stopped {service_name} (PID: {pid})")
                    return True
                except ProcessLookupError:
                    print(f"Process {service_name} (PID: {pid}) already stopped")
                    return True
                except PermissionError:
                    print(f"Permission denied to stop {service_name} (PID: {pid})")
                    return False
                except Exception as e:
                    print(f"Failed to stop {service_name} (PID: {pid}): {e}")
                    return False
            else:
                print(f"Port {port} is in use but couldn't find process for {service_name}")
                return False
        else:
            print(f"Service {service_name} is not running (port {port} not in use)")
            return True

    def start_all(self) -> bool:
        """Start all services"""
        print("Starting all services...")
        success = True
        
        # Start services in dependency order
        start_order = [
            'scanner', 'specialist', 'frontier', 'random-forest',
            'ensemble', 'planning', 'notification-service', 
            'notification-receiver', 'ui'
        ]
        
        for service_name in start_order:
            if not self.start_service(service_name):
                success = False
            time.sleep(1)  # Small delay between starts
        
        if success:
            print("All services started successfully!")
            print("\nService URLs:")
            print("- Scanner Agent: http://localhost:8001")
            print("- Specialist Agent: http://localhost:8002")
            print("- Frontier Agent: http://localhost:8003")
            print("- Random Forest Agent: http://localhost:8004")
            print("- Ensemble Agent: http://localhost:8005")
            print("- Planning Agent: http://localhost:8006")
            print("- Notification Service: http://localhost:8007")
            print("- Notification Receiver: http://localhost:8008")
            print("- UI: http://localhost:7860")
        else:
            print("Some services failed to start. Check logs/ directory for details.")
        
        return success

    def stop_all(self) -> bool:
        """Stop all services"""
        print("Stopping all services...")
        success = True
        
        # Stop tracked processes first
        for service_name in reversed(list(self.processes.keys())):
            if not self.stop_service(service_name):
                success = False
        
        # Clear the processes dict
        self.processes.clear()
        
        # Now stop any remaining services by port
        for service_name, service_info in self.services.items():
            port = service_info['port']
            if self.is_port_in_use(port):
                print(f"Found orphaned service on port {port}, stopping {service_name}...")
                if not self.stop_service(service_name):
                    success = False
        
        if success:
            print("All services stopped successfully!")
        else:
            print("Some services failed to stop properly.")
        
        return success

    def status(self) -> None:
        """Show status of all services"""
        print("Service Status:")
        print("-" * 50)
        
        for service_name, service_info in self.services.items():
            port = service_info['port']
            try:
                # First check if we have a tracked process
                if service_name in self.processes:
                    process = self.processes[service_name]
                    if process.poll() is None:
                        print(f"{service_name:20} | Running (PID: {process.pid}) | Port: {port}")
                    else:
                        print(f"{service_name:20} | Stopped (exit code: {process.returncode}) | Port: {port}")
                        del self.processes[service_name]
                else:
                    # Check if port is in use and try to find the actual process
                    if self.is_port_in_use(port):
                        # Try to find the process using this port
                        pid = self._find_process_by_port(port)
                        if pid:
                            print(f"{service_name:20} | Running (PID: {pid}) | Port: {port}")
                        else:
                            print(f"{service_name:20} | Port {port} in use (external process)")
                    else:
                        print(f"{service_name:20} | Stopped | Port: {port}")
            except Exception as e:
                print(f"{service_name:20} | Error checking status: {e}")

    def restart(self, service_name: str) -> bool:
        """Restart a specific service"""
        print(f"Restarting {service_name}...")
        self.stop_service(service_name)
        time.sleep(1)
        return self.start_service(service_name)

    def force_kill_all(self) -> bool:
        """Force kill all processes using service ports"""
        print("Force killing all services...")
        success = True
        
        for service_name, service_info in self.services.items():
            port = service_info['port']
            if self.is_port_in_use(port):
                pid = self._find_process_by_port(port)
                if pid:
                    try:
                        os.kill(pid, signal.SIGKILL)
                        print(f"Force killed {service_name} (PID: {pid})")
                    except ProcessLookupError:
                        print(f"Process {service_name} (PID: {pid}) already stopped")
                    except PermissionError:
                        print(f"Permission denied to kill {service_name} (PID: {pid})")
                        success = False
                    except Exception as e:
                        print(f"Failed to kill {service_name} (PID: {pid}): {e}")
                        success = False
        
        # Clear tracked processes
        self.processes.clear()
        
        if success:
            print("All services force killed!")
        else:
            print("Some services could not be killed.")
        
        return success

    def cleanup(self):
        """Clean up on exit"""
        if self.processes:
            print("\nCleaning up running processes...")
            self.stop_all()

def main():
    manager = ServiceManager()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nReceived interrupt signal. Cleaning up...")
        manager.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if len(sys.argv) < 2:
        print("Usage: python service_manager.py <command> [service_name]")
        print("Commands: start, stop, restart, status")
        print("Service names: scanner, specialist, frontier, random-forest, ensemble, planning, notification-service, notification-receiver, ui")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    service_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        if command == 'start':
            if service_name:
                manager.start_service(service_name)
            else:
                manager.start_all()
        elif command == 'stop':
            if service_name:
                manager.stop_service(service_name)
            else:
                manager.stop_all()
        elif command == 'restart':
            if service_name:
                manager.restart(service_name)
            else:
                print("Please specify a service name to restart")
        elif command == 'status':
            manager.status()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        manager.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        manager.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
