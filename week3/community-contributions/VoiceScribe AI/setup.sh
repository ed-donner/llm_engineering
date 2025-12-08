#!/bin/bash

# VoiceScribe AI - Setup Script
# This script automates the installation and setup process

echo "=========================================="
echo "🎤 VoiceScribe AI - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "   Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📥 Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

# Check for GPU support
echo ""
echo "🔍 Checking for GPU support..."
python3 -c "import torch; print('   GPU Available:', torch.cuda.is_available()); print('   GPU Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "🚀 To run VoiceScribe AI:"
echo "   1. Activate the virtual environment:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "      venv\\Scripts\\activate"
else
    echo "      source venv/bin/activate"
fi
echo "   2. Run the application:"
echo "      python voicescribe_ai.py"
echo ""
echo "📚 For more information, see README.md"
echo ""
