#!/usr/bin/env python3
"""
Installation script for YouTube Video Summarizer
This script installs all required dependencies for the project using either UV or pip.
"""

import subprocess
import sys
import os
import shutil

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_uv_installed():
    """Check if UV is installed"""
    if shutil.which("uv"):
        print("✅ UV is already installed")
        return True
    else:
        print("❌ UV is not installed")
        return False

def install_uv():
    """Install UV package manager"""
    print("🔄 Installing UV...")
    try:
        # Try to install UV using pip first
        if not run_command(f"{sys.executable} -m pip install uv", "Installing UV via pip"):
            # Fallback to curl installation
            install_script = "curl -LsSf https://astral.sh/uv/install.sh | sh"
            if not run_command(install_script, "Installing UV via curl"):
                print("❌ Failed to install UV. Please install it manually:")
                print("   pip install uv")
                print("   or visit: https://github.com/astral-sh/uv")
                return False
        return True
    except Exception as e:
        print(f"❌ Error installing UV: {e}")
        return False

def choose_package_manager():
    """Let user choose between UV and pip"""
    print("\n📦 Choose your package manager:")
    print("1. UV (recommended - faster, better dependency resolution)")
    print("2. pip (traditional Python package manager)")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice == "1":
            return "uv"
        elif choice == "2":
            return "pip"
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

def install_dependencies_uv():
    """Install dependencies using UV"""
    print("🚀 Installing YouTube Video Summarizer dependencies with UV...")
    print("=" * 60)
    
    # Check if UV is installed, install if not
    if not check_uv_installed():
        if not install_uv():
            return False
    
    # Check if pyproject.toml exists
    pyproject_file = os.path.join(os.path.dirname(__file__), "pyproject.toml")
    if not os.path.exists(pyproject_file):
        print("❌ pyproject.toml not found. Please ensure you're in the project directory.")
        return False
    
    # Install dependencies using UV
    if not run_command("uv sync", "Installing dependencies with UV"):
        return False
    
    print("=" * 60)
    print("🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Create a .env file with your OpenAI API key:")
    print("   OPENAI_API_KEY=your_api_key_here")
    print("2. Run the script:")
    print("   uv run python youtube_video_summarizer.py")
    print("\n💡 For Jupyter notebook support, install with:")
    print("   uv sync --extra jupyter")
    print("\n💡 For development dependencies, install with:")
    print("   uv sync --extra dev")
    
    return True

def install_dependencies_pip():
    """Install dependencies using pip"""
    print("🚀 Installing YouTube Video Summarizer dependencies with pip...")
    print("=" * 60)
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install dependencies from requirements.txt
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_file):
        if not run_command(f"{sys.executable} -m pip install -r {requirements_file}", "Installing dependencies from requirements.txt"):
            return False
    else:
        # Install core dependencies individually
        core_deps = [
            "requests",
            "tiktoken", 
            "python-dotenv",
            "openai",
            "youtube-transcript-api",
            "beautifulsoup4"
        ]
        
        for dep in core_deps:
            if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
                return False
    
    print("=" * 60)
    print("🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Create a .env file with your OpenAI API key:")
    print("   OPENAI_API_KEY=your_api_key_here")
    print("2. Run the script:")
    print("   python youtube_video_summarizer.py")
    print("\n💡 For Jupyter notebook support, also install:")
    print("   pip install jupyter ipython")
    
    return True

def install_dependencies():
    """Install required dependencies using chosen package manager"""
    # Check Python version
    if not check_python_version():
        return False
    
    # Let user choose package manager
    package_manager = choose_package_manager()
    
    if package_manager == "uv":
        return install_dependencies_uv()
    else:
        return install_dependencies_pip()

def main():
    """Main installation function"""
    print("🎬 YouTube Video Summarizer - Installation Script")
    print("=" * 60)
    
    if install_dependencies():
        print("\n✅ All dependencies installed successfully!")
        print("🚀 You can now run the YouTube Video Summarizer!")
    else:
        print("\n❌ Installation failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
