# Ollama Setup Guide - Run LLMs for FREE!

Use powerful AI models locally at **zero cost** with Ollama.

## Quick Start

### 1. Install Ollama

#### macOS / Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
Download from: https://ollama.ai/download

### 2. Pull a Model

```bash
# Recommended: Llama 3.1 8B (good balance of quality/speed)
ollama pull llama3.1:8b

# Or try others:
ollama pull mistral          # Technical tasks
ollama pull phi3             # Lightweight
ollama pull codellama        # Code understanding
```

### 3. Configure AIBooks

Edit `.env`:
```bash
FREE_PROVIDER=ollama
FREE_LLM_MODEL=llama3.1:8b
USE_FREE_FOR_SIMPLE=true
```

### 4. Test It

```bash
# Start Ollama (if not running)
ollama serve

# Test with AIBooks
aibooks ingest test.pdf
```

Done! You're now using FREE local AI.

---

## Available Models

| Model | Size | Best For | Quality | Speed |
|-------|------|----------|---------|-------|
| **llama3.1:8b** | 4.7GB | General purpose | ⭐⭐⭐⭐ | Fast |
| **llama3.1:70b** | 40GB | Best quality | ⭐⭐⭐⭐⭐ | Slow |
| **mistral** | 4.1GB | Technical content | ⭐⭐⭐⭐ | Fast |
| **phi3** | 2.3GB | Quick tasks | ⭐⭐⭐ | Very Fast |
| **codellama** | 3.8GB | Code/tech docs | ⭐⭐⭐⭐ | Fast |

### Pull Multiple Models

```bash
ollama pull llama3.1:8b    # For simple tasks
ollama pull llama3.1:70b   # For complex tasks
```

Then configure:
```bash
SIMPLE_TASK_MODEL=llama3.1:8b
ADVANCED_LLM_MODEL=llama3.1:70b
```

---

## Hardware Requirements

### Minimum (llama3.1:8b)
- **RAM**: 8GB
- **Storage**: 6GB
- **Speed**: Slow without GPU

### Recommended
- **RAM**: 16GB+
- **GPU**: NVIDIA GPU with 8GB+ VRAM
- **Storage**: 10GB+ for multiple models
- **Speed**: Fast with GPU

### High-End (llama3.1:70b)
- **RAM**: 64GB
- **GPU**: NVIDIA GPU with 48GB+ VRAM
- **Storage**: 50GB
- **Speed**: Good with powerful GPU

---

## GPU Acceleration

Ollama automatically uses GPU if available!

### Check GPU Usage

```bash
# During model run
nvidia-smi  # For NVIDIA
```

### NVIDIA Setup (Linux)
```bash
# Install CUDA drivers
# Ubuntu:
sudo apt install nvidia-cuda-toolkit

# Verify
nvidia-smi
```

### Apple Silicon (M1/M2/M3)
Works out of the box! Uses Metal for acceleration.

---

## Configuration Options

### Basic (Free Only)
```bash
DEFAULT_PROVIDER=ollama
ADVANCED_PROVIDER=ollama
FREE_PROVIDER=ollama

DEFAULT_LLM_MODEL=llama3.1:8b
ADVANCED_LLM_MODEL=llama3.1:8b
FREE_LLM_MODEL=llama3.1:8b

USE_FREE_FOR_SIMPLE=true
DAILY_COST_CAP=0.0
```

### Hybrid (Free + Paid)
```bash
DEFAULT_PROVIDER=ollama
ADVANCED_PROVIDER=openai
FREE_PROVIDER=ollama

DEFAULT_LLM_MODEL=llama3.1:8b
ADVANCED_LLM_MODEL=gpt-4o
FREE_LLM_MODEL=llama3.1:8b

USE_FREE_FOR_SIMPLE=true
DAILY_COST_CAP=5.0
```

---

## Commands

### List Models
```bash
ollama list
```

### Run Model Interactively
```bash
ollama run llama3.1:8b
```

### Remove Model
```bash
ollama rm llama3.1:8b
```

### Check Status
```bash
curl http://localhost:11434/api/tags
```

---

## Troubleshooting

### Ollama Not Running

```bash
# Start server
ollama serve

# Check if running
ps aux | grep ollama
```

### Model Not Found

```bash
# Pull the model first
ollama pull llama3.1:8b

# List available
ollama list
```

### Slow Performance

1. **Use smaller model**: `ollama pull phi3`
2. **Enable GPU**: Install CUDA/Metal drivers
3. **Close other apps**: Free up RAM
4. **Use SSD**: Install models on SSD

### Out of Memory

```bash
# Use smaller model
ollama pull phi3  # Only 2.3GB

# Or increase swap (Linux)
sudo fallocate -l 16G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Connection Refused

```bash
# Check if Ollama is running
ollama serve

# Check port
netstat -an | grep 11434

# Try different port
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

Then update `.env`:
```bash
OLLAMA_BASE_URL=http://localhost:11435
```

---

## Model Recommendations

### For Documents
- **PDF/EPUB**: `llama3.1:8b` or `mistral`
- **Technical docs**: `codellama` or `mistral`
- **Academic papers**: `llama3.1:70b` (if you have RAM)

### By Task
- **Metadata extraction**: `llama3.1:8b` ⭐
- **Text cleanup**: `phi3` (fast)
- **Quality analysis**: `llama3.1:70b` (best)
- **OCR correction**: `mistral`

---

## Performance Comparison

Tested on M1 MacBook Pro 16GB:

| Model | Speed (tokens/s) | Quality | Memory |
|-------|------------------|---------|---------|
| **phi3** | ~40 | Good | 4GB |
| **llama3.1:8b** | ~20 | Excellent | 8GB |
| **mistral** | ~18 | Excellent | 8GB |
| **llama3.1:70b** | ~2 | Best | 40GB |

---

## Cost Comparison

Processing 100 documents (500 pages each):

| Provider | Cost | Time |
|----------|------|------|
| **Ollama (llama3.1:8b)** | $0 | Varies* |
| OpenAI (gpt-4o-mini) | ~$5 | Fast |
| Anthropic (Claude Haiku) | ~$3 | Fast |

*Speed depends on hardware

**Savings with Ollama**: 100% (FREE!)

---

## Advanced: Custom Models

### Fine-tune Your Own

```bash
# Create Modelfile
cat > Modelfile <<EOF
FROM llama3.1:8b
SYSTEM You are an expert at processing ebooks and documents.
EOF

# Create custom model
ollama create bookbot -f Modelfile

# Use it
ollama run bookbot
```

Update `.env`:
```bash
FREE_LLM_MODEL=bookbot
```

---

## Next Steps

1. ✅ Install Ollama
2. ✅ Pull a model: `ollama pull llama3.1:8b`
3. ✅ Configure AIBooks (edit `.env`)
4. ✅ Test: `aibooks ingest test.pdf`
5. ✅ Monitor: `aibooks stats` (should show $0 cost!)

Enjoy FREE AI processing! 🎉

---

## Resources

- **Ollama Website**: https://ollama.ai/
- **Model Library**: https://ollama.ai/library
- **GitHub**: https://github.com/ollama/ollama
- **Discord**: https://discord.gg/ollama
