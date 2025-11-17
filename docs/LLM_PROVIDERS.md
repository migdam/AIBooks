# LLM Provider Guide

AIBooks supports multiple LLM providers, including **FREE local models** via Ollama!

## Supported Providers

### 🆓 Ollama (FREE - Local)

Run powerful AI models locally on your machine at **zero cost**!

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended model
ollama pull llama3.1:8b

# Verify it's running
ollama list
```

**Recommended Models:**
- `llama3.1:8b` - General purpose, good quality (4.7GB)
- `llama3.1:70b` - Best quality, slower (40GB)
- `mistral` - Excellent for technical content (4.1GB)
- `phi3` - Small and fast (2.3GB)
- `codellama` - Optimized for code (3.8GB)

**Pros:**
- ✅ Completely FREE
- ✅ No API keys needed
- ✅ Privacy - data never leaves your machine
- ✅ No rate limits
- ✅ Works offline

**Cons:**
- ❌ Requires local resources (RAM, CPU/GPU)
- ❌ Slower than cloud APIs (unless you have GPU)
- ❌ Quality may be lower for complex tasks

**Configuration:**
```bash
# .env
FREE_PROVIDER=ollama
FREE_LLM_MODEL=llama3.1:8b
SIMPLE_TASK_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
USE_FREE_FOR_SIMPLE=true
```

---

### 💰 OpenAI (Paid)

High-quality models from OpenAI.

**Models:**
- `gpt-4o` - Best quality ($2.50 / 1M input tokens)
- `gpt-4o-mini` - Best value ($0.15 / 1M input tokens) ⭐ **Recommended**
- `gpt-4-turbo` - Fast & capable ($10 / 1M input tokens)
- `gpt-3.5-turbo` - Cheapest ($0.50 / 1M input tokens)

**Setup:**
1. Get API key: https://platform.openai.com/api-keys
2. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   DEFAULT_PROVIDER=openai
   DEFAULT_LLM_MODEL=gpt-4o-mini
   ```

---

### 💰 Anthropic Claude (Paid)

High-quality, safety-focused models.

**Models:**
- `claude-3-5-sonnet` - Latest, best ($3 / 1M input tokens) ⭐
- `claude-3-opus` - Most capable ($15 / 1M input tokens)
- `claude-3-haiku` - Fastest, cheapest ($0.25 / 1M input tokens)

**Setup:**
1. Get API key: https://console.anthropic.com/
2. Add to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   DEFAULT_PROVIDER=anthropic
   DEFAULT_LLM_MODEL=claude-3-5-sonnet
   ```

---

### 🚀 Groq (Paid - FAST & Cheap!)

Super-fast inference with free tier available!

**Models:**
- `llama-3.1-70b-versatile` - Best quality (Llama 3.1 70B)
- `llama-3.1-8b-instant` - Fast (Llama 3.1 8B)
- `mixtral-8x7b-32768` - Long context (Mixtral)

**Pricing:** ~$0.27 / 1M tokens (very cheap!)

**Setup:**
1. Get API key: https://console.groq.com/
2. Install: `pip install groq`
3. Add to `.env`:
   ```bash
   GROQ_API_KEY=gsk_...
   DEFAULT_PROVIDER=groq
   DEFAULT_LLM_MODEL=llama-3.1-8b-instant
   ```

---

## Configuration Strategies

### Strategy 1: FREE Everything (Ollama Only)

Perfect for learning, testing, or privacy-focused use.

```bash
# .env
DEFAULT_PROVIDER=ollama
ADVANCED_PROVIDER=ollama
FREE_PROVIDER=ollama

DEFAULT_LLM_MODEL=llama3.1:8b
ADVANCED_LLM_MODEL=llama3.1:70b
FREE_LLM_MODEL=llama3.1:8b

USE_FREE_FOR_SIMPLE=true
DAILY_COST_CAP=0.0
```

**Cost:** $0.00
**Requirements:** Ollama installed, ~8GB RAM minimum

---

### Strategy 2: Hybrid (Free for Simple, Paid for Complex)

Best value - use free Ollama for simple tasks, paid APIs for complex analysis.

```bash
# .env
DEFAULT_PROVIDER=openai
ADVANCED_PROVIDER=openai
FREE_PROVIDER=ollama

DEFAULT_LLM_MODEL=gpt-4o-mini
ADVANCED_LLM_MODEL=gpt-4o
FREE_LLM_MODEL=llama3.1:8b
SIMPLE_TASK_MODEL=llama3.1:8b

USE_FREE_FOR_SIMPLE=true
DAILY_COST_CAP=5.0
```

**Cost:** ~$1-5/day depending on usage
**Best for:** Production use with cost optimization

---

### Strategy 3: Premium Quality (Paid Only)

Maximum quality, no compromises.

```bash
# .env
DEFAULT_PROVIDER=anthropic
ADVANCED_PROVIDER=anthropic

DEFAULT_LLM_MODEL=claude-3-5-sonnet
ADVANCED_LLM_MODEL=claude-3-opus

USE_FREE_FOR_SIMPLE=false
DAILY_COST_CAP=20.0
```

**Cost:** $5-20/day
**Best for:** Professional use requiring highest quality

---

### Strategy 4: Fast & Cheap (Groq)

Fast inference with low costs.

```bash
# .env
DEFAULT_PROVIDER=groq
ADVANCED_PROVIDER=groq
FREE_PROVIDER=ollama

DEFAULT_LLM_MODEL=llama-3.1-8b-instant
ADVANCED_LLM_MODEL=llama-3.1-70b-versatile
FREE_LLM_MODEL=llama3.1:8b

USE_FREE_FOR_SIMPLE=true
DAILY_COST_CAP=2.0
```

**Cost:** ~$0.50-2/day
**Best for:** High volume with budget constraints

---

## Task Classification

AIBooks automatically selects the best provider based on task complexity:

### Simple Tasks (uses FREE_MODEL if enabled)
- Format detection
- Simple metadata extraction
- Quick validation

### Moderate Tasks (uses DEFAULT_MODEL)
- Metadata enhancement
- Text cleanup
- Chapter detection

### Complex Tasks (uses ADVANCED_MODEL)
- Metadata inference from content
- Quality analysis
- OCR correction
- Failure recovery

---

## Cost Optimization Tips

### 1. Use Free Models for Simple Tasks

```bash
USE_FREE_FOR_SIMPLE=true
FREE_LLM_MODEL=llama3.1:8b
```

This can reduce costs by 50-70%!

### 2. Set Daily Budget

```bash
DAILY_COST_CAP=5.0
COST_WARNING_THRESHOLD=3.0
```

System will switch to free models when budget is running low.

### 3. Use Cheaper Models for Non-Critical Tasks

```bash
METADATA_LLM_MODEL=gpt-4o-mini
CLEANUP_LLM_MODEL=llama3.1:8b
```

### 4. Monitor Costs

```bash
# Check daily spending
aibooks stats

# Analyze cost breakdown
aibooks evolve
```

---

## Provider Comparison

| Provider | Quality | Speed | Cost | Local | Best For |
|----------|---------|-------|------|-------|----------|
| **Ollama** | Good | Slow* | FREE | ✅ | Privacy, learning, simple tasks |
| **OpenAI (gpt-4o-mini)** | Excellent | Fast | Low | ❌ | General production use |
| **OpenAI (gpt-4o)** | Best | Fast | High | ❌ | Complex analysis |
| **Anthropic (Haiku)** | Good | Very Fast | Low | ❌ | Simple tasks, budget |
| **Anthropic (Sonnet)** | Excellent | Fast | Medium | ❌ | Professional use |
| **Groq** | Good | Very Fast | Very Low | ❌ | High volume |

*Ollama speed depends on hardware (much faster with GPU)

---

## Requirements

### Ollama
```bash
# Install
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.1:8b
```

### OpenAI
```bash
pip install openai
```

### Anthropic
```bash
pip install anthropic
```

### Groq
```bash
pip install groq
```

---

## Troubleshooting

### Ollama Not Available

**Check if running:**
```bash
ollama list
```

**Start service:**
```bash
# macOS/Linux
ollama serve

# Check API
curl http://localhost:11434/api/tags
```

### Provider Not Working

**Check available providers:**
```python
from aibooks.core import LLMFactory
print(LLMFactory.get_available_providers())
```

### High Costs

1. Enable free models: `USE_FREE_FOR_SIMPLE=true`
2. Lower daily cap: `DAILY_COST_CAP=2.0`
3. Use cheaper models: `DEFAULT_LLM_MODEL=gpt-4o-mini`
4. Check spending: `aibooks stats`

---

## Example Configurations

### Beginner (Free)
```bash
DEFAULT_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3.1:8b
USE_FREE_FOR_SIMPLE=true
DAILY_COST_CAP=0
```

### Budget-Conscious ($1-2/day)
```bash
DEFAULT_PROVIDER=groq
FREE_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama-3.1-8b-instant
USE_FREE_FOR_SIMPLE=true
DAILY_COST_CAP=2.0
```

### Professional ($5-10/day)
```bash
DEFAULT_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4o-mini
ADVANCED_LLM_MODEL=gpt-4o
USE_FREE_FOR_SIMPLE=false
DAILY_COST_CAP=10.0
```

### Enterprise (Unlimited)
```bash
DEFAULT_PROVIDER=anthropic
DEFAULT_LLM_MODEL=claude-3-5-sonnet
ADVANCED_LLM_MODEL=claude-3-opus
USE_FREE_FOR_SIMPLE=false
DAILY_COST_CAP=100.0
```

---

## Next Steps

1. Choose your strategy
2. Update `.env` configuration
3. Test with: `aibooks ingest /path/to/test.pdf`
4. Monitor costs: `aibooks stats`
5. Optimize: `aibooks evolve`

For more help, see `README.md` or open an issue on GitHub.
