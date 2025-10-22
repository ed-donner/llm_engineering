"""
Run the Radio Africa Group Advanced Chatbot
This script ensures all ports are free and launches the chatbot
"""

import os
import subprocess
import time
import sys

def kill_processes_on_ports():
    """Kill all processes using Gradio ports"""
    print("🔍 Checking for processes using Gradio ports...")
    
    # Check for processes on common Gradio ports
    ports_to_check = [7860, 7861, 7862, 7863, 7864, 7865, 7866, 7867, 7868, 7869, 7870, 7871, 7872, 7873, 7874, 7875, 7876, 7877, 7878, 7879]
    
    for port in ports_to_check:
        try:
            # Find process using the port
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        try:
                            print(f"🔄 Killing process {pid} using port {port}")
                            subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                        except:
                            pass
        except:
            pass
    
    print("✅ Port cleanup completed!")

def find_free_port(start_port=7860):
    """Find a free port starting from the given port"""
    import socket
    
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def main():
    """Main function to run the chatbot"""
    print("🚀 Starting Radio Africa Group Advanced Chatbot...")
    
    # Kill any existing processes
    kill_processes_on_ports()
    
    # Find a free port
    free_port = find_free_port(7860)
    if not free_port:
        print("❌ No free ports available!")
        return
    
    print(f"✅ Using port {free_port}")
    
    # Set environment variable for Gradio
    os.environ['GRADIO_SERVER_PORT'] = str(free_port)
    
    # Import and run the chatbot
    try:
        # Change to the correct directory
        os.chdir('week2/community-contributions/week2-assignment-Joshua')
        
        # Import the chatbot
        from radio_africa_advanced_chatbot import main as chatbot_main
        
        print("🎯 Launching Radio Africa Group Advanced Chatbot...")
        print(f"🌐 Interface will be available at: http://127.0.0.1:{free_port}")
        
        # Run the chatbot
        chatbot_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please make sure you're in the correct directory and all dependencies are installed.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
