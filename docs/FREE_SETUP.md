# 🆓 FREE Setup Guide - Use AIBooks at Zero Cost!

Process unlimited documents with **completely free** local AI models.

## Quick Start (5 Minutes)

### 1. Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from: https://ollama.ai/download
```

### 2. Pull a Model

```bash
ollama pull llama3.1:8b
```

Wait ~5 minutes for the 4.7GB download.

### 3. Configure AIBooks

Edit `.env`:

```bash
# Use FREE provider for everything
DEFAULT_PROVIDER=ollama
ADVANCED_PROVIDER=ollama
FREE_PROVIDER=ollama

# Use FREE models
DEFAULT_LLM_MODEL=llama3.1:8b
ADVANCED_LLM_MODEL=llama3.1:8b
FREE_LLM_MODEL=llama3.1:8b

# Ensure free mode is enabled
USE_FREE_FOR_SIMPLE=true

# Set budget to $0 (enforce free only)
DAILY_COST_CAP=0.0
```

### 4. Test It

```bash
# Check Ollama is available
aibooks providers

# Test the model
aibooks test-llm --provider ollama --model llama3.1:8b

# Process a document
aibooks ingest test.pdf

# Check costs (should be $0!)
aibooks stats
```

Done! You're now running AIBooks completely free! 🎉

---

## What You Get for FREE

✅ **Unlimited Processing**: No API limits  
✅ **Full Privacy**: Data never leaves your machine  
✅ **All Features**: Same functionality as paid versions  
✅ **Multiple Models**: Llama 3.1, Mistral, Phi3, etc.  
✅ **No API Keys**: Just install and run  

---

## Hardware Requirements

### Minimum (Works but Slow)
- **RAM**: 8GB
- **Storage**: 6GB for llama3.1:8b
- **CPU**: Any modern processor
- **Speed**: ~2-5 tokens/sec

### Recommended (Good Performance)
- **RAM**: 16GB
- **Storage**: 10GB (for multiple models)
- **GPU**: NVIDIA GPU or Apple Silicon (M1/M2/M3)
- **Speed**: ~20-40 tokens/sec

### Optimal (Fast Processing)
- **RAM**: 32GB+
- **Storage**: 50GB
- **GPU**: NVIDIA RTX 3080 or better / M2 Pro/Max
- **Speed**: 40-80 tokens/sec

---

## Model Recommendations for Free Setup

### For Most Users: llama3.1:8b ⭐
```bash
ollama pull llama3.1:8b
```
- **Size**: 4.7GB
- **Quality**: Excellent
- **Speed**: Good
- **Best for**: General purpose

### For Low-End Hardware: phi3
```bash
ollama pull phi3
```
- **Size**: 2.3GB
- **Quality**: Good
- **Speed**: Very fast
- **Best for**: Quick processing on limited hardware

### For Best Quality: llama3.1:70b
```bash
ollama pull llama3.1:70b
```
- **Size**: 40GB
- **Quality**: Best
- **Speed**: Slow (needs powerful GPU)
- **Best for**: High-quality analysis (if you have the hardware)

---

## Cost Comparison

Processing 1,000 documents per month:

| Provider | Setup | Monthly Cost |
|----------|-------|--------------|
| **Ollama (Free)** | llama3.1:8b | **$0.00** |
| OpenAI | gpt-4o-mini | $50-100 |
| Anthropic | claude-haiku | $30-80 |
| Groq | llama-3.1-8b | $10-30 |

**Savings with Ollama: 100%**

---

## Performance Tips

### 1. Use GPU Acceleration

**NVIDIA (Linux/Windows)**:
```bash
# Install CUDA toolkit
# Ollama will automatically use GPU

# Verify
nvidia-smi
```

**Apple Silicon (macOS)**:
Works automatically! No setup needed.

### 2. Use Smaller Models for Speed

```bash
# Fast for simple tasks
ollama pull phi3

# Configure
FREE_LLM_MODEL=phi3
SIMPLE_TASK_MODEL=phi3
```

### 3. Increase RAM/Swap (Linux)

```bash
# Add 16GB swap
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 4. Use SSD Storage

Install Ollama models on SSD for better performance:
```bash
# Check model location
ollama list

# Models stored in:
# macOS: ~/.ollama/models
# Linux: /usr/share/ollama/.ollama/models
```

---

## Monitoring Performance

### Check Model Speed

```bash
# Run interactive session
ollama run llama3.1:8b

# Type a message and watch tokens/sec
# Good: >10 tokens/sec
# Great: >30 tokens/sec
```

### Monitor Resource Usage

```bash
# CPU/RAM
top
htop

# GPU (NVIDIA)
nvidia-smi

# Disk space
ollama list
```

---

## Troubleshooting

### Slow Performance

**Solutions**:
1. Use smaller model: `ollama pull phi3`
2. Close other applications
3. Add more RAM/swap
4. Get GPU acceleration

### Out of Memory

**Solutions**:
1. Use phi3 instead (only 2.3GB)
2. Increase swap space
3. Close other apps
4. Upgrade RAM

### Ollama Not Found

```bash
# Check if installed
which ollama

# Start service
ollama serve

# Check status
ps aux | grep ollama
```

### Models Not Downloading

```bash
# Check disk space
df -h

# Try smaller model first
ollama pull phi3

# Check internet connection
curl https://ollama.ai
```

---

## Advanced: Multiple Models

Pull different models for different tasks:

```bash
# Fast model for simple tasks
ollama pull phi3

# General purpose
ollama pull llama3.1:8b

# Best quality (if you have RAM)
ollama pull llama3.1:70b
```

Configure:
```bash
SIMPLE_TASK_MODEL=phi3
DEFAULT_LLM_MODEL=llama3.1:8b
ADVANCED_LLM_MODEL=llama3.1:70b
```

---

## FAQ

### Q: Is it really free?
**A**: Yes! Completely free. No hidden costs, no API limits.

### Q: What's the catch?
**A**: You need local hardware (CPU/GPU). Quality may be slightly lower than GPT-4o.

### Q: Can I use it offline?
**A**: Yes! Once models are downloaded, works 100% offline.

### Q: Is my data private?
**A**: Yes! Everything runs locally. Data never leaves your machine.

### Q: How does quality compare?
**A**: Llama 3.1 8B ≈ GPT-3.5 quality. Llama 3.1 70B ≈ GPT-4 quality.

### Q: What if I need better quality sometimes?
**A**: Use hybrid setup - Ollama for simple tasks, paid API for complex tasks.

---

## Next Steps

1. ✅ Install Ollama
2. ✅ Pull llama3.1:8b
3. ✅ Configure AIBooks for free mode
4. ✅ Test: `aibooks test-llm --provider ollama`
5. ✅ Process documents: `aibooks ingest /path/to/books/`
6. ✅ Verify $0 cost: `aibooks stats`

**You're now processing documents for FREE!** 🎉

---

## Resources

- **Ollama Website**: https://ollama.ai/
- **Model Library**: https://ollama.ai/library
- **GitHub**: https://github.com/ollama/ollama
- **AIBooks Docs**: See `docs/LLM_PROVIDERS.md`
