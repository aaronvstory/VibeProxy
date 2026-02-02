# VibeProxy Quick Start

> **Validated 2026-01-25** — All examples tested against live VibeProxy

---

## TL;DR

```
Base URL:    http://localhost:8317/v1
Endpoint:    /v1/chat/completions
API Key:     Any non-empty string (e.g., "x")
```

**One endpoint for ALL models:** Claude, GPT, Gemini, Grok, Qwen.

---

### Common Commands

- **List models (pretty):**
  ```bash
  curl -s http://100.123.126.47:8317/v1/models | jq -r '.data[].id' | sort
  ```

- **Quick health check:**
  ```bash
  curl -s http://100.123.126.47:8317/v1/models | jq -r '"Models: \(.data | length) ✅"'
  ```

- **Test a chat:**
  ```bash
  curl -s http://100.123.126.47:8317/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer vibeproxy" \
    -d '{"model":"gpt-5.2-codex","messages":[{"role":"user","content":"say hi"}],"max_tokens":20}' \
    | jq -r '.choices[0].message.content // .error.message'
  ```

- **Handy script (optional):**
  - `vibe status` — shows model count & health
  - `vibe models` — lists all models
  - `vibe test` — sends a test chat
  - `vibe test claude-sonnet-4.5` — tests a specific model

  > If `~/bin` isn’t in your `PATH`, either add it or run `~/bin/vibe` directly.

---

## 5-Minute Setup

### 1. Verify VibeProxy is Running

```bash
curl -s http://localhost:8317/v1/models | head -c 100
```
**Expected:** JSON starting with `{"data":[{...`

> **If "Connection refused":** Start the SSH tunnel or check VibeProxy on your Mac.

### 2. List Available Models

```bash
# All models
curl -s http://localhost:8317/v1/models | jq '.data[].id'

# Count models
curl -s http://localhost:8317/v1/models | jq '.data | length'
```
```bash
# All models
curl -s http://localhost:8317/v1/models | jq '.data[].id'

# Count models
curl -s http://localhost:8317/v1/models | jq '.data | length'
```

### 3. Make a Chat Request

```bash
curl -X POST http://localhost:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

---

## Key Rules

| Rule | Details |
|------|---------|
| **Endpoint** | Always use `/v1/chat/completions` for ALL models |
| **GPT-5 temperature** | MUST be `1` (enforced by LiteLLM) |
| **Claude temperature** | `0` to `1` (0 = deterministic) |
| **Gemini temperature** | `0` to `2` |
| **API key** | Any non-empty string works |
| **Vision** | Works transparently for Claude 3+, GPT-4+, Gemini |

### Temperature Quick Reference

```python
def get_temperature(model: str) -> float:
    if "gpt-5" in model.lower():
        return 1.0  # Required!
    return 0.0  # Default for Claude/Gemini
```

---

## Common Configurations

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8317/v1",
    api_key="x"  # Any non-empty string
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0
)
print(response.choices[0].message.content)
```

### Python (httpx/requests)

```python
import httpx

response = httpx.post(
    "http://localhost:8317/v1/chat/completions",
    json={
        "model": "claude-sonnet-4-5-20250929",
        "messages": [{"role": "user", "content": "Hello!"}],
        "max_tokens": 100,
        "temperature": 0
    }
)
print(response.json()["choices"][0]["message"]["content"])
```

### LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="claude-sonnet-4-5-20250929",
    openai_api_base="http://localhost:8317/v1",
    openai_api_key="x",
    temperature=0
)
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8317/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'claude-sonnet-4-5-20250929',
    messages: [{ role: 'user', content: 'Hello!' }],
    temperature: 0
  })
});
const data = await response.json();
console.log(data.choices[0].message.content);
```

### Docker Container

From inside Docker, use `host.docker.internal` instead of `localhost`:

```
http://host.docker.internal:8317/v1/chat/completions
```

### Environment Variables

```bash
export OPENAI_API_BASE="http://localhost:8317/v1"
export OPENAI_API_KEY="x"
```

---

## Best Models by Use Case

| Use Case | Model | Notes |
|----------|-------|-------|
| **General coding** | `claude-sonnet-4-5-20250929` | Best value |
| **Deep analysis** | `claude-opus-4-5-20251101` | Most capable |
| **Fast responses** | `claude-haiku-4-5-20251001` | Fastest |
| **Code reasoning** | `gpt-5.2-codex` | temp=1 required |
| **Large context** | `gemini-2.5-pro` | 1M tokens |
| **Vision tasks** | `gemini-3-pro-image-preview` | Enhanced vision |

---

## Extended Thinking (Claude only)

Add `-thinking-N` suffix to enable extended thinking with N token budget:

```bash
curl -X POST http://localhost:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929-thinking-5000",
    "messages": [{"role": "user", "content": "Solve this step by step..."}]
  }'
```

| Budget | Use Case |
|--------|----------|
| 2000-3000 | Simple reasoning |
| 5000-8000 | Complex analysis |
| 10000+ | Deep problem solving |

---

## Troubleshooting

### Connection refused

```bash
# Check if tunnel is running (Windows)
netstat -an | findstr 8317

# Check VibeProxy directly (Mac)
curl http://localhost:8317/v1/models
```

**Fix:** Start SSH tunnel or VibeProxy app.

### Empty response from GPT-5

**Cause:** Wrong temperature.

**Fix:** Use `temperature: 1` (not 0 or 0.7).

### Model not found

**Cause:** Typo in model ID.

**Fix:** Get exact IDs:
```bash
curl -s http://localhost:8317/v1/models | jq '.data[].id'
```

### Provider authentication failed

**Cause:** OAuth token expired.

**Fix:** Re-authenticate in VibeProxy menu bar app on Mac.

---

## Vision Request Example

```python
import base64
import httpx

# Read and encode image
with open("image.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

response = httpx.post(
    "http://localhost:8317/v1/chat/completions",
    json={
        "model": "claude-sonnet-4-5-20250929",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }],
        "max_tokens": 500
    }
)
```

---

## Full Documentation

For complete reference including error handling, streaming, rate limiting, and client libraries:

**[VIBEPROXY-LLM-INTEGRATION-GUIDE.md](./VIBEPROXY-LLM-INTEGRATION-GUIDE.md)**

---

*Validated against live VibeProxy on 2026-01-25*
