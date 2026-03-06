#!/usr/bin/env python3

import sys
import os
import subprocess
import time
import signal
from service_manager import ServiceManager

def show_usage():
    print("Usage: python main.py <command> [service_name]")
    print("Commands:")
    print("  start [service]  - Start all services or specific service")
    print("  stop [service]   - Stop all services or specific service")
    print("  restart [service] - Restart specific service")
    print("  status           - Show status of all services")
    print("  run              - Start all services and launch UI (default)")
    print("  ui               - Launch UI only (assumes services are running)")
    print("  kill             - Force kill all services (use if stop doesn't work)")
    print("\nService names: scanner, specialist, frontier, random-forest, ensemble, planning, notification-service, notification-receiver, ui")
    print("\nExamples:")
    print("  python main.py run              # Start everything and launch UI")
    print("  python main.py start            # Start all services")
    print("  python main.py start scanner    # Start only scanner service")
    print("  python main.py status           # Check service status")
    print("  python main.py stop             # Stop all services")
    print("  python main.py kill             # Force kill all services")

def launch_ui():
    """Launch the UI assuming services are already running"""
    print("Launching UI...")
    try:
        from services.ui import App
        app = App()
        app.run()
    except Exception as e:
        print(f"Failed to launch UI: {e}")
        print("Make sure all services are running first. Use 'python main.py status' to check.")

def run_full_app():
    """Start all services and launch the UI"""
    print("Starting The Price is Right - Full Application")
    print("=" * 50)
    
    # Initialize service manager
    manager = ServiceManager()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nReceived interrupt signal. Cleaning up...")
        manager.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start all services first
        print("Starting microservices...")
        if not manager.start_all():
            print("Failed to start some services. Check logs/ directory for details.")
            return
        
        print("\nWaiting for services to initialize...")
        time.sleep(3)  # Give services time to start
        
        # Now launch the UI
        launch_ui()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.cleanup()

def main():
    if len(sys.argv) < 2:
        # Default behavior: run the full app
        run_full_app()
        return
    
    command = sys.argv[1].lower()
    service_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Initialize service manager
    manager = ServiceManager()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nReceived interrupt signal. Cleaning up...")
        manager.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if command == 'run':
            run_full_app()
        elif command == 'ui':
            launch_ui()
        elif command == 'start':
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
        elif command == 'kill':
            manager.force_kill_all()
        elif command in ['help', '-h', '--help']:
            show_usage()
        else:
            print(f"Unknown command: {command}")
            show_usage()
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
