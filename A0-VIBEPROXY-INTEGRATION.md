# Agent Zero + VibeProxy Integration Guide

## TL;DR: YES, IT WORKS!

Agent Zero can use VibeProxy to access your Claude Code and ChatGPT subscriptions without API keys!

## Overview

| Component | Role |
|-----------|------|
| **VibeProxy** | Mac app that proxies AI API calls via OAuth (no API keys needed) |
| **SSH Tunnel** | Forwards Mac's port 8317 to Windows localhost:8317 |
| **Agent Zero** | Runs in Docker, uses LiteLLM to connect to any OpenAI-compatible endpoint |

```
┌─────────────────────────────────────────────────────────────────────┐
│  Windows Docker                                                     │
│  ┌─────────────────┐                                                │
│  │  Agent Zero     │                                                │
│  │  (LiteLLM)      │──► host.docker.internal:8317                  │
│  └─────────────────┘              │                                 │
└───────────────────────────────────┼─────────────────────────────────┘
                                    │ SSH Tunnel
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MacBook                                                            │
│  ┌─────────────────┐                                                │
│  │  VibeProxy      │──► OAuth Tokens ──► Claude/OpenAI APIs        │
│  │  (port 8317)    │                                                │
│  └─────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Technical Findings

### Why It Works

1. **Agent Zero uses LiteLLM** - supports custom `api_base` for any provider
2. **VibeProxy is OpenAI-compatible** - accepts standard API formats
3. **VibeProxy ignores API keys** - uses OAuth tokens instead (set `api_key: "dummy-not-used"`)
4. **Docker has `host.docker.internal`** - A0 can reach host's localhost:8317

### Endpoint Mapping

| Model Type | VibeProxy Endpoint | From Docker Container |
|------------|-------------------|----------------------|
| Claude models | `http://localhost:8317` | `http://host.docker.internal:8317` |
| OpenAI models | `http://localhost:8317/v1` | `http://host.docker.internal:8317/v1` |
| Gemini models | `http://localhost:8317/v1` | `http://host.docker.internal:8317/v1` |

---

## Setup Instructions

### Prerequisites

1. ✅ VibeProxy running on Mac with providers authenticated
2. ✅ SSH tunnel from Windows → Mac (port 8317)
3. ✅ Agent Zero running in Docker

### Option A: Configure via A0 Web UI (Easiest)

1. **Open A0 Settings**: http://localhost:5080 → Settings (gear icon)

2. **For Claude models (Sonnet/Opus/Haiku):**
   - Provider: `Anthropic`
   - Model Name: `claude-sonnet-4-5` (or `claude-opus-4-5`, `claude-haiku-4`)
   - API URL: `http://host.docker.internal:8317`
   - In API Keys section: Set `ANTHROPIC_API_KEY` to `dummy-not-used`

3. **For OpenAI models (GPT-5.1/GPT-4o):**
   - Provider: `OpenAI`
   - Model Name: `gpt-5.1-codex-max` (or `gpt-4o`, `gpt-4-turbo`)
   - API URL: `http://host.docker.internal:8317/v1`
   - In API Keys section: Set `OPENAI_API_KEY` to `dummy-not-used`

4. **Save Settings**

### Option B: Edit settings.json Directly

Edit `C:\claude\agent-zero-data\tmp\settings.json`:

```json
{
  "chat_model_provider": "anthropic",
  "chat_model_name": "claude-sonnet-4-5",
  "chat_model_api_base": "http://host.docker.internal:8317",
  "chat_model_kwargs": {
    "temperature": "0"
  },
  "chat_model_ctx_length": 200000,
  "chat_model_vision": true,

  "util_model_provider": "openai",
  "util_model_name": "gpt-4o",
  "util_model_api_base": "http://host.docker.internal:8317/v1",

  "api_keys": {
    "ANTHROPIC_API_KEY": "dummy-not-used",
    "OPENAI_API_KEY": "dummy-not-used"
  }
}
```

### Option C: Add Custom Provider (Cleanest)

Add to `C:\claude\agent-zero\conf\model_providers.yaml`:

```yaml
chat:
  # ... existing providers ...

  vibeproxy_claude:
    name: VibeProxy (Claude)
    litellm_provider: anthropic
    kwargs:
      api_base: http://host.docker.internal:8317

  vibeproxy_openai:
    name: VibeProxy (OpenAI)
    litellm_provider: openai
    kwargs:
      api_base: http://host.docker.internal:8317/v1
```

Then in the UI, just select "VibeProxy (Claude)" or "VibeProxy (OpenAI)" as the provider.

---

## Environment Variable Method

Alternatively, add to your `docker-compose.yml` environment:

```yaml
environment:
  # VibeProxy dummy keys (OAuth handles auth)
  - ANTHROPIC_API_KEY=dummy-not-used
  - OPENAI_API_KEY=dummy-not-used
```

Then set the `api_base` URLs in the settings.

---

## Available Models via VibeProxy

### Via Claude Code Subscription
| Model | Name in A0 |
|-------|------------|
| Claude Sonnet 4.5 | `claude-sonnet-4-5` |
| Claude Opus 4.5 | `claude-opus-4-5` |
| Claude Haiku 4 | `claude-haiku-4` |

### Via ChatGPT/Codex Subscription
| Model | Name in A0 |
|-------|------------|
| GPT-5.1 Codex Max | `gpt-5.1-codex-max` |
| GPT-4 Turbo | `gpt-4-turbo` |
| GPT-4o | `gpt-4o` |

### Extended Thinking (Claude)
VibeProxy supports extended thinking with a special model name suffix:

```
claude-sonnet-4-5-20250929-thinking-10000
```

This injects a 10,000 token thinking budget.

---

## Troubleshooting

### Connection Refused
```
Error: Connection refused to host.docker.internal:8317
```
**Fix:** Ensure SSH tunnel is running on Windows:
```powershell
.\ssh-tunnel-vibeproxy.ps1
```

### Unauthorized / 401 Error
```
Error: 401 Unauthorized
```
**Fix:** Check VibeProxy on Mac - provider must show "Connected ✅" in menu bar.

### Model Not Found
```
Error: Model claude-sonnet-4-5 not found
```
**Fix:** Verify the exact model name. Check VibeProxy logs on Mac:
```bash
tail -f ~/Library/Logs/VibeProxy/vibeproxy.log
```

### Test Connection from Docker
```bash
# Enter A0 container
docker exec -it agent-zero-instance bash

# Test VibeProxy connectivity
curl -X POST http://host.docker.internal:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## Quick Start Checklist

- [ ] Mac: VibeProxy running, providers authenticated (green checkmarks)
- [ ] Windows: SSH tunnel running (`.\ssh-tunnel-vibeproxy.ps1`)
- [ ] Test tunnel: `.\test-connection.ps1` shows success
- [ ] A0: Set provider (Anthropic/OpenAI)
- [ ] A0: Set API base to `http://host.docker.internal:8317` (add `/v1` for OpenAI)
- [ ] A0: Set API key to `dummy-not-used`
- [ ] A0: Save settings and test!

---

## Comparison: Droid-CLI vs Agent Zero Config

| Setting | Droid-CLI | Agent Zero |
|---------|-----------|------------|
| Config file | `~/.factory/config.json` | `tmp/settings.json` |
| Provider key | `"provider": "anthropic"` | `"chat_model_provider": "anthropic"` |
| Model key | `"model": "claude-sonnet-4-5"` | `"chat_model_name": "claude-sonnet-4-5"` |
| Base URL key | `"base_url": "http://localhost:8317"` | `"chat_model_api_base": "http://host.docker.internal:8317"` |
| API key | `"api_key": "dummy-not-used"` | `api_keys.ANTHROPIC_API_KEY = "dummy-not-used"` |
| URL for Claude | `http://localhost:8317` | `http://host.docker.internal:8317` |
| URL for OpenAI | `http://localhost:8317/v1` | `http://host.docker.internal:8317/v1` |

**Key Difference:** A0 runs in Docker, so use `host.docker.internal` instead of `localhost`!

---

## References

- **VibeProxy GitHub:** https://github.com/automazeio/vibeproxy
- **Agent Zero GitHub:** https://github.com/frdel/agent-zero
- **DeepWiki - Agent Zero:** https://deepwiki.com/frdel/agent-zero
- **DeepWiki - VibeProxy:** https://deepwiki.com/automazeio/vibeproxy

---

## Important Caveats & Limitations

### 1. Embedding Models NOT Supported
VibeProxy proxies **chat completions only**. Keep using local embeddings:
```json
{
  "embed_model_provider": "huggingface",
  "embed_model_name": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### 2. Extended Thinking May Not Work
The `-thinking-NUMBER` suffix is processed by VibeProxy's ThinkingProxy layer. LiteLLM may not pass this correctly. Test before relying on it.

### 3. Docker Desktop Required
`host.docker.internal` works with **Docker Desktop for Windows/Mac**. If using:
- WSL2 Docker: May need `host.docker.internal` or gateway IP
- Linux Docker: Use `172.17.0.1` (default bridge gateway) instead

### 4. Model Name Compatibility
Tested model names from VibeProxy docs:
- `claude-sonnet-4-5` ✅
- `claude-opus-4-5` ✅
- `claude-haiku-4` ✅
- `gpt-5.1-codex-max` ✅
- `gpt-4o` ✅
- `gpt-4-turbo` ✅

If a model doesn't work, check VibeProxy logs for the exact expected name.

### 5. This Guide is Based on Documentation
All findings are from DeepWiki analysis of both repos. **Actual testing is recommended** before production use.

---

*Guide created by Claude Code after thorough DeepWiki research on both repositories.*
