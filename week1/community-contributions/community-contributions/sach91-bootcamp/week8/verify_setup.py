"""
Setup Verification Script for KnowledgeHub
Run this to check if everything is configured correctly
"""
import sys
import os

print("🔍 KnowledgeHub Setup Verification\n")
print("=" * 60)

# Check Python version
print(f"✓ Python version: {sys.version}")
print(f"✓ Python executable: {sys.executable}")
print(f"✓ Current directory: {os.getcwd()}")
print()

# Check directory structure
print("📁 Checking directory structure...")
required_dirs = ['agents', 'models', 'utils']
for dir_name in required_dirs:
    if os.path.isdir(dir_name):
        init_file = os.path.join(dir_name, '__init__.py')
        if os.path.exists(init_file):
            print(f"  ✓ {dir_name}/ exists with __init__.py")
        else:
            print(f"  ⚠️  {dir_name}/ exists but missing __init__.py")
    else:
        print(f"  ❌ {dir_name}/ directory not found")
print()

# Check required files
print("📄 Checking required files...")
required_files = ['app.py', 'requirements.txt']
for file_name in required_files:
    if os.path.exists(file_name):
        print(f"  ✓ {file_name} exists")
    else:
        print(f"  ❌ {file_name} not found")
print()

# Try importing modules
print("📦 Testing imports...")
errors = []

try:
    from utils import OllamaClient, EmbeddingModel, DocumentParser
    print("  ✓ utils module imported successfully")
except ImportError as e:
    print(f"  ❌ Cannot import utils: {e}")
    errors.append(str(e))

try:
    from models import Document, DocumentChunk, SearchResult, Summary
    print("  ✓ models module imported successfully")
except ImportError as e:
    print(f"  ❌ Cannot import models: {e}")
    errors.append(str(e))

try:
    from agents import (
        IngestionAgent, QuestionAgent, SummaryAgent,
        ConnectionAgent, ExportAgent
    )
    print("  ✓ agents module imported successfully")
except ImportError as e:
    print(f"  ❌ Cannot import agents: {e}")
    errors.append(str(e))

print()

# Check dependencies
print("📚 Checking Python dependencies...")
required_packages = [
    'gradio', 'chromadb', 'sentence_transformers', 
    'requests', 'numpy', 'tqdm'
]

missing_packages = []
for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        print(f"  ✓ {package} installed")
    except ImportError:
        print(f"  ❌ {package} not installed")
        missing_packages.append(package)

print()

# Check Ollama
print("🤖 Checking Ollama...")
try:
    import requests
    response = requests.get('http://localhost:11434/api/tags', timeout=2)
    if response.status_code == 200:
        print("  ✓ Ollama is running")
        models = response.json().get('models', [])
        if models:
            print(f"  ✓ Available models: {[m['name'] for m in models]}")
            if any('llama3.2' in m['name'] for m in models):
                print("  ✓ llama3.2 model found")
            else:
                print("  ⚠️  llama3.2 model not found. Run: ollama pull llama3.2")
        else:
            print("  ⚠️  No models found. Run: ollama pull llama3.2")
    else:
        print("  ⚠️  Ollama responded but with error")
except Exception as e:
    print(f"  ❌ Cannot connect to Ollama: {e}")
    print("     Start Ollama with: ollama serve")

print()
print("=" * 60)

# Final summary
if errors or missing_packages:
    print("\n⚠️  ISSUES FOUND:\n")
    if errors:
        print("Import Errors:")
        for error in errors:
            print(f"  - {error}")
    if missing_packages:
        print("\nMissing Packages:")
        print(f"  Run: pip install {' '.join(missing_packages)}")
    print("\n💡 Fix these issues before running app.py")
else:
    print("\n✅ All checks passed! You're ready to run:")
    print("   python app.py")
    
print()
