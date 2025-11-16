# 🚀 Quick Start Guide

Get up and running with AIBooks in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- (Optional) Calibre for ebook metadata extraction

## Installation

### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/AIBooks.git
cd AIBooks

# Run the installation script
bash scripts/install.sh
```

The script will:
- Create a virtual environment
- Install all dependencies
- Initialize the database
- Create a `.env` file from template

### Option 2: Manual Installation

```bash
# Clone and navigate
git clone https://github.com/yourusername/AIBooks.git
cd AIBooks

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install AIBooks
pip install -e .

# Create .env file
cp .env.example .env

# Initialize database
aibooks init
```

## Configuration

Edit `.env` and add your API keys:

```bash
# Required for LLM features
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Adjust cost limits
DAILY_COST_CAP=10.0
```

## Install Calibre (Optional but Recommended)

For best metadata extraction results:

```bash
# Ubuntu/Debian
sudo apt-get install calibre

# macOS
brew install calibre

# Windows
# Download from: https://calibre-ebook.com/download
```

## First Document

Process your first document:

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Ingest a single file
aibooks ingest /path/to/your/book.pdf

# Or process an entire directory
aibooks ingest /path/to/books/
```

## View Results

Check your processed documents:

```bash
# View statistics
aibooks stats

# Check output files
ls output/txt/    # Plain text
ls output/md/     # Markdown
ls output/json/   # JSON with full structure
```

## What's Next?

1. **Process More Documents**: `aibooks ingest` supports PDF, EPUB, MOBI, DOCX, and more
2. **Monitor Costs**: `aibooks stats` shows LLM usage and costs
3. **Optimize Pipeline**: `aibooks evolve` analyzes performance and suggests improvements
4. **Read the Docs**: Check `README.md` for advanced features

## Troubleshooting

### Dependencies Not Installed

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database Issues

```bash
# Reset database
aibooks init --reset
```

### Calibre Not Found

```bash
# Check if installed
which ebook-meta

# If not found, install calibre (see above)
```

### Import Errors

Make sure you're in the virtual environment:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Getting Help

- **CLI Help**: `aibooks --help`
- **Command Help**: `aibooks ingest --help`
- **Issues**: https://github.com/yourusername/AIBooks/issues
- **Documentation**: See `README.md`

## Validation

Run the validation script to ensure everything is working:

```bash
bash scripts/validate.sh
```

---

**Happy Reading! 📚**
