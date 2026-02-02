# VibeProxy LLM Integration Guide

A comprehensive guide for integrating VibeProxy into LLM-based applications, AI agents, and automated workflows.

> **Quick Start:** For a concise setup guide, see **[VIBEPROXY-QUICKSTART.md](./VIBEPROXY-QUICKSTART.md)**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Base URLs and Endpoints](#base-urls-and-endpoints)
5. [Supported Providers and Models](#supported-providers-and-models)
6. [API Reference](#api-reference)
7. [Health Checks and Liveness](#health-checks-and-liveness)
8. [Model Discovery](#model-discovery)
9. [Model Capabilities and Modalities](#model-capabilities-and-modalities)
10. [Making Chat Requests](#making-chat-requests)
11. [Extended Thinking Mode](#extended-thinking-mode)
12. [Model-Specific Constraints](#model-specific-constraints)
13. [Authentication](#authentication)
14. [Error Handling](#error-handling)
15. [Rate Limiting](#rate-limiting)
16. [Configuration Examples](#configuration-examples)
17. [Client Libraries](#client-libraries)
18. [Troubleshooting](#troubleshooting)
19. [Best Practices](#best-practices)

---

## Overview

### What is VibeProxy?

VibeProxy is an OAuth proxy server that bridges AI subscription services (Claude Code, ChatGPT Plus/Pro, GitHub Copilot) to a local OpenAI-compatible API endpoint. It allows applications to use subscription-based AI models without per-token API billing.

### Key Capabilities

- **Unified API**: Single OpenAI-compatible endpoint for multiple providers
- **OAuth Authentication**: Uses existing subscriptions (no API keys required)
- **Multi-Provider Support**: Anthropic, OpenAI, Google, xAI, Qwen
- **Model Routing**: Automatic routing to appropriate backend based on model ID
- **Local Server**: Runs on `localhost:8317` with optional SSH tunneling
- **Extended Thinking**: Special support for Claude extended thinking mode via model name suffixes
- **Transparent Proxy**: Vision and other modalities pass through unchanged

### Why Use VibeProxy?

| Traditional API | VibeProxy |
|-----------------|-----------|
| Pay per token | Use existing subscriptions |
| Multiple API keys | Single endpoint |
| Different APIs per provider | Unified OpenAI-compatible API |
| Direct internet access required | Works behind firewalls via SSH |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR APPLICATION                            │
│  (LLM Agent, Chatbot, IDE Plugin, Automation Script)                │
└─────────────────────────────────────────┬───────────────────────────┘
                                          │ HTTP/HTTPS
                                          ▼
┌────────────────────────────────────────────────────────────────────┐
│                    VibeProxy Server (localhost:8317)               │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 ThinkingProxy (Swift)                       │   │
│  │  - Intercepts requests on port 8317                         │   │
│  │  - Processes Claude extended thinking suffixes              │   │
│  │  - Forwards to CLIProxyAPIPlus on port 8318                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                      │                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 CLIProxyAPIPlus (Go binary)                 │   │
│  │  - OpenAI-compatible API                                    │   │
│  │  - OAuth token management                                   │   │
│  │  - Provider routing                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                      │                             │
│                            Model Router                            │
│                                      │                             │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┬───────────┐   │
│  │Anthropic│ OpenAI  │ Google  │ Copilot │  xAI    │   Qwen    │   │
│  │ Direct  │ Direct  │ Direct  │  Proxy  │         │           │   │
│  └────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴─────┬─────┘   │
└───────┼─────────┼─────────┼─────────┼─────────┼──────────┼─────────┘
        │         │         │         │         │          │
        ▼         ▼         ▼         ▼         ▼          ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                     AI Provider APIs                        │
   │  Anthropic API  OpenAI API  Google AI  GitHub Copilot  Etc. │
   └─────────────────────────────────────────────────────────────┘
```

### Network Topology (SSH Tunnel Scenario)

When VibeProxy runs on a Mac and clients run on Windows/Linux:

```
Windows/Linux Client                    Mac (VibeProxy Host)
┌─────────────────────┐                ┌─────────────────────┐
│  Your Application   │                │     VibeProxy       │
│  localhost:8317 ────┼──SSH Tunnel───►│    localhost:8317   │
└─────────────────────┘                └──────────┬──────────┘
                                                  │
                                                  ▼
                                         AI Provider APIs
```

---

## Prerequisites

### For VibeProxy Server (Mac)

- Apple Silicon Mac (M1/M2/M3/M4)
- macOS 13.0+ (Ventura or later)
- VibeProxy app installed and running
- Authenticated with at least one provider:
  - Claude Code subscription
  - ChatGPT Plus/Pro subscription
  - GitHub Copilot subscription

### For Client Applications

- Network access to VibeProxy (direct or via SSH tunnel)
- HTTP client capability
- JSON request/response handling

### For SSH Tunnel (Windows/Linux Clients)

- SSH client installed
- SSH access to Mac running VibeProxy
- Port 8317 available locally

---

## Base URLs and Endpoints

> **Validated 2026-01-25:** All endpoints tested against live VibeProxy.

### Universal Endpoint (All Models)

**One endpoint works for ALL models** - Claude, GPT, Gemini, Grok, Qwen:

```
Base URL:  http://localhost:8317/v1
Endpoint:  POST /v1/chat/completions
```

| Access Method | Base URL |
|---------------|----------|
| Local (same machine) | `http://localhost:8317/v1` |
| Docker container | `http://host.docker.internal:8317/v1` |
| SSH tunnel | `http://localhost:8317/v1` |
| LAN access | `http://<mac-ip>:8317/v1` |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | Chat completion request (ALL models) |
| `/v1/completions` | POST | Legacy completion (limited support) |

### Provider Setting (for LiteLLM/LangChain)

Some frameworks require a `provider` setting. Use these mappings:

| Model Family | Provider Setting | Notes |
|--------------|------------------|-------|
| `claude-*` | `"openai"` or `"other"` | Works with OpenAI-compatible client |
| `gpt-*` | `"openai"` | |
| `gemini-*` | `"openai"` | |
| All others | `"openai"` | |

**Note:** While Claude models natively use Anthropic's API format, VibeProxy's CLIProxyAPIPlus handles format translation automatically. You can use the OpenAI-compatible endpoint for all models.

---

## Supported Providers and Models

### Provider Routing

VibeProxy automatically routes requests based on model ID patterns:

| Model ID Pattern | Provider | Route |
|------------------|----------|-------|
| `claude-*` with date suffix | Anthropic | Direct API |
| `claude-*` without date | GitHub Copilot | Copilot Proxy |
| `gpt-5*`, `gpt-4*` | OpenAI/Copilot | Copilot or Direct |
| `gemini-*` | Google | Direct or Copilot |
| `grok-*` | xAI | Copilot |
| `qwen*` | Qwen/Alibaba | Direct |

### Complete Model List

#### Anthropic (Direct API)

| Model ID | Display Name | Context | Max Output | Vision | Notes |
|----------|--------------|---------|------------|--------|-------|
| `claude-opus-4-5-20251101` | Claude Opus 4.5 | 200,000 | 32,000 | Yes | Most capable |
| `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 | 200,000 | 32,000 | Yes | Best value |
| `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | 200,000 | 8,192 | Yes | Fastest |
| `claude-opus-4-1-20250805` | Claude Opus 4.1 | 200,000 | 32,000 | Yes | Previous gen |
| `claude-sonnet-4-20250514` | Claude Sonnet 4 | 200,000 | 32,000 | Yes | Legacy |
| `claude-3-7-sonnet-20250219` | Claude 3.7 Sonnet | 200,000 | 32,000 | Yes | Legacy |
| `claude-3-5-haiku-20241022` | Claude 3.5 Haiku | 200,000 | 8,192 | Yes | Legacy fast |

#### OpenAI (via Copilot)

| Model ID | Display Name | Context | Max Output | Vision | Notes |
|----------|--------------|---------|------------|--------|-------|
| `gpt-5.2-codex` | GPT-5.2 Codex | 400,000 | 128,000 | Yes | Best reasoning |
| `gpt-5.2` | GPT-5.2 | 400,000 | 128,000 | Yes | General |
| `gpt-5.1-codex-max` | GPT-5.1 Codex Max | 400,000 | 128,000 | Yes | Deep analysis |
| `gpt-5.1-codex` | GPT-5.1 Codex | 400,000 | 128,000 | Yes | Coding focus |
| `gpt-5.1-codex-mini` | GPT-5.1 Codex Mini | 400,000 | 128,000 | Yes | Fast coding |
| `gpt-5.1` | GPT-5.1 | 400,000 | 128,000 | Yes | General |
| `gpt-5-codex` | GPT-5 Codex | 400,000 | 128,000 | Yes | Previous gen |
| `gpt-5-mini` | GPT-5 Mini | 400,000 | 128,000 | Yes | Lightweight |
| `gpt-5` | GPT-5 | 400,000 | 128,000 | Yes | Base model |
| `gpt-4.1` | GPT-4.1 | 128,000 | 16,000 | Yes | Legacy |

#### Google (Direct or Copilot)

| Model ID | Display Name | Context | Max Output | Vision | Notes |
|----------|--------------|---------|------------|--------|-------|
| `gemini-3-pro-preview` | Gemini 3 Pro Preview | 1,000,000 | 65,536 | Yes | Latest |
| `gemini-3-flash-preview` | Gemini 3 Flash Preview | 1,000,000 | 65,536 | Yes | Fast |
| `gemini-3-pro-image-preview` | Gemini 3 Pro (Image) | 1,000,000 | 65,536 | Yes | Enhanced vision |
| `gemini-2.5-pro` | Gemini 2.5 Pro | 1,000,000 | 65,536 | Yes | Large context |
| `gemini-2.5-flash` | Gemini 2.5 Flash | 1,000,000 | 65,536 | Yes | Balanced |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite | 1,000,000 | 65,536 | Yes | Lightweight |

#### Other Providers

| Model ID | Display Name | Provider | Vision | Notes |
|----------|--------------|----------|--------|-------|
| `grok-code-fast-1` | Grok Code Fast | xAI | Yes | Code-optimized |
| `qwen3-coder-plus` | Qwen3 Coder Plus | Alibaba | Limited | Coding model |
| `qwen3-coder-flash` | Qwen3 Coder Flash | Alibaba | Limited | Fast coding |

---

## API Reference

### GET /v1/models

Lists all available models from VibeProxy.

**Request:**

```http
GET /v1/models HTTP/1.1
Host: localhost:8317
```

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "claude-opus-4-5-20251101",
      "object": "model",
      "created": 1730419200,
      "owned_by": "anthropic"
    },
    {
      "id": "gpt-5.2-codex",
      "object": "model",
      "created": 1730419200,
      "owned_by": "github-copilot"
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"list"` |
| `data` | array | Array of model objects |
| `data[].id` | string | Model identifier (use in requests) |
| `data[].object` | string | Always `"model"` |
| `data[].created` | integer | Unix timestamp |
| `data[].owned_by` | string | Provider identifier |

**Important:** The `/v1/models` endpoint does **not** return capability information (vision support, context length, etc.). Capability information must be maintained separately based on known model specifications.

### POST /v1/chat/completions

Send a chat completion request.

**Request:**

```http
POST /v1/chat/completions HTTP/1.1
Host: localhost:8317
Content-Type: application/json

{
  "model": "claude-sonnet-4-5-20250929",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 1024,
  "temperature": 0.7
}
```

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | Yes | - | Model ID from `/v1/models` |
| `messages` | array | Yes | - | Conversation messages |
| `max_tokens` | integer | No | 1024 | Maximum tokens to generate |
| `temperature` | number | No | Model-specific | Randomness (0-2) |
| `top_p` | number | No | 1.0 | Nucleus sampling |
| `stream` | boolean | No | false | Enable streaming |
| `stop` | string/array | No | null | Stop sequences |

**Message Format:**

```json
{
  "role": "user|assistant|system",
  "content": "Message text"
}
```

**Vision Message Format (for image input):**

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "What's in this image?"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "data:image/jpeg;base64,/9j/4AAQ..."
      }
    }
  ]
}
```

**Response:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1730419200,
  "model": "claude-sonnet-4-5-20250929",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 9,
    "total_tokens": 24
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique request ID |
| `object` | string | Always `"chat.completion"` |
| `created` | integer | Unix timestamp |
| `model` | string | Model used |
| `choices` | array | Response choices |
| `choices[].message` | object | Assistant's response |
| `choices[].finish_reason` | string | `stop`, `length`, `error` |
| `usage` | object | Token usage statistics |

---

## Health Checks and Liveness

### Quick Health Check

Check if VibeProxy is running and responding:

```bash
curl -s http://localhost:8317/v1/models | head -c 100
```

**Expected Response:** JSON starting with `{"object":"list","data":[`

### Programmatic Health Check (Python)

```python
import httpx

async def check_vibeproxy_health(base_url: str = "http://localhost:8317") -> tuple[bool, str]:
    """
    Check if VibeProxy is healthy and responding.

    Returns:
        tuple[bool, str]: (is_healthy, status_message)
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/v1/models")

            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                return True, f"Healthy ({model_count} models available)"
            else:
                return False, f"HTTP {response.status_code}"

    except httpx.ConnectError:
        return False, "Connection refused - VibeProxy not running or tunnel down"
    except httpx.TimeoutException:
        return False, "Connection timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"
```

### Health Check (JavaScript/Node.js)

```javascript
async function checkVibeProxyHealth(baseUrl = 'http://localhost:8317') {
  try {
    const response = await fetch(`${baseUrl}/v1/models`, {
      signal: AbortSignal.timeout(5000)
    });

    if (response.ok) {
      const data = await response.json();
      const modelCount = data.data?.length || 0;
      return { healthy: true, message: `Healthy (${modelCount} models)` };
    }
    return { healthy: false, message: `HTTP ${response.status}` };

  } catch (error) {
    if (error.name === 'AbortError') {
      return { healthy: false, message: 'Connection timeout' };
    }
    return { healthy: false, message: error.message };
  }
}
```

### Health Check (curl/bash)

```bash
#!/bin/bash

check_vibeproxy() {
    local response
    response=$(curl -s --max-time 5 "http://localhost:8317/v1/models" 2>/dev/null)

    if [ $? -eq 0 ] && echo "$response" | grep -q '"object":"list"'; then
        local count=$(echo "$response" | grep -o '"id"' | wc -l)
        echo "Healthy ($count models available)"
        return 0
    else
        echo "Not responding"
        return 1
    fi
}

# Usage
if check_vibeproxy; then
    echo "VibeProxy is ready"
else
    echo "VibeProxy is down"
    exit 1
fi
```

### Port Liveness Check

Check if port 8317 is accepting connections (doesn't verify API):

```bash
# Linux/Mac
nc -z localhost 8317 && echo "Port open" || echo "Port closed"

# Windows PowerShell
Test-NetConnection localhost -Port 8317

# Cross-platform Python
python -c "import socket; s=socket.socket(); s.settimeout(1); print('Open' if s.connect_ex(('localhost',8317))==0 else 'Closed')"
```

---

## Model Discovery

### Listing All Models

```python
import httpx

async def list_models(base_url: str = "http://localhost:8317") -> list[dict]:
    """
    Retrieve all available models from VibeProxy.

    Returns:
        list[dict]: List of model objects with id, object, created, owned_by
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{base_url}/v1/models")
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
```

### Filtering Models by Provider

```python
def filter_models_by_provider(models: list[dict], provider: str) -> list[dict]:
    """
    Filter models by provider name.

    Args:
        models: List of model objects
        provider: Provider to filter by (anthropic, openai, google, etc.)

    Returns:
        Filtered list of models
    """
    return [m for m in models if m.get("owned_by", "").lower() == provider.lower()]

# Usage
all_models = await list_models()
claude_models = filter_models_by_provider(all_models, "anthropic")
gpt_models = filter_models_by_provider(all_models, "github-copilot")
```

### Detecting Provider from Model ID

```python
def detect_provider(model_id: str) -> str:
    """
    Determine the provider from a model ID string.

    Args:
        model_id: Model identifier

    Returns:
        Provider name (Anthropic, OpenAI, Google, xAI, Qwen, Other)
    """
    model_lower = model_id.lower()

    if "claude" in model_lower:
        return "Anthropic"
    elif "gpt" in model_lower:
        return "OpenAI"
    elif "gemini" in model_lower:
        return "Google"
    elif "grok" in model_lower:
        return "xAI"
    elif "qwen" in model_lower:
        return "Qwen"
    else:
        return "Other"
```

### Caching Model Lists

```python
import time
from typing import Optional

class ModelCache:
    """Cache for model list with TTL."""

    def __init__(self, ttl_seconds: int = 30):
        self._models: list[dict] = []
        self._last_refresh: float = 0
        self._ttl = ttl_seconds

    async def get_models(
        self,
        base_url: str = "http://localhost:8317",
        force_refresh: bool = False
    ) -> list[dict]:
        """
        Get models with caching.

        Args:
            base_url: VibeProxy base URL
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            List of model objects
        """
        now = time.time()
        cache_age = now - self._last_refresh

        if not force_refresh and cache_age < self._ttl and self._models:
            return self._models

        try:
            self._models = await list_models(base_url)
            self._last_refresh = now
            return self._models
        except Exception:
            # Return stale cache on error
            if self._models:
                return self._models
            raise

# Usage
cache = ModelCache(ttl_seconds=60)
models = await cache.get_models()  # Fetches if stale
models = await cache.get_models()  # Returns cached
models = await cache.get_models(force_refresh=True)  # Force refresh
```

---

## Model Capabilities and Modalities

### Important: No Capabilities API

**VibeProxy does not provide an API endpoint to query model capabilities or supported modalities.** The `/v1/models` endpoint only returns basic model information (id, created, owned_by) without capability details.

This is by design - VibeProxy acts as a transparent proxy that forwards requests unchanged to the underlying providers. It does not inspect or validate model capabilities.

### Vision Support

VibeProxy transparently passes vision/image data through to the underlying models. **You do not need to configure anything special in VibeProxy for vision to work.**

**Models with Native Vision Support:**

| Provider | Models | Vision Support |
|----------|--------|----------------|
| Anthropic | All Claude 3+ models | Full multimodal |
| OpenAI | All GPT-4+ models | Full multimodal |
| Google | All Gemini models | Full multimodal |
| Google | `gemini-3-pro-image-preview` | Enhanced vision capabilities |

**How Vision Works:**

1. Your application sends a request with image data (base64 or URL)
2. VibeProxy forwards the request unchanged to the provider
3. The provider's model processes the image natively
4. Response is returned through VibeProxy

**Example Vision Request:**

```python
async def analyze_image(image_base64: str, prompt: str) -> str:
    """Analyze an image using a vision-capable model."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ]

    response = await chat(
        model="claude-sonnet-4-5-20250929",  # Any vision-capable model
        messages=messages
    )
    return response["choices"][0]["message"]["content"]
```

### Maintaining a Capabilities Database

Since VibeProxy doesn't provide capability information, you should maintain your own capabilities mapping:

```python
MODEL_CAPABILITIES = {
    # Claude models
    "claude-opus-4-5-20251101": {
        "vision": True,
        "context_window": 200000,
        "max_output": 32000,
        "extended_thinking": True,
        "temperature_range": (0, 1)
    },
    "claude-sonnet-4-5-20250929": {
        "vision": True,
        "context_window": 200000,
        "max_output": 32000,
        "extended_thinking": True,
        "temperature_range": (0, 1)
    },
    "claude-haiku-4-5-20251001": {
        "vision": True,
        "context_window": 200000,
        "max_output": 8192,
        "extended_thinking": False,
        "temperature_range": (0, 1)
    },
    # GPT models
    "gpt-5.2-codex": {
        "vision": True,
        "context_window": 400000,
        "max_output": 128000,
        "extended_thinking": False,
        "temperature_range": (1, 1)  # Must be 1
    },
    # Gemini models
    "gemini-3-pro-image-preview": {
        "vision": True,  # Enhanced vision
        "context_window": 1000000,
        "max_output": 65536,
        "extended_thinking": False,
        "temperature_range": (0, 2)
    }
}

def get_model_capabilities(model_id: str) -> dict:
    """Get capabilities for a model, with sensible defaults."""
    return MODEL_CAPABILITIES.get(model_id, {
        "vision": True,  # Assume vision support for modern models
        "context_window": 128000,
        "max_output": 16000,
        "extended_thinking": False,
        "temperature_range": (0, 1)
    })

def supports_vision(model_id: str) -> bool:
    """Check if a model supports vision input."""
    caps = get_model_capabilities(model_id)
    return caps.get("vision", True)
```

---

## Making Chat Requests

### Basic Chat Request (Python)

```python
import httpx
from typing import Optional

async def chat(
    model: str,
    messages: list[dict],
    base_url: str = "http://localhost:8317",
    max_tokens: int = 1024,
    temperature: Optional[float] = None
) -> dict:
    """
    Send a chat completion request to VibeProxy.

    Args:
        model: Model ID (e.g., "claude-sonnet-4-5-20250929")
        messages: List of message dicts with "role" and "content"
        base_url: VibeProxy base URL
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (None = model default)

    Returns:
        Chat completion response dict
    """
    # Auto-set temperature for GPT-5 models (required to be 1)
    if temperature is None:
        temperature = 1.0 if "gpt-5" in model.lower() else 0.0

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage
response = await chat(
    model="claude-sonnet-4-5-20250929",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Explain Python decorators."}
    ]
)
print(response["choices"][0]["message"]["content"])
```

### Streaming Chat (Python)

```python
import httpx
from typing import AsyncGenerator, Optional

async def chat_stream(
    model: str,
    messages: list[dict],
    base_url: str = "http://localhost:8317",
    max_tokens: int = 1024,
    temperature: Optional[float] = None
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion from VibeProxy.

    Yields:
        Content chunks as they arrive
    """
    if temperature is None:
        temperature = 1.0 if "gpt-5" in model.lower() else 0.0

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{base_url}/v1/chat/completions",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    chunk = json.loads(data)
                    if content := chunk["choices"][0]["delta"].get("content"):
                        yield content

# Usage
async for chunk in chat_stream(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Write a poem about coding."}]
):
    print(chunk, end="", flush=True)
```

### Chat Request (JavaScript/Node.js)

```javascript
async function chat(model, messages, options = {}) {
  const {
    baseUrl = 'http://localhost:8317',
    maxTokens = 1024,
    temperature = null
  } = options;

  // Auto-set temperature for GPT-5 models
  const temp = temperature ?? (model.toLowerCase().includes('gpt-5') ? 1.0 : 0.0);

  const response = await fetch(`${baseUrl}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages,
      max_tokens: maxTokens,
      temperature: temp
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  return response.json();
}

// Usage
const response = await chat('claude-sonnet-4-5-20250929', [
  { role: 'user', content: 'Hello!' }
]);
console.log(response.choices[0].message.content);
```

### Chat Request (curl)

```bash
curl -X POST http://localhost:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 100,
    "temperature": 0
  }'
```

---

## Extended Thinking Mode

### Overview

VibeProxy provides special support for Claude's extended thinking mode through model name suffixes. This allows you to enable extended thinking without modifying your request body.

### How It Works

1. Append `-thinking-NUMBER` to any Claude model ID
2. VibeProxy intercepts the request
3. Strips the suffix and adds the `thinking` parameter to the request body
4. Forwards the modified request to the provider

### Syntax

```
<base-model-id>-thinking-<token-budget>
```

**Examples:**

| Model with Thinking | Base Model | Token Budget |
|---------------------|------------|--------------|
| `claude-sonnet-4-5-20250929-thinking-2000` | `claude-sonnet-4-5-20250929` | 2,000 |
| `claude-sonnet-4-5-20250929-thinking-5000` | `claude-sonnet-4-5-20250929` | 5,000 |
| `claude-sonnet-4-5-20250929-thinking-8000` | `claude-sonnet-4-5-20250929` | 8,000 |
| `claude-opus-4-5-20251101-thinking-10000` | `claude-opus-4-5-20251101` | 10,000 |

### Usage Example

```python
# Enable extended thinking with 5000 token budget
response = await chat(
    model="claude-sonnet-4-5-20250929-thinking-5000",
    messages=[
        {"role": "user", "content": "Solve this complex math problem step by step..."}
    ]
)
```

### Important Notes

- Extended thinking is only supported for Claude models
- Token budget must be a positive integer
- Higher token budgets allow more thorough reasoning but increase latency
- The model name returned in the response will be the base model (without suffix)
- For gemini-claude variants, the `-thinking` suffix is preserved differently

### When to Use Extended Thinking

| Use Case | Recommended Budget |
|----------|-------------------|
| Simple reasoning | 2,000 - 3,000 |
| Complex analysis | 5,000 - 8,000 |
| Deep problem solving | 10,000+ |
| Math proofs | 8,000 - 15,000 |

---

## Model-Specific Constraints

### GPT-5 Temperature Constraint

**CRITICAL:** All GPT-5 models require `temperature=1`. LiteLLM (used by many clients) enforces this constraint.

```
litellm.UnsupportedParamsError: gpt-5 models (including gpt-5-codex)
don't support temperature=0.1. Only temperature=1 is supported.
```

**Affected Models:**
- `gpt-5.2-codex`
- `gpt-5.2`
- `gpt-5.1-codex-max`
- `gpt-5.1-codex`
- `gpt-5.1-codex-mini`
- `gpt-5.1`
- `gpt-5-codex`
- `gpt-5-mini`
- `gpt-5`
- Any model ID containing "gpt-5"

**Solution:**

```python
def get_temperature(model: str, desired: float = 0.0) -> float:
    """Get appropriate temperature for model."""
    if "gpt-5" in model.lower():
        return 1.0  # GPT-5 requires temperature=1
    return desired

# Usage
temp = get_temperature("gpt-5.2-codex", desired=0.0)  # Returns 1.0
temp = get_temperature("claude-sonnet-4-5-20250929", desired=0.0)  # Returns 0.0
```

### Claude Temperature Range

Claude models support `temperature` from 0 to 1:
- `0`: Deterministic (best for code/analysis)
- `0.5-0.7`: Balanced creativity
- `1`: Maximum creativity

### Gemini Temperature Range

Gemini models support `temperature` from 0 to 2:
- `0-1`: Similar to other models
- `1-2`: Extended creativity range

### Context Window Limits

| Model Family | Context Window | Recommended Max Input |
|--------------|----------------|----------------------|
| Claude | 200,000 | 180,000 |
| GPT-5 | 400,000 | 350,000 |
| Gemini | 1,000,000 | 900,000 |

### Max Output Limits

| Model | Max Output | Notes |
|-------|------------|-------|
| Claude Opus/Sonnet | 32,000 | Extended output |
| Claude Haiku | 8,192 | Shorter responses |
| GPT-5 variants | 128,000 | Very large outputs |
| Gemini | 65,536 | Large outputs |

---

## Authentication

VibeProxy handles OAuth authentication internally. **No API keys are needed for requests.**

### Dummy API Keys for Compatibility

Some clients require an API key parameter. Use any non-empty string:

```python
# For libraries that require api_key
api_key = "dummy-not-used"
api_key = "vibeproxy"
api_key = "x"  # Minimal placeholder
```

### Agent Zero Configuration Example

```json
{
  "chat": {
    "model": "claude-sonnet-4-5-20250929",
    "api_base": "http://host.docker.internal:8317/v1"
  },
  "api_keys": {
    "ANTHROPIC_API_KEY": "dummy-not-used",
    "OPENAI_API_KEY": "dummy-not-used"
  }
}
```

### LangChain Configuration

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="claude-sonnet-4-5-20250929",
    openai_api_key="dummy-not-used",  # Required but not validated
    openai_api_base="http://localhost:8317/v1"
)
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request

```json
{
  "error": {
    "message": "Invalid model: unknown-model",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

**Cause:** Model ID not recognized
**Solution:** Use `/v1/models` to get valid model IDs

#### 401 Unauthorized

```json
{
  "error": {
    "message": "Provider authentication failed",
    "type": "authentication_error"
  }
}
```

**Cause:** VibeProxy's OAuth token expired or provider not authenticated
**Solution:** Re-authenticate in VibeProxy menu bar app

#### 429 Rate Limited

```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error"
  }
}
```

**Cause:** Too many requests to provider
**Solution:** Implement exponential backoff

#### 500 Internal Error

```json
{
  "error": {
    "message": "Internal server error",
    "type": "server_error"
  }
}
```

**Cause:** VibeProxy or provider issue
**Solution:** Check VibeProxy logs, retry request

#### 502 Bad Gateway

```json
{
  "error": {
    "message": "Provider unavailable",
    "type": "provider_error"
  }
}
```

**Cause:** Provider API is down
**Solution:** Try alternative model/provider

### Error Handling Pattern (Python)

```python
import httpx
from typing import Optional

class VibeProxyError(Exception):
    """Base exception for VibeProxy errors."""
    def __init__(self, message: str, error_type: str, status_code: int):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        super().__init__(f"{error_type}: {message}")

class ModelNotFoundError(VibeProxyError):
    pass

class AuthenticationError(VibeProxyError):
    pass

class RateLimitError(VibeProxyError):
    pass

async def chat_with_error_handling(
    model: str,
    messages: list[dict],
    base_url: str = "http://localhost:8317",
    max_retries: int = 3
) -> dict:
    """Chat with comprehensive error handling."""

    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{base_url}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 1.0 if "gpt-5" in model.lower() else 0.0
                    }
                )

                if response.status_code == 200:
                    return response.json()

                # Parse error response
                try:
                    error_data = response.json().get("error", {})
                    error_msg = error_data.get("message", "Unknown error")
                    error_type = error_data.get("type", "unknown")
                except:
                    error_msg = response.text[:200]
                    error_type = "unknown"

                # Handle specific errors
                if response.status_code == 400:
                    raise ModelNotFoundError(error_msg, error_type, 400)
                elif response.status_code == 401:
                    raise AuthenticationError(error_msg, error_type, 401)
                elif response.status_code == 429:
                    # Rate limited - exponential backoff
                    import asyncio
                    wait_time = (2 ** attempt) * 1.0
                    await asyncio.sleep(wait_time)
                    last_error = RateLimitError(error_msg, error_type, 429)
                    continue
                else:
                    raise VibeProxyError(error_msg, error_type, response.status_code)

        except httpx.ConnectError:
            last_error = ConnectionError("VibeProxy not reachable")
            import asyncio
            await asyncio.sleep(1.0)
            continue
        except httpx.TimeoutException:
            last_error = TimeoutError("Request timed out")
            continue

    raise last_error or Exception("Max retries exceeded")
```

---

## Rate Limiting

### Provider Rate Limits

Rate limits are enforced by the underlying providers, not VibeProxy itself:

| Provider | Typical Limits |
|----------|----------------|
| Anthropic (Claude Code) | ~50 requests/minute |
| OpenAI (Copilot) | ~60 requests/minute |
| Google (Gemini) | Varies by tier |

### Implementing Backoff

```python
import asyncio
from typing import Callable, TypeVar

T = TypeVar('T')

async def with_exponential_backoff(
    func: Callable[[], T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> T:
    """
    Execute function with exponential backoff on failure.

    Args:
        func: Async function to execute
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries

    Returns:
        Function result on success

    Raises:
        Last exception if all retries fail
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError as e:
            delay = min(base_delay * (2 ** attempt), max_delay)
            await asyncio.sleep(delay)
            last_error = e
        except Exception as e:
            last_error = e
            raise

    raise last_error
```

### Request Throttling

```python
import asyncio
import time

class RateLimiter:
    """Simple rate limiter for VibeProxy requests."""

    def __init__(self, requests_per_minute: int = 30):
        self._interval = 60.0 / requests_per_minute
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until rate limit allows next request."""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_request

            if elapsed < self._interval:
                await asyncio.sleep(self._interval - elapsed)

            self._last_request = time.time()

# Usage
limiter = RateLimiter(requests_per_minute=30)

async def rate_limited_chat(model: str, messages: list[dict]) -> dict:
    await limiter.acquire()
    return await chat(model, messages)
```

---

## Configuration Examples

### Agent Zero (A0) Configuration

> **Validated 2026-01-25:** Same base URL works for all models.

**All Models (Claude, GPT, Gemini):**

```json
{
  "chat_model_provider": "other",
  "chat_model_name": "claude-sonnet-4-5-20250929",
  "chat_model_api_base": "http://host.docker.internal:8317/v1",
  "chat_model_kwargs": {
    "temperature": "0"
  }
}
```

**GPT-5 Models (temperature=1 required):**

```json
{
  "chat_model_provider": "other",
  "chat_model_name": "gpt-5.2-codex",
  "chat_model_api_base": "http://host.docker.internal:8317/v1",
  "chat_model_kwargs": {
    "temperature": "1"
  }
}
```

Full configuration with all models:

```json
{
  "version": "v0.9.7-10",
  "chat_model_provider": "other",
  "chat_model_name": "claude-sonnet-4-5-20250929",
  "chat_model_api_base": "http://host.docker.internal:8317/v1",
  "chat_model_kwargs": {
    "temperature": "0",
    "drop_params": true,
    "supports_response_schema": false
  },
  "chat_model_ctx_length": 200000,
  "chat_model_ctx_history": 0.7,
  "chat_model_vision": true,
  "util_model_provider": "other",
  "util_model_name": "claude-haiku-4-5-20251001",
  "util_model_api_base": "http://host.docker.internal:8317/v1",
  "util_model_ctx_length": 200000,
  "util_model_kwargs": {
    "temperature": "0",
    "drop_params": true
  },
  "browser_model_provider": "other",
  "browser_model_name": "claude-sonnet-4-5-20250929",
  "browser_model_api_base": "http://host.docker.internal:8317/v1",
  "browser_model_vision": true,
  "browser_model_kwargs": {
    "temperature": "0"
  },
  "embed_model_provider": "huggingface",
  "embed_model_name": "sentence-transformers/all-MiniLM-L6-v2",
  "api_keys": {
    "ANTHROPIC_API_KEY": "dummy-not-used",
    "OPENAI_API_KEY": "dummy-not-used"
  }
}
```

### Factory/Droid CLI Configuration

Location: `~/.factory/config.json`

> **Validated 2026-01-25:** Same base URL for all models.

```json
{
  "custom_models": [
    {
      "model_display_name": "Claude Sonnet 4.5 (VibeProxy)",
      "model": "claude-sonnet-4-5-20250929",
      "base_url": "http://localhost:8317/v1",
      "api_key": "dummy-not-used",
      "provider": "openai"
    },
    {
      "model_display_name": "GPT-5.2 Codex (VibeProxy)",
      "model": "gpt-5.2-codex",
      "base_url": "http://localhost:8317/v1",
      "api_key": "dummy-not-used",
      "provider": "openai"
    },
    {
      "model_display_name": "Gemini 3 Pro Image (VibeProxy)",
      "model": "gemini-3-pro-image-preview",
      "base_url": "http://localhost:8317/v1",
      "api_key": "dummy-not-used",
      "provider": "openai"
    }
  ]
}
```

Usage:

```bash
droid exec -m custom:claude-sonnet-4-5-20250929 "your prompt"
```

### LangChain Configuration

> **Validated 2026-01-25:** Same base URL for all models.

```python
from langchain_openai import ChatOpenAI

# Claude via VibeProxy (OpenAI-compatible)
claude = ChatOpenAI(
    model="claude-sonnet-4-5-20250929",
    openai_api_key="dummy",
    openai_api_base="http://localhost:8317/v1",
    temperature=0
)

# GPT-5 via VibeProxy (temperature=1 required)
gpt5 = ChatOpenAI(
    model="gpt-5.2-codex",
    openai_api_key="dummy",
    openai_api_base="http://localhost:8317/v1",
    temperature=1  # Required for GPT-5
)

# Gemini via VibeProxy
gemini = ChatOpenAI(
    model="gemini-3-pro-preview",
    openai_api_key="dummy",
    openai_api_base="http://localhost:8317/v1",
    temperature=0.7
)
```

### LiteLLM Configuration

```python
import litellm

# Configure VibeProxy as custom endpoint
litellm.api_base = "http://localhost:8317/v1"
litellm.api_key = "dummy-not-used"

# For GPT-5, drop unsupported params
litellm.drop_params = True

response = litellm.completion(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### OpenAI SDK Configuration

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8317/v1",
    api_key="dummy-not-used"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0
)
```

---

## Client Libraries

### Python Async Client

```python
"""VibeProxy Python Client"""

import httpx
import time
from dataclasses import dataclass
from typing import Optional, List, AsyncGenerator

@dataclass
class Model:
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "vibeproxy"

    @property
    def provider(self) -> str:
        id_lower = self.id.lower()
        if "claude" in id_lower:
            return "Anthropic"
        elif "gpt" in id_lower:
            return "OpenAI"
        elif "gemini" in id_lower:
            return "Google"
        elif "grok" in id_lower:
            return "xAI"
        elif "qwen" in id_lower:
            return "Qwen"
        return "Other"

@dataclass
class ChatResponse:
    content: str
    tokens: int = 0
    elapsed: float = 0.0
    model: str = ""
    finish_reason: str = "stop"

class VibeProxyClient:
    """Async client for VibeProxy API."""

    _cache: dict = {"models": [], "last_refresh": 0.0}

    def __init__(self, base_url: str = "http://localhost:8317"):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(60.0, connect=5.0),
                headers={"Content-Type": "application/json"}
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get("/v1/models", timeout=5.0)
            return response.status_code == 200
        except:
            return False

    async def list_models(self, force_refresh: bool = False) -> List[Model]:
        cache = VibeProxyClient._cache
        now = time.time()

        if not force_refresh and (now - cache["last_refresh"]) < 30 and cache["models"]:
            return cache["models"]

        client = await self._get_client()
        response = await client.get("/v1/models", timeout=5.0)
        response.raise_for_status()
        data = response.json()

        models = [
            Model(
                id=item.get("id", ""),
                object=item.get("object", "model"),
                created=item.get("created", 0),
                owned_by=item.get("owned_by", "vibeproxy")
            )
            for item in data.get("data", [])
        ]

        cache["models"] = models
        cache["last_refresh"] = now
        return models

    async def chat(
        self,
        model: str,
        messages: List[dict],
        max_tokens: int = 1024,
        temperature: Optional[float] = None
    ) -> ChatResponse:
        start_time = time.time()

        if temperature is None:
            temperature = 1.0 if "gpt-5" in model.lower() else 0.0

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        client = await self._get_client()
        response = await client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        content = ""
        finish_reason = "error"
        if "choices" in data and data["choices"]:
            choice = data["choices"][0]
            content = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason", "stop")

        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)

        return ChatResponse(
            content=content,
            tokens=tokens,
            elapsed=time.time() - start_time,
            model=model,
            finish_reason=finish_reason
        )

    async def chat_stream(
        self,
        model: str,
        messages: List[dict],
        max_tokens: int = 1024,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        if temperature is None:
            temperature = 1.0 if "gpt-5" in model.lower() else 0.0

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }

        client = await self._get_client()
        async with client.stream("POST", "/v1/chat/completions", json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    chunk = json.loads(data)
                    if content := chunk["choices"][0]["delta"].get("content"):
                        yield content

    async def test_model(self, model: str) -> tuple[bool, str]:
        try:
            response = await self.chat(
                model=model,
                messages=[{"role": "user", "content": "Reply with just 'OK'"}],
                max_tokens=10
            )
            if response.finish_reason == "error":
                return False, response.content
            return True, f"OK ({response.elapsed:.1f}s, {response.tokens} tokens)"
        except Exception as e:
            return False, str(e)
```

---

## Troubleshooting

### Connection Issues

#### "Connection refused"

**Cause:** VibeProxy not running or SSH tunnel down

**Diagnosis:**

```bash
# Check if port is open
curl http://localhost:8317/v1/models

# Check SSH tunnel (Windows)
netstat -an | findstr 8317

# Check VibeProxy status (Mac)
curl http://localhost:8317/v1/models
```

**Solutions:**

1. Start VibeProxy on Mac
2. Start SSH tunnel on Windows
3. Verify Mac IP hasn't changed

#### "Connection timeout"

**Cause:** Network issues, Mac sleeping, or firewall

**Solutions:**

1. Wake Mac from sleep
2. Check network connectivity
3. Verify firewall allows port 8317
4. Try direct connection vs SSH tunnel

### Model Issues

#### "Model not found"

**Cause:** Invalid model ID

**Solution:** Use exact model ID from `/v1/models`

```bash
# Get valid model IDs
curl -s http://localhost:8317/v1/models | jq '.data[].id'
```

#### Empty response from GPT-5

**Cause:** Wrong temperature setting

**Solution:** Use `temperature=1` for all GPT-5 models

### Authentication Issues

#### "Provider authentication failed"

**Cause:** OAuth token expired

**Solutions:**

1. Open VibeProxy menu bar app
2. Re-authenticate with provider
3. Check provider subscription is active

### Vision Issues

#### "Image not processed"

**Possible Causes:**

1. Model doesn't support vision (check capabilities)
2. Image format not supported
3. Image too large

**Solutions:**

1. Use a vision-capable model (Claude 3+, GPT-4+, Gemini)
2. Convert image to JPEG or PNG
3. Resize large images before sending

### SSH Tunnel Issues

#### Tunnel disconnects frequently

**Solutions:**

1. Use the intelligent tunnel script with auto-reconnect
2. Enable SSH keepalive:

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ...
```

#### Mac IP changed

**Solution:** Network scan for new IP:

```bash
# Find Mac on network
nmap -p 22 192.168.1.0/24 --open
```

### Performance Issues

#### Slow responses

**Diagnosis:**

```python
import time

start = time.time()
response = await client.chat(model, messages)
print(f"Elapsed: {time.time() - start:.2f}s")
```

**Potential causes:**

1. Network latency (SSH tunnel)
2. Model processing time
3. Provider rate limiting

**Solutions:**

1. Use faster model (Haiku vs Opus)
2. Reduce max_tokens
3. Check network path

---

## Best Practices

### Model Selection

| Use Case | Recommended Model |
|----------|-------------------|
| Code analysis | `gpt-5.2-codex`, `claude-opus-4-5-20251101` |
| Fast responses | `claude-haiku-4-5-20251001`, `gemini-2.5-flash` |
| Large context | `gemini-2.5-pro` (1M tokens) |
| Best value | `claude-sonnet-4-5-20250929` |
| Deep reasoning | `gpt-5.1-codex-max` |
| Vision tasks | `gemini-3-pro-image-preview`, `claude-sonnet-4-5-20250929` |
| Extended thinking | `claude-sonnet-4-5-20250929-thinking-5000` |

### Connection Management

1. **Reuse clients**: Create one client instance, reuse for all requests
2. **Connection pooling**: httpx and aiohttp handle this automatically
3. **Health checks**: Check connection before batch operations
4. **Graceful degradation**: Fall back to alternative models on failure

### Error Handling

1. **Retry with backoff**: Use exponential backoff for transient errors
2. **Circuit breaker**: Stop requests after repeated failures
3. **Timeout tuning**: Set appropriate timeouts (5s connect, 60s read)
4. **Error logging**: Log errors with context for debugging

### Caching

1. **Cache model lists**: Refresh every 30-60 seconds
2. **Don't cache completions**: Responses vary by model state
3. **Cache health status**: Avoid repeated health checks
4. **Maintain capability database**: Keep model capabilities locally

### Security

1. **Local network only**: Don't expose VibeProxy to internet
2. **SSH tunnel**: Use encrypted tunnel for remote access
3. **No sensitive data in logs**: Be careful with prompt logging

### Naming Conventions

| Convention | Description |
|------------|-------------|
| Dated models | `claude-opus-4-5-20251101` - Direct API, specific version |
| Undated models | `claude-opus-4.5` - Via Copilot, may update |
| Codex suffix | `gpt-5.2-codex` - Optimized for code |
| Mini suffix | `gpt-5-mini` - Lightweight variant |
| Max suffix | `gpt-5.1-codex-max` - Maximum capability |
| Thinking suffix | `claude-*-thinking-N` - Extended thinking with N tokens |
| Image suffix | `gemini-*-image-preview` - Enhanced vision |

---

## Quick Reference

### Common Commands

```bash
# List models
curl http://localhost:8317/v1/models | jq '.data[].id'

# Health check
curl -s http://localhost:8317/v1/models | head -c 50

# Test chat
curl -X POST http://localhost:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20250929","messages":[{"role":"user","content":"Hi"}]}'

# Count models
curl -s http://localhost:8317/v1/models | jq '.data | length'

# Filter by provider
curl -s http://localhost:8317/v1/models | jq '.data[] | select(.owned_by == "anthropic") | .id'
```

### Environment Variables

```bash
# For libraries expecting these
export OPENAI_API_BASE="http://localhost:8317/v1"
export OPENAI_API_KEY="dummy-not-used"
export ANTHROPIC_API_KEY="dummy-not-used"
```

### Docker Base URL

When running in Docker containers:

```
# ALL models use the same base URL
http://host.docker.internal:8317/v1
```

### Base URL (Universal)

> **Validated 2026-01-25:** One endpoint works for all models.

| Access Method | Base URL |
|---------------|----------|
| Local | `http://localhost:8317/v1` |
| Docker | `http://host.docker.internal:8317/v1` |
| LAN | `http://<mac-ip>:8317/v1` |

### Key Temperature Rules

| Model | Temperature |
|-------|-------------|
| `gpt-5*` | Must be `1` |
| `claude-*` | `0` to `1` |
| `gemini-*` | `0` to `2` |

### Vision-Capable Models Summary

| Provider | Vision Models |
|----------|---------------|
| Anthropic | All Claude 3+ models |
| OpenAI | All GPT-4+ models |
| Google | All Gemini models (enhanced: `gemini-3-pro-image-preview`) |

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-25 | 1.1.0 | **BREAKING:** Fixed incorrect base URL documentation. All models use `/v1/chat/completions`. Added Quick Start guide link. Validated all endpoints empirically. |
| 2026-01-25 | 1.0.0 | Initial comprehensive guide |

---

*This document is designed for LLM consumption. For human-readable quick start, see [VIBEPROXY-QUICKSTART.md](./VIBEPROXY-QUICKSTART.md).*
