# OpenRouter Setup Guide

Complete guide for setting up and using OpenRouter with Docling Hybrid OCR.

---

## Table of Contents

- [What is OpenRouter?](#what-is-openrouter)
- [Why OpenRouter?](#why-openrouter)
- [Getting an API Key](#getting-an-api-key)
- [Configuration](#configuration)
- [Available Models](#available-models)
- [Rate Limits and Pricing](#rate-limits-and-pricing)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## What is OpenRouter?

**OpenRouter** is a unified API gateway that provides access to multiple Large Language Models (LLMs) and Vision-Language Models (VLMs) through a single API interface.

**For Docling Hybrid OCR:**
- OpenRouter provides access to Nemotron Nano VLM (our default model)
- No local GPU required
- Simple API key authentication
- Pay-as-you-go pricing with free tier available

**Official Website:** https://openrouter.ai

---

## Why OpenRouter?

### Advantages

✅ **No GPU Required**
- Cloud-based inference
- Works on any machine (Windows, Mac, Linux)
- No CUDA or hardware setup needed

✅ **Free Tier Available**
- Free access to select models (including Nemotron Nano)
- Great for testing and small-scale use
- Easy upgrade path to paid tier

✅ **Easy Setup**
- Single API key for all models
- OpenAI-compatible API
- No complex configuration

✅ **Multiple Models**
- Switch between different VLMs
- Test which model works best for your documents
- Fallback to alternative models if needed

✅ **Reliable Infrastructure**
- Production-grade API
- Good uptime and performance
- Rate limiting and error handling

### When to Use OpenRouter

**Perfect For:**
- Testing and development
- Small to medium batch processing
- Users without GPU hardware
- Getting started quickly

**Consider Alternatives If:**
- Processing thousands of pages daily (use local vLLM)
- Offline processing required (use DeepSeek local)
- Specific latency requirements (use local inference)
- Cost is primary concern for large volumes (local may be cheaper)

---

## Getting an API Key

### Step 1: Create Account

1. Visit https://openrouter.ai
2. Click **"Sign Up"** in the top-right corner
3. Sign up using:
   - Google account (recommended)
   - Email and password
   - GitHub account

### Step 2: Verify Email

1. Check your email for verification link
2. Click the link to activate your account
3. Log in to OpenRouter dashboard

### Step 3: Generate API Key

1. Once logged in, navigate to **"API Keys"** in the sidebar
2. Click **"Create Key"**
3. Give your key a descriptive name (e.g., "docling-hybrid-dev")
4. Optional: Set usage limits for safety
5. Click **"Create"**
6. **Copy the key immediately** - it starts with `sk-or-v1-...`
7. **Important:** Store the key securely - you won't see it again!

### Step 4: (Optional) Add Credits

- Free tier includes some models at no cost
- For paid models or higher volume, add credits:
  - Click "Credits" in dashboard
  - Choose amount ($5 minimum)
  - Add payment method

---

## Configuration

### Method 1: Environment File (Recommended)

Create a `.env.local` file in your project directory:

```bash
# Copy example file
cp .env.example .env.local

# Edit with your key
nano .env.local
```

Add your API key:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
DOCLING_HYBRID_CONFIG=configs/local.toml
DOCLING_HYBRID_LOG_LEVEL=INFO
```

Load the environment:

```bash
source .env.local
```

### Method 2: openrouter_key File (Simple)

For quick local development:

```bash
# Create key file
echo 'sk-or-v1-your-actual-key-here' > openrouter_key

# Source environment setup
source ./scripts/setup_env.sh
```

**Important:** Add `openrouter_key` to `.gitignore` to prevent committing!

### Method 3: Direct Export (Testing)

For temporary testing:

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

Note: This only persists for current shell session.

### Method 4: System Environment (Production)

For production deployments:

**Linux/Mac (systemd service):**
```ini
# /etc/systemd/system/docling-hybrid.service
[Service]
Environment="OPENROUTER_API_KEY=sk-or-v1-..."
```

**Docker:**
```yaml
# docker-compose.yml
services:
  docling-hybrid:
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
```

**Kubernetes:**
```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: openrouter-secret
type: Opaque
stringData:
  api-key: sk-or-v1-...
```

### Verify Configuration

Check your API key is set:

```bash
# Should display your key
echo $OPENROUTER_API_KEY

# Should show "sk-or-v1-..."
```

Test with CLI:

```bash
# Should succeed if key is valid
docling-hybrid-ocr info

# Should show OpenRouter as available
docling-hybrid-ocr backends
```

---

## Available Models

### Default Model: Nemotron Nano

**Model ID:** `nvidia/nemotron-nano-12b-v2-vl:free`

**Specifications:**
- **Parameters:** 12 billion
- **Provider:** NVIDIA
- **Type:** Vision-Language Model
- **Context:** 8K tokens
- **Free Tier:** Yes (limited rate)

**Performance:**
- Good accuracy for most documents
- Fast inference (~2-5s per page)
- Handles tables and formulas reasonably well
- Suitable for production use

**Use Case:**
- General purpose OCR
- Mixed document types
- Budget-conscious deployments

### Alternative Models

You can use other models by modifying `configs/local.toml`:

```toml
[backends.nemotron-openrouter]
model = "your-preferred-model"
```

**Recommended Alternatives:**

1. **GPT-4 Vision** (Higher accuracy, paid)
   ```toml
   model = "openai/gpt-4-vision-preview"
   ```

2. **Claude 3 Opus** (Best quality, expensive)
   ```toml
   model = "anthropic/claude-3-opus"
   ```

3. **Gemini Pro Vision** (Good balance)
   ```toml
   model = "google/gemini-pro-vision"
   ```

Check OpenRouter's model list for latest options: https://openrouter.ai/models

---

## Rate Limits and Pricing

### Free Tier

**Nemotron Nano Free:**
- Rate Limit: ~10 requests/minute
- Daily Limit: Varies (check dashboard)
- Cost: $0

**Tips for Free Tier:**
- Start with `--max-pages 5` for testing
- Use `--dpi 150` to reduce request size
- Process documents during off-peak hours
- Monitor usage in dashboard

### Paid Tier

**Pricing Model:**
- Pay per token (input + output)
- Varies by model (Nemotron Nano is cheapest)
- Typical cost: $0.01 - $0.10 per page

**Example Costs (Nemotron Nano):**
- 10-page document: ~$0.05 - $0.20
- 100-page document: ~$0.50 - $2.00
- 1000-page document: ~$5.00 - $20.00

**Cost Optimization:**
- Use lower DPI (150 instead of 200)
- Process only necessary pages
- Batch similar documents
- Use caching (future feature)

### Rate Limit Handling

Docling Hybrid OCR automatically handles rate limits:

1. **Detects 429 errors** from OpenRouter
2. **Reads Retry-After header** for wait time
3. **Exponential backoff** if no header provided
4. **Retries automatically** up to 3 times

You'll see logs like:

```
[INFO] Rate limit hit, waiting 60s before retry...
[INFO] Retrying request (attempt 2/3)...
```

---

## Best Practices

### Security

**✅ DO:**
- Store API key in environment variables
- Use `.env.local` file (add to `.gitignore`)
- Rotate keys periodically
- Use different keys for dev/prod
- Set usage limits in OpenRouter dashboard

**❌ DON'T:**
- Commit API keys to git
- Share keys in chat/email
- Use same key across all projects
- Hardcode keys in source code
- Leave keys in CI/CD logs

### Performance

**Optimize for Speed:**
```bash
# Use lower DPI
docling-hybrid-ocr convert doc.pdf --dpi 150

# Process fewer pages first
docling-hybrid-ocr convert doc.pdf --max-pages 10

# Use multiple workers (if on paid tier)
export DOCLING_HYBRID_MAX_WORKERS=4
```

**Optimize for Quality:**
```bash
# Use higher DPI
docling-hybrid-ocr convert doc.pdf --dpi 250

# Try different model
# Edit configs/local.toml to use GPT-4 Vision
```

### Cost Management

**Monitor Usage:**
```bash
# Check your usage at:
# https://openrouter.ai/activity

# Track conversion costs
docling-hybrid-ocr convert doc.pdf --verbose
# Look for "tokens_used" in output
```

**Reduce Costs:**
- Start with free-tier models
- Use `--max-pages` for testing
- Lower DPI reduces tokens
- Process PDFs in batches overnight
- Set budget alerts in OpenRouter

---

## Troubleshooting

### Error: "Missing OPENROUTER_API_KEY"

**Symptom:**
```
ConfigurationError: Missing OPENROUTER_API_KEY environment variable
```

**Solution:**
```bash
# Check if set
echo $OPENROUTER_API_KEY

# If empty, load environment
source .env.local

# Or set directly
export OPENROUTER_API_KEY=sk-or-v1-your-key
```

### Error: "Invalid API Key"

**Symptom:**
```
BackendError: OpenRouter authentication failed (401)
```

**Solutions:**
1. Check key format: `sk-or-v1-...`
2. Verify key in OpenRouter dashboard
3. Ensure no extra spaces/newlines
4. Try regenerating key

### Error: "Rate Limit Exceeded"

**Symptom:**
```
RateLimitError: Rate limit exceeded, retry after 60s
```

**Solutions:**
1. Wait for indicated time
2. Reduce concurrent workers:
   ```bash
   export DOCLING_HYBRID_MAX_WORKERS=1
   ```
3. Add delays between documents
4. Upgrade to paid tier
5. Use different model

### Error: "Connection Timeout"

**Symptom:**
```
BackendTimeoutError: Request timeout after 120s
```

**Solutions:**
1. Check internet connection
2. Verify OpenRouter status: https://status.openrouter.ai
3. Increase timeout:
   ```bash
   export DOCLING_HYBRID_HTTP_TIMEOUT_S=300
   ```
4. Try again later (temporary overload)

### Poor OCR Quality

**Solutions:**
1. Increase DPI:
   ```bash
   docling-hybrid-ocr convert doc.pdf --dpi 250
   ```
2. Try different model (edit config)
3. Check PDF quality (re-scan if needed)
4. Enable verbose logging to see raw output:
   ```bash
   export DOCLING_HYBRID_LOG_LEVEL=DEBUG
   ```

---

## Advanced Configuration

### Custom Backend Configuration

Create custom config in `configs/my-config.toml`:

```toml
[backends.my-custom-openrouter]
name = "my-custom-openrouter"
model = "openai/gpt-4-vision-preview"
base_url = "https://openrouter.ai/api/v1/chat/completions"
temperature = 0.0
max_tokens = 4096

[backends]
default = "my-custom-openrouter"
```

Use it:

```bash
export DOCLING_HYBRID_CONFIG=configs/my-config.toml
docling-hybrid-ocr convert doc.pdf
```

### Request Headers

Add custom headers (for tracking, etc.):

```python
from docling_hybrid.common.models import OcrBackendConfig

config = OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    # Custom headers via metadata
    extra_headers={
        "HTTP-Referer": "https://my-app.com",
        "X-Title": "My App Name"
    }
)
```

### Monitoring and Logging

Enable detailed logging:

```bash
export DOCLING_HYBRID_LOG_LEVEL=DEBUG
docling-hybrid-ocr convert doc.pdf --verbose
```

Log to file:

```python
from docling_hybrid.orchestrator.callbacks import FileProgressCallback

callback = FileProgressCallback(Path("conversion.log"))
result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)
```

---

## FAQ

**Q: Is OpenRouter free?**
A: Yes, free tier available with select models (including our default Nemotron Nano). Paid tier for higher volume and premium models.

**Q: Do I need a GPU?**
A: No! OpenRouter is cloud-based, works on any machine.

**Q: How long does my API key last?**
A: API keys don't expire unless you delete them. Rotate periodically for security.

**Q: Can I use multiple models?**
A: Yes, configure different backends in config file or use fallback chain.

**Q: What happens if I run out of credits?**
A: Free tier continues with rate limits. Paid tier stops until you add credits.

**Q: Is my data private?**
A: Check OpenRouter's privacy policy. For sensitive documents, consider local inference.

**Q: Can I get a refund?**
A: Contact OpenRouter support for billing questions.

**Q: What's the best model for my use case?**
A: Start with Nemotron Nano (free). If quality insufficient, try GPT-4 Vision or Claude 3.

---

## Support

### OpenRouter Support
- **Dashboard:** https://openrouter.ai/dashboard
- **Documentation:** https://openrouter.ai/docs
- **Status Page:** https://status.openrouter.ai
- **Discord:** https://discord.gg/openrouter

### Docling Hybrid Support
- **GitHub Issues:** https://github.com/docling-hybrid/docling-hybrid-ocr/issues
- **Discussions:** https://github.com/docling-hybrid/docling-hybrid-ocr/discussions
- **Documentation:** https://github.com/docling-hybrid/docling-hybrid-ocr/tree/main/docs

---

## Next Steps

1. ✅ Get your API key
2. ✅ Configure environment
3. ✅ Test with small PDF
4. 📖 Read [QUICK_START.md](QUICK_START.md) for usage examples
5. 📖 Read [API_REFERENCE.md](API_REFERENCE.md) for Python API
6. 🚀 Start converting your PDFs!

---

*Last Updated: 2025-11-25*
*OpenRouter Version: v1*
*For: Docling Hybrid OCR v0.1.0+*
