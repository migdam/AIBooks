#!/bin/bash
# Installation script for AIBooks

set -e

echo "🚀 AIBooks Installation Script"
echo "================================"
echo

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.10+ required (found $python_version)"
    exit 1
fi

echo "✅ Python $python_version found"
echo

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"
echo

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo "✅ pip upgraded"
echo

# Install dependencies
echo "Installing AIBooks dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo

# Install AIBooks in development mode
echo "Installing AIBooks..."
pip install -e .
echo "✅ AIBooks installed"
echo

# Check for Calibre
echo "Checking for Calibre..."
if command -v ebook-meta &> /dev/null; then
    echo "✅ Calibre found: $(which ebook-meta)"
else
    echo "⚠️  Warning: Calibre not found"
    echo "   Install with:"
    echo "   - Ubuntu/Debian: sudo apt-get install calibre"
    echo "   - macOS: brew install calibre"
    echo "   - Windows: Download from https://calibre-ebook.com/download"
fi
echo

# Create .env file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
else
    echo "ℹ️  .env file already exists"
fi
echo

# Initialize database
echo "Initializing database..."
aibooks init
echo "✅ Database initialized"
echo

echo "🎉 Installation complete!"
echo
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Edit .env file with your API keys"
echo "3. Start ingesting documents: aibooks ingest /path/to/books/"
echo
echo "For help: aibooks --help"
