# 📚 AIBooks - LLM-Ready Document & Ebook Ingestion System

**Version 1.0** | Deep Agentic Self-Learning Pipeline

---

## 🎯 Overview

AIBooks is a **highly accurate, self-improving, agentic pipeline** that converts documents and e-books into **clean, reliable, structured LLM-ready representations**. It combines state-of-the-art parsing (Docling), comprehensive metadata extraction (Calibre), and **6 cooperating AI agents** that learn and improve over time.

### Key Features

🆓 **FREE Local LLM Support (Ollama)**
- Run powerful AI models **completely free** on your machine!
- No API keys required, fully private
- Llama 3.1, Mistral, Phi3, and more
- **50-100% cost reduction** with intelligent provider switching

✨ **State-of-the-Art Parsing**
- Docling-based parsing with OCR fallback
- Multi-column detection, table extraction, figure extraction
- Supports PDF, EPUB, MOBI, AZW3, DOCX, RTF, TXT, HTML, and images

🎯 **Multi-Provider LLM Support**
- **OpenAI** (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku)
- **Groq** (Fast inference, very cheap)
- **Ollama** (Local models, FREE!)
- Automatic provider selection by task complexity

🤖 **6 Intelligent Agents**
- **Format Strategist** - Selects optimal parsing strategy
- **Metadata Intelligence** - Fuses and refines metadata from multiple sources
- **Text Quality Reinforcer** - Evaluates and improves text quality
- **Cost Optimizer** - Minimizes LLM costs while maintaining quality
- **Failure Recovery** - Handles parsing failures automatically
- **Pipeline Evolution** - Analyzes performance and suggests improvements

📊 **Comprehensive Metadata**
- Calibre metadata extraction (ISBN, author, title, series, tags)
- Docling front-page metadata
- Filename heuristics
- LLM-assisted refinement

💰 **Cost & Time Tracking**
- Every LLM call logged with cost and duration
- Daily budget management
- Automatic switch to free models when budget tight
- Cost optimization suggestions

🗄️ **SQLite Knowledge Base**
- All documents, metadata, and processing logs
- Agent learning patterns and heuristics
- Deduplication via SHA-256 hashing

📤 **Multiple Output Formats**
- Clean TXT (plain text)
- Structured Markdown (with chapters, TOC)
- JSON (full structure with tables, figures, metadata)

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AIBooks.git
cd AIBooks

# Install dependencies
pip install -e .

# Option A: FREE Setup (Ollama - no API keys!)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b

# Option B: Paid LLMs (OpenAI, Anthropic, Groq)
# Get API keys from providers
# Add to .env file

# Optional: Install Calibre (for metadata extraction)
# Ubuntu/Debian:
sudo apt-get install calibre

# macOS:
brew install calibre

# Configure
cp .env.example .env
# Edit .env with your choices
```

### Initialize Database

```bash
aibooks init
```

### Check Available Providers

```bash
# See what LLM providers you have configured
aibooks providers

# Test a provider
aibooks test-llm --provider ollama --model llama3.1:8b
```

### Ingest Documents

```bash
# Single file
aibooks ingest /path/to/book.pdf

# Multiple files
aibooks ingest book1.pdf book2.epub book3.mobi

# Entire directory (recursive)
aibooks ingest /path/to/books/

# With verbose logging
aibooks ingest -v /path/to/books/
```

### View Statistics

```bash
# Show pipeline statistics
aibooks stats

# Last 30 days
aibooks stats --days 30
```

### Pipeline Evolution

```bash
# Analyze performance and get suggestions
aibooks evolve

# Auto-apply safe improvements
aibooks evolve --auto-apply
```

---

## 📖 Architecture

```
┌───────────────────────┐
│   Input Documents     │
│ PDF, EPUB, MOBI, etc. │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  Format Strategist    │ ◄─── Agent 1
│  (Optimal Strategy)   │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│   Docling Parser      │ ◄─── State-of-the-art
│  + OCR + Vision       │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ Metadata Extraction   │
│ Calibre + Heuristics  │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ Metadata Intelligence │ ◄─── Agent 2
│  (Fusion + Refine)    │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  Text Quality Agent   │ ◄─── Agent 3
│  (Assess + Clean)     │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│   Cost Optimizer      │ ◄─── Agent 4
│  (Minimize LLM Cost)  │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  Output Generation    │
│  TXT, MD, JSON        │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│   SQLite Database     │
│ + Agent Learning      │
└───────────────────────┘
```

---

## 🛠️ Configuration

Edit `.env` to configure:

```bash
# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Cost Control
DAILY_COST_CAP=10.0
COST_WARNING_THRESHOLD=5.0

# Models
DEFAULT_LLM_MODEL=gpt-4o-mini
METADATA_LLM_MODEL=gpt-4o-mini
AGENT_LLM_MODEL=gpt-4o

# Processing
MAX_WORKERS=4
BATCH_SIZE=10
DOCLING_OCR_ENABLED=true
DOCLING_VISION_ENABLED=true

# Paths
DATABASE_PATH=./aibooks.db
OUTPUT_DIR=./output
```

---

## 📊 Database Schema

### `documents` Table

Stores all processed documents with metadata:

- **Metadata**: title, author, ISBN, publisher, publication_date, series, tags, language
- **File Info**: format, source_file, content_hash
- **Processed Content**: chapters_json, tables_json, docling_json
- **Statistics**: words, pages, created_at, updated_at

### `genai_usage_log` Table

Tracks every LLM API call:

- **Timing**: timestamp, duration_ms
- **Usage**: model, tokens_in, tokens_out, cost
- **Context**: step, document_id, payload_preview

### `agent_learning` Table

Stores learned patterns for continuous improvement:

- **Pattern**: agent_name, learning_type, pattern_key, pattern_value
- **Performance**: success_count, failure_count, confidence_score
- **Tracking**: created_at, updated_at, last_used_at

---

## 🤖 The 6 Agents Explained

### 1. Format Strategist Agent

**Purpose**: Selects the optimal parsing strategy based on file type, size, and past performance.

**Learns**:
- Which parsing methods work best for each format
- When to enable OCR vs direct text extraction
- Optimal settings for large files

**Example Decision**: "For this 150MB scanned PDF, use Docling with OCR enabled and process in 50-page chunks."

### 2. Metadata Intelligence Agent

**Purpose**: Fuses metadata from multiple sources and assesses quality.

**Learns**:
- Which metadata sources are most reliable
- Common filename → metadata patterns
- When LLM enhancement is worth the cost

**Example Decision**: "Title confidence is low (0.4), recommend LLM enhancement. ISBN is valid."

### 3. Text Quality Reinforcer Agent

**Purpose**: Evaluates extracted text quality and determines cleaning strategy.

**Learns**:
- OCR artifact patterns
- When aggressive cleaning is needed
- Text normalization rules

**Example Decision**: "High OCR artifact count detected (quality=0.52), apply aggressive cleaning with LLM assistance."

### 4. Cost Optimizer Agent

**Purpose**: Minimizes LLM costs while maintaining quality.

**Learns**:
- Which models give best quality/cost ratio for each task
- When to skip optional LLM calls
- Optimal batching strategies

**Example Decision**: "Daily budget 70% used. Use gpt-4o-mini for metadata, skip optional quality check."

### 5. Failure Recovery Agent

**Purpose**: Handles parsing failures and determines recovery strategy.

**Learns**:
- Which fallback methods work for different error types
- When to retry vs give up
- Alternative parser strategies

**Example Decision**: "OCR timeout error detected. Retry with reduced DPI and chunked processing."

### 6. Pipeline Evolution Agent

**Purpose**: Analyzes overall pipeline performance and suggests improvements.

**Learns**:
- Long-term cost trends
- Success rate patterns
- Format-specific optimizations

**Example Decision**: "Success rate dropped to 82%. Suggest reviewing failure recovery patterns for PDFs."

---

## 📤 Output Formats

### Plain Text (`output/txt/`)

Clean, normalized text with optional metadata header:

```
================================================================================
Title: The Great Gatsby
Author(s): F. Scott Fitzgerald
Published: 1925
ISBN: 9780743273565
================================================================================

Chapter 1

In my younger and more vulnerable years...
```

### Markdown (`output/md/`)

Structured Markdown with YAML front matter:

```markdown
---
title: "The Great Gatsby"
authors: ["F. Scott Fitzgerald"]
date: "1925"
isbn: "9780743273565"
---

## Table of Contents

1. [Chapter 1](#chapter-1)
2. [Chapter 2](#chapter-2)

## Chapter 1

In my younger and more vulnerable years...
```

### JSON (`output/json/`)

Complete structured data:

```json
{
  "document_id": 42,
  "metadata": {
    "title": "The Great Gatsby",
    "authors": ["F. Scott Fitzgerald"],
    "isbn": "9780743273565",
    "publication_date": "1925"
  },
  "text": "...",
  "word_count": 47094,
  "chapters": [...],
  "tables": [],
  "figures": []
}
```

---

## 💡 Advanced Usage

### Python API

```python
from aibooks.core.processor import DocumentProcessor
from pathlib import Path

# Initialize processor
processor = DocumentProcessor()

# Process single document
doc = processor.process_document(Path("book.pdf"))

print(f"Title: {doc.title}")
print(f"Author: {doc.author}")
print(f"Pages: {doc.pages}")
print(f"Words: {doc.words}")

# Process batch
docs = processor.process_batch([
    Path("book1.pdf"),
    Path("book2.epub"),
])

# Get cost summary
cost = processor.get_daily_cost_summary()
print(f"Daily spend: ${cost['daily_spend']:.2f}")

# Analyze performance
analysis = processor.analyze_pipeline_performance(days=7)
print(f"Success rate: {analysis['analysis']['success_rate']:.1%}")
```

### Custom Agent Configuration

Access agents directly for fine-tuned control:

```python
from aibooks.agents.orchestrator import AgentOrchestrator
from aibooks.db.database import get_db

db = get_db()
with db.session_scope() as session:
    agents = AgentOrchestrator(session)

    # Get custom parsing strategy
    strategy = agents.get_parsing_strategy(
        file_path=Path("document.pdf"),
        format_type="pdf",
        file_size=5_000_000
    )

    # Optimize LLM usage
    llm_decision = agents.optimize_llm_usage(
        step="metadata_enhancement",
        estimated_tokens=2000,
        daily_budget=10.0
    )
```

---

## 🔧 Troubleshooting

### Calibre Not Found

```bash
# Install Calibre
sudo apt-get install calibre  # Ubuntu/Debian
brew install calibre          # macOS

# Or specify custom path in .env
CALIBRE_PATH=/custom/path/to/ebook-meta
```

### High Costs

```bash
# Reduce daily budget
DAILY_COST_CAP=5.0

# Use cheaper models
DEFAULT_LLM_MODEL=gpt-4o-mini
METADATA_LLM_MODEL=gpt-4o-mini

# Analyze cost breakdown
aibooks stats
aibooks evolve
```

### Low Success Rate

```bash
# Enable verbose logging
aibooks ingest -v /path/to/books/

# Check failure patterns in database
sqlite3 aibooks.db "SELECT * FROM agent_learning WHERE agent_name='failure_recovery'"

# Run evolution analysis
aibooks evolve
```

---

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=aibooks --cov-report=html

# Specific test
pytest tests/test_parser.py
```

---

## 🗺️ Roadmap

### v1.1 (Next Release)

- [ ] Web UI (React + FastAPI)
- [ ] Real-time progress monitoring
- [ ] LLM-assisted metadata enhancement
- [ ] Multi-language support improvements

### v2.0 (Future)

- [ ] Semantic chunking for RAG
- [ ] Automatic embedding generation
- [ ] On-device inference (Llama 3.1)
- [ ] GPU acceleration
- [ ] Export to Calibre library
- [ ] Mobile reader sync

---

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Docling** - State-of-the-art document parsing
- **Calibre** - Comprehensive ebook metadata extraction
- **LangGraph** - Agent orchestration framework
- **OpenAI & Anthropic** - LLM capabilities

---

## 📧 Contact

For questions, issues, or suggestions:

- **GitHub Issues**: [Report a bug](https://github.com/yourusername/AIBooks/issues)
- **Email**: your.email@example.com

---

**Made with ❤️ for the AI and ebook community**
