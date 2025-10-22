"""
Simple launch script for Radio Africa Group Chatbot
Handles port conflicts and launches the chatbot
"""

import os
import sys
import subprocess
import time
import socket

def kill_gradio_processes():
    """Kill all Gradio processes"""
    print("🔄 Killing existing Gradio processes...")
    
    try:
        # Get all processes using ports 7860-7890
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        
        pids_to_kill = set()
        for line in result.stdout.split('\n'):
            for port in range(7860, 7890):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        pids_to_kill.add(pid)
        
        # Kill all identified processes
        for pid in pids_to_kill:
            try:
                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                print(f"✅ Killed process {pid}")
            except:
                pass
                
    except Exception as e:
        print(f"⚠️  Error: {e}")

def find_free_port():
    """Find a free port"""
    for port in range(7860, 8000):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def main():
    """Main function"""
    print("🚀 Radio Africa Group Advanced Chatbot")
    print("=" * 50)
    
    # Kill existing processes
    kill_gradio_processes()
    time.sleep(2)
    
    # Find free port
    free_port = find_free_port()
    if not free_port:
        print("❌ No free ports available!")
        return
    
    print(f"✅ Using port: {free_port}")
    
    # Set environment variable
    os.environ['GRADIO_SERVER_PORT'] = str(free_port)
    
    print(f"🌐 Interface will be available at: http://127.0.0.1:{free_port}")
    print("\n📋 Available features:")
    print("   - Model switching (GPT/Claude)")
    print("   - Web scraping from radioafricagroup.co.ke")
    print("   - Audio input/output support")
    print("   - Advanced tool integration")
    print("   - Streaming responses")
    print("   - Comprehensive database management")
    
    print("\n🎯 You can now run the notebook or Python script!")
    print("   The ports are now free and ready to use.")

if __name__ == "__main__":
    main()
