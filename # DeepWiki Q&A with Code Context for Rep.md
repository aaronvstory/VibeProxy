# DeepWiki Q&A with Code Context for Repository: aaronvstory/VibeProxy


## Q1

woorth updating with this
??
# OpenClaw + VibeProxy Integration Guide

**Created:** 2026-01-31
**Last Updated:** 2026-02-01
**Status:** Working Configuration

---

## TL;DR - The Five Golden Rules

1. **Use `api: "openai-completions"`** - NOT `openai-responses` (causes JSON parsing errors with Claude)
2. **Add `vibeproxy:default` to auth-profiles.json** - Even though apiKey is in models config
3. **Add `models.providers.vibeproxy`** - Required for custom model names to be recognized
4. **Avoid Antigravity as primary** - `gemini-claude-*` has tiny quotas (~10-15 req/hr)
5. **Use GPT-5.2 for agentic work** - Higher rate limits, more reliable for tool-heavy sessions

### Minimum Working Config

```json
// ~/.clawdbot/openclaw.json (and clawdbot.json)
{
  "models": {
    "mode": "merge",
    "providers": {
      "vibeproxy": {
        "baseUrl": "http://localhost:8317/v1",
        "apiKey": "vibeproxy",
        "api": "openai-completions",
        "models": [{"id": "claude-opus-4.5", "name": "Claude Opus 4.5", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 8192}]
      }
    }
  },
  "agents": {"defaults": {"model": {"primary": "vibeproxy/claude-opus-4.5"}}}
}
```

```json
// ~/.clawdbot/agents/main/agent/auth-profiles.json
{
  "version": 1,
  "profiles": {"vibeproxy:default": {"type": "token", "provider": "vibeproxy", "token": "vibeproxy"}},
  "lastGood": {"vibeproxy": "vibeproxy:default"},
  "usageStats": {}
}
```

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [SSH Tunnel Setup](#ssh-tunnel-setup)
4. [Complete Model Catalog](#complete-model-catalog)
5. [Step-by-Step Initial Setup](#step-by-step-initial-setup-from-scratch)
6. [Alternative Configuration Examples](#alternative-configuration-examples)
7. [Configuration Files](#configuration-files)
8. [Custom Provider Schema](#custom-provider-schema)
9. [Auth Profiles](#auth-profiles)
10. [Gateway Management](#gateway-management)
11. [Switching Between VibeProxy and Native OAuth](#switching-between-vibeproxy-and-native-oauth)
12. [Common Errors and Fixes](#common-errors-and-fixes)
13. [Troubleshooting Checklist](#troubleshooting-checklist)
14. [Quick Reference Commands](#quick-reference-commands)
15. [Root Cause Analysis](#root-cause-analysis-complete-picture)
16. [DO NOTs](#do-nots-things-that-dont-work)
17. [Known Limitations and Caveats](#known-limitations-and-caveats)
18. [Debugging Session History](#debugging-session-history-2026-01-31)
19. [Appendix: Configuration Files](#appendix-complete-working-configuration-files)
20. [Quick Diagnostic Script](#quick-diagnostic-script)

---

## Overview

This guide documents how to configure OpenClaw (formerly Clawdbot) to route all model requests through VibeProxy, a local proxy that provides unified authentication for Claude/OpenAI models via SSH tunnel.

### Key Concepts

- **VibeProxy** handles ALL authentication - no need for OpenClaw's OAuth/tokens
- **OpenClaw and Clawdbot are the SAME thing** - rebranded due to legal issues, configs are shared
- **Both CLI tools exist**: `openclaw` and `clawdbot` - use either, they share config
- **Config files are symlinked**: `~/.openclaw` -> `~/.clawdbot`

---

## Architecture

### Option A: Local VibeProxy (Recommended)

VibeProxy runs directly on DMBP16:

```
┌─────────────────────────────────────────────┐
│                   DMBP16                    │
│                                             │
│  ┌─────────────┐      ┌─────────────────┐  │
│  │  OpenClaw   │      │   VibeProxy     │  │
│  │  Gateway    │─────►│   Menu Bar App  │  │
│  │  Port 18789 │ 8317 │   Port 8317     │  │
│  └─────────────┘      └─────────────────┘  │
│                              │              │
└──────────────────────────────│──────────────┘
                               ▼
                        ┌─────────────────┐
                        │  Anthropic API  │
                        │  OpenAI API     │
                        │  Google AI      │
                        │  GitHub Copilot │
                        └─────────────────┘
```

**Setup:**
1. Install VibeProxy.app (copy from DMBP14 or download)
2. Copy auth config: `scp -r danielba@192.168.50.71:/Users/danielba/.cli-proxy-api ~/.cli-proxy-api`
3. Launch VibeProxy.app, click "Start Server"
4. Verify: `curl http://localhost:8317/v1/models`

### Option B: SSH Tunnel (Legacy)

VibeProxy runs on DMBP14, tunneled to DMBP16:

```
┌─────────────────┐     SSH Tunnel      ┌─────────────────┐
│     DMBP16      │ ←────────────────── │     DMBP14      │
│  (This Machine) │    Port 8317        │  (VibeProxy)    │
│                 │                     │                 │
│  OpenClaw       │                     │  VibeProxy      │
│  Gateway        │──── HTTP ──────────►│  Server         │
│  Port 18789     │  localhost:8317     │                 │
└─────────────────┘                     └─────────────────┘
                                               │
                                               ▼
                                        ┌─────────────────┐
                                        │  Anthropic API  │
                                        │  OpenAI API     │
                                        └─────────────────┘
```

---

## SSH Tunnel Setup

### Starting the Tunnel

```bash
# Basic tunnel command
ssh -L 8317:localhost:8317 danielba@192.168.50.71

# Production tunnel with keepalive and auto-reconnect options
ssh -o BatchMode=yes \
    -o ConnectTimeout=5 \
    -o ServerAliveInterval=5 \
    -o ServerAliveCountMax=1 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=accept-new \
    -f -N \
    -L 8317:localhost:8317 \
    danielba@192.168.50.71
```

### Verifying the Tunnel

```bash
# Check if port 8317 is listening
lsof -i :8317

# Expected output:
# COMMAND   PID USER   FD   TYPE  DEVICE SIZE/OFF NODE NAME
# ssh     XXXXX molt    5u  IPv6  ...     0t0  TCP localhost:8317 (LISTEN)

# Test VibeProxy directly
curl -s "http://localhost:8317/v1/models" | jq '.data[].id'

# Test a chat completion
curl -s "http://localhost:8317/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer vibeproxy" \
  -d '{"model":"claude-opus-4.5","messages":[{"role":"user","content":"Say hi"}],"max_tokens":20}'
```

### Available VibeProxy Models (34 total)

```bash
# Query live: curl -s "http://localhost:8317/v1/models" | jq -r '.data[].id' | sort

# Top-tier models by provider:
Claude:  claude-opus-4.5, claude-sonnet-4.5, claude-haiku-4.5
GPT:     gpt-5.2, gpt-5.2-codex, gpt-5.1, gpt-5.1-codex
Gemini:  gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro
Other:   qwen3-coder-plus, qwen3-coder-flash, grok-code-fast-1
```

---

## Complete Model Catalog

### How to Query Available Models

```bash
# List all model IDs
curl -s "http://localhost:8317/v1/models" | jq -r '.data[].id' | sort

# List models with their provider (owned_by)
curl -s "http://localhost:8317/v1/models" | jq -r '.data[] | "\(.owned_by)\t\(.id)"' | sort

# Count total models
curl -s "http://localhost:8317/v1/models" | jq '.data | length'

# Get full model details
curl -s "http://localhost:8317/v1/models" | jq '.data[]'
```

### All VibeProxy Models (42 total, as of 2026-02-01)

**IMPORTANT:** All models use the prefix `vibeproxy/` in OpenClaw config. Example: `vibeproxy/claude-opus-4.5`

**Providers:** anthropic (8), antigravity (10), github-copilot (9), google (1), openai (9), qwen (3)

#### Claude Models (13 models)

| Model ID | Tier | Notes |
|----------|------|-------|
| **Top Tier (Opus 4.5)** |
| `claude-opus-4.5` | Flagship | Best reasoning, extended thinking, vision |
| `claude-opus-4-5-20251101` | Flagship | Dated version of Opus 4.5 |
| **High Tier (Opus 4.1/4)** |
| `claude-opus-4.1` | High | Previous gen flagship |
| `claude-opus-4-1-20250805` | High | Dated version |
| `claude-opus-4-20250514` | High | Opus 4.0 |
| **Mid Tier (Sonnet)** |
| `claude-sonnet-4.5` | Mid | Fast, capable, cost-effective |
| `claude-sonnet-4-5-20250929` | Mid | Dated version |
| `claude-sonnet-4` | Mid | Previous sonnet |
| `claude-sonnet-4-20250514` | Mid | Dated version |
| `claude-3-7-sonnet-20250219` | Mid | Claude 3.7 Sonnet |
| **Fast Tier (Haiku)** |
| `claude-haiku-4.5` | Fast | Fastest Claude, good for simple tasks |
| `claude-haiku-4-5-20251001` | Fast | Dated version |
| `claude-3-5-haiku-20241022` | Fast | Claude 3.5 Haiku |

#### GPT Models (11 models)

| Model ID | Tier | Notes |
|----------|------|-------|
| **Top Tier (5.2)** |
| `gpt-5.2` | Flagship | Latest GPT, strong reasoning |
| `gpt-5.2-codex` | Flagship | Code-optimized 5.2 |
| **High Tier (5.1)** |
| `gpt-5.1` | High | Previous flagship |
| `gpt-5.1-codex` | High | Code-optimized 5.1 |
| `gpt-5.1-codex-max` | High | Extended context codex |
| `gpt-5.1-codex-mini` | High | Faster codex variant |
| **Mid Tier (5.0)** |
| `gpt-5` | Mid | GPT 5.0 base |
| `gpt-5-codex` | Mid | Code-optimized 5.0 |
| `gpt-5-mini` | Mid | Faster 5.0 variant |
| `gpt-5-codex-mini` | Mid | Fast code model |
| **Legacy** |
| `gpt-4.1` | Legacy | GPT 4.1 |

#### Gemini Models (5 models)

| Model ID | Tier | Notes |
|----------|------|-------|
| **Top Tier (3.0 Preview)** |
| `gemini-3-pro-preview` | Flagship | Latest Gemini, 1M context |
| `gemini-3-flash-preview` | Flagship | Fast Gemini 3.0 |
| **High Tier (2.5)** |
| `gemini-2.5-pro` | High | Production Gemini, 1M context |
| `gemini-2.5-flash` | High | Fast production Gemini |
| `gemini-2.5-flash-lite` | High | Ultra-fast, lower capability |

#### Antigravity Models (10 models) - Google AI Studio

| Model ID | Tier | Notes |
|----------|------|-------|
| **Gemini Native** |
| `gemini-3-pro-preview` | Flagship | Latest Gemini via Antigravity |
| `gemini-3-flash-preview` | Fast | Fast Gemini 3.0 |
| `gemini-3-pro-image-preview` | Flagship | Image generation capable |
| `gemini-2.5-flash` | Mid | Production Gemini |
| `gemini-2.5-flash-lite` | Fast | Ultra-lightweight |
| **Hybrid Models** (Claude via Gemini) |
| `gemini-claude-opus-4-5-thinking` | Flagship | Claude Opus with extended thinking |
| `gemini-claude-sonnet-4-5` | Mid | Claude Sonnet via Antigravity |
| `gemini-claude-sonnet-4-5-thinking` | Mid | Sonnet with thinking |
| **Other** |
| `gpt-oss-120b-medium` | Mid | Open-source GPT variant |
| `tab_flash_lite_preview` | Fast | Experimental fast model |

#### Other Models (5 models)

| Model ID | Provider | Notes |
|----------|----------|-------|
| `grok-code-fast-1` | GitHub Copilot | Grok code model |
| `oswe-vscode-prime` | GitHub Copilot | VS Code optimized |
| `qwen3-coder-flash` | Qwen | Fast Qwen coder |
| `qwen3-coder-plus` | Qwen | Enhanced Qwen coder |
| `vision-model` | Qwen | Vision specialist |

### Model Recommendations (Updated)

| Use Case | Recommended Model | Why |
|----------|-------------------|-----|
| **Best overall** | `claude-opus-4.5` | Top reasoning, tools, extended thinking |
| **Best GPT** | `gpt-5.2` | Latest OpenAI flagship |
| **Best Gemini** | `gemini-3-pro-preview` | Latest Google flagship |
| **Claude when rate limited** | `gemini-claude-opus-4-5-thinking` | Claude via Antigravity (separate quota) |
| **Fast + capable** | `claude-sonnet-4.5` | Good balance |
| **Fastest Claude** | `claude-haiku-4.5` | Quick responses |
| **Fastest Gemini** | `gemini-3-flash-preview` | Very fast |
| **Code specialist** | `gpt-5.2-codex` | Optimized for code |
| **Huge context** | `gemini-3-pro-preview` | 1M tokens |
| **Image generation** | `gemini-3-pro-image-preview` | Native image gen |

### Model Prefix Rules

**In OpenClaw config, ALL VibeProxy models use the same prefix:**

```
vibeproxy/<model-id>
```

Examples:
- `vibeproxy/claude-opus-4.5`
- `vibeproxy/gpt-5.2`
- `vibeproxy/gemini-3-pro-preview`
- `vibeproxy/qwen3-coder-plus`

**DO NOT use:**
- ~~`anthropic/claude-opus-4.5`~~ (wrong - that's for direct Anthropic API)
- ~~`openai/gpt-5.2`~~ (wrong - that's for direct OpenAI API)
- ~~`openai:vibeproxy/model`~~ (wrong - invalid format)

### How to Test Models Without User Interaction

```bash
# === Test via curl (direct to VibeProxy) ===

# Simple test - should return a response
curl -s "http://localhost:8317/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer vibeproxy" \
  -d '{"model":"claude-opus-4.5","messages":[{"role":"user","content":"Say hello"}],"max_tokens":50}' \
  | jq -r '.choices[0].message.content'

# Test a different model
curl -s "http://localhost:8317/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer vibeproxy" \
  -d '{"model":"gpt-5.2","messages":[{"role":"user","content":"Say hello"}],"max_tokens":50}' \
  | jq -r '.choices[0].message.content'

# Test Gemini 3
curl -s "http://localhost:8317/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer vibeproxy" \
  -d '{"model":"gemini-3-pro-preview","messages":[{"role":"user","content":"Say hello"}],"max_tokens":50}' \
  | jq -r '.choices[0].message.content'


# === Test via OpenClaw CLI ===

# Test with a fresh session (avoids corrupted session issues)
openclaw agent --local --session-id "test-$(date +%s)" -m "Say hello" --json

# Test a specific model by temporarily changing config
# (Or just test via curl first to avoid config changes)


# === Quick validation script ===

# Save as ~/scripts/test-vibeproxy-models.sh
cat << 'EOF'
#!/bin/bash
MODELS=("claude-opus-4.5" "gpt-5.2" "gemini-3-pro-preview" "claude-sonnet-4.5")
for model in "${MODELS[@]}"; do
  echo -n "Testing $model: "
  RESP=$(curl -s "http://localhost:8317/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer vibeproxy" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"max_tokens\":10}" \
    2>/dev/null)
  if echo "$RESP" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    echo "✓ OK"
  else
    echo "✗ FAILED"
    echo "$RESP" | head -c 100
  fi
done
EOF
```

---

## Step-by-Step Initial Setup (From Scratch)

### Prerequisites

1. **SSH Access to VibeProxy host (DMBP14)**
   ```bash
   ssh danielba@192.168.50.71  # Should work without password
   ```

2. **OpenClaw/Clawdbot installed**
   ```bash
   which openclaw  # or: which clawdbot
   ```

### Step 1: Start the SSH Tunnel

```bash
# Start the tunnel in background
ssh -f -N -L 8317:localhost:8317 danielba@192.168.50.71

# Verify it's working
curl -s "http://localhost:8317/v1/models" | jq '.data[0].id'
# Should output: "claude-opus-4.5" or similar
```

### Step 2: Configure the VibeProxy Provider

Edit `~/.clawdbot/openclaw.json`:

```bash
# Using jq to add vibeproxy provider (or edit manually)
cat ~/.clawdbot/openclaw.json | jq '.models = {
  "mode": "merge",
  "providers": {
    "vibeproxy": {
      "baseUrl": "http://localhost:8317/v1",
      "apiKey": "vibeproxy",
      "api": "openai-completions",
      "models": [
        {"id": "claude-opus-4.5", "name": "Claude Opus 4.5", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 8192},
        {"id": "claude-sonnet-4.5", "name": "Claude Sonnet 4.5", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 8192},
        {"id": "gpt-5.2", "name": "GPT 5.2", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 16384},
        {"id": "gpt-5.2-codex", "name": "GPT 5.2 Codex", "input": ["text"], "contextWindow": 200000, "maxTokens": 16384},
        {"id": "gemini-3-pro-preview", "name": "Gemini 3.0 Pro", "input": ["text", "image"], "contextWindow": 1000000, "maxTokens": 8192},
        {"id": "gemini-3-flash-preview", "name": "Gemini 3.0 Flash", "input": ["text", "image"], "contextWindow": 1000000, "maxTokens": 8192}
      ]
    }
  }
}' > /tmp/openclaw.json && mv /tmp/openclaw.json ~/.clawdbot/openclaw.json
```

### Step 3: Set the Primary Model

Edit `~/.clawdbot/openclaw.json` - set `agents.defaults.model.primary`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "vibeproxy/claude-opus-4.5",
        "fallbacks": [
          "vibeproxy/claude-sonnet-4.5",
          "vibeproxy/gpt-5.2"
        ]
      }
    }
  }
}
```

**IMPORTANT:** Also update `~/.clawdbot/clawdbot.json` with the same values!

### Step 4: Add Auth Profile

Edit `~/.clawdbot/agents/main/agent/auth-profiles.json`:

```json
{
  "version": 1,
  "profiles": {
    "vibeproxy:default": {
      "type": "token",
      "provider": "vibeproxy",
      "token": "vibeproxy"
    }
  },
  "lastGood": {
    "vibeproxy": "vibeproxy:default"
  },
  "usageStats": {}
}
```

### Step 5: Start the Gateway

```bash
# Kill any existing gateway
pkill -9 -f "openclaw.*gateway"
pkill -9 -f "clawdbot.*gateway"

# Start fresh with nohup (prevents EPIPE crashes)
nohup openclaw gateway --force > /dev/null 2>&1 &

# Wait for startup
sleep 5

# Verify
pgrep -f "openclaw.*gateway" && echo "Gateway running!"
grep "agent model" ~/.clawdbot/logs/gateway.log | tail -1
# Should show: [gateway] agent model: vibeproxy/claude-opus-4.5
```

### Step 6: Test

```bash
# Quick test
openclaw agent --local --session-id test -m "Say hello" --json

# If it works, you'll see a response. If not, check:
tail -20 ~/.clawdbot/logs/gateway.err.log
```

---

## Alternative Configuration Examples

### GPT-5.2 as Primary Model

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "vibeproxy": {
        "baseUrl": "http://localhost:8317/v1",
        "apiKey": "vibeproxy",
        "api": "openai-completions",
        "models": [
          {"id": "gpt-5.2", "name": "GPT 5.2", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 16384},
          {"id": "gpt-5.1", "name": "GPT 5.1", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 16384},
          {"id": "claude-opus-4.5", "name": "Claude Opus 4.5", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 8192}
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "vibeproxy/gpt-5.2",
        "fallbacks": ["vibeproxy/gpt-5.1", "vibeproxy/claude-opus-4.5"]
      },
      "models": {
        "vibeproxy/gpt-5.2": {"alias": "gpt"},
        "vibeproxy/gpt-5.1": {"alias": "gpt51"},
        "vibeproxy/claude-opus-4.5": {"alias": "opus"}
      }
    }
  }
}
```

### Gemini 3.0 Pro as Primary Model

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "vibeproxy": {
        "baseUrl": "http://localhost:8317/v1",
        "apiKey": "vibeproxy",
        "api": "openai-completions",
        "models": [
          {"id": "gemini-3-pro-preview", "name": "Gemini 3.0 Pro", "input": ["text", "image"], "contextWindow": 1000000, "maxTokens": 8192},
          {"id": "gemini-3-flash-preview", "name": "Gemini 3.0 Flash", "input": ["text", "image"], "contextWindow": 1000000, "maxTokens": 8192},
          {"id": "claude-opus-4.5", "name": "Claude Opus 4.5", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 8192}
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "vibeproxy/gemini-3-pro-preview",
        "fallbacks": ["vibeproxy/gemini-3-flash-preview", "vibeproxy/claude-opus-4.5"]
      },
      "models": {
        "vibeproxy/gemini-3-pro-preview": {"alias": "gemini"},
        "vibeproxy/gemini-3-flash-preview": {"alias": "flash"},
        "vibeproxy/claude-opus-4.5": {"alias": "opus"}
      }
    }
  }
}
```

### All Top Models (Maximum Flexibility)

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "vibeproxy": {
        "baseUrl": "http://localhost:8317/v1",
        "apiKey": "vibeproxy",
        "api": "openai-completions",
        "models": [
          {"id": "claude-opus-4.5", "name": "Claude Opus 4.5", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 8192},
          {"id": "claude-sonnet-4.5", "name": "Claude Sonnet 4.5", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 8192},
          {"id": "claude-haiku-4.5", "name": "Claude Haiku 4.5", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 8192},
          {"id": "gpt-5.2", "name": "GPT 5.2", "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 16384},
          {"id": "gpt-5.2-codex", "name": "GPT 5.2 Codex", "input": ["text"], "contextWindow": 200000, "maxTokens": 16384},
          {"id": "gemini-3-pro-preview", "name": "Gemini 3.0 Pro", "input": ["text", "image"], "contextWindow": 1000000, "maxTokens": 8192},
          {"id": "gemini-3-flash-preview", "name": "Gemini 3.0 Flash", "input": ["text", "image"], "contextWindow": 1000000, "maxTokens": 8192},
          {"id": "qwen3-coder-plus", "name": "Qwen3 Coder Plus", "input": ["text"], "contextWindow": 128000, "maxTokens": 8192},
          {"id": "grok-code-fast-1", "name": "Grok Code Fast", "input": ["text"], "contextWindow": 128000, "maxTokens": 8192}
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "vibeproxy/claude-opus-4.5",
        "fallbacks": ["vibeproxy/gpt-5.2", "vibeproxy/gemini-3-pro-preview"]
      },
      "models": {
        "vibeproxy/claude-opus-4.5": {"alias": "opus"},
        "vibeproxy/claude-sonnet-4.5": {"alias": "sonnet"},
        "vibeproxy/claude-haiku-4.5": {"alias": "haiku"},
        "vibeproxy/gpt-5.2": {"alias": "gpt"},
        "vibeproxy/gpt-5.2-codex": {"alias": "codex"},
        "vibeproxy/gemini-3-pro-preview": {"alias": "gemini"},
        "vibeproxy/gemini-3-flash-preview": {"alias": "flash"},
        "vibeproxy/qwen3-coder-plus": {"alias": "qwen"},
        "vibeproxy/grok-code-fast-1": {"alias": "grok"}
      }
    }
  }
}
```

### Quick Model Switch Commands

Once configured with aliases, you can switch models:

```bash
# Switch to GPT
openclaw config set agents.defaults.model.primary vibeproxy/gpt-5.2

# Switch to Gemini 3.0
openclaw config set agents.defaults.model.primary vibeproxy/gemini-3-pro-preview

# Switch to Claude via Antigravity (when direct Claude is rate limited)
openclaw config set agents.defaults.model.primary vibeproxy/gemini-claude-opus-4-5-thinking

# Switch back to Claude
openclaw config set agents.defaults.model.primary vibeproxy/claude-opus-4.5

# Restart gateway to apply
pkill -9 -f "openclaw.*gateway" && nohup openclaw gateway --force > /dev/null 2>&1 &
```

### Fallback Strategy When Rate Limited

**WARNING:** Antigravity models (`gemini-claude-*`) have VERY LOW quotas (~10-15 requests/hour). They are NOT suitable for agentic workloads with many tool calls.

**Recommended fallback order:**
```json
"fallbacks": [
  "vibeproxy/gpt-5.2",           // GitHub Copilot - high limits
  "vibeproxy/claude-sonnet-4.5",  // Direct Anthropic (separate from opus)
  "vibeproxy/gemini-3-pro-preview" // Google Gemini
]
```

**Avoid as primary/early fallback:**
- `vibeproxy/gemini-claude-opus-4-5-thinking` - tiny quota, will rate limit fast
- `vibeproxy/gemini-claude-sonnet-4-5-thinking` - same issue

These Antigravity models are Claude routed through Google AI Studio with strict rate limits. Only use as last resort.

---

## Configuration Files

### File Locations

| File | Path | Purpose |
|------|------|---------|
| Main Config | `~/.clawdbot/openclaw.json` | Primary configuration (gateway reads this) |
| Alt Config | `~/.clawdbot/clawdbot.json` | Also read, keep in sync |
| Auth Profiles | `~/.clawdbot/agents/main/agent/auth-profiles.json` | Authentication credentials |
| Models JSON | `~/.clawdbot/agents/main/agent/models.json` | Auto-generated from config |
| Sessions | `~/.clawdbot/agents/main/sessions/*.jsonl` | Session history |
| Gateway Log | `~/.clawdbot/logs/gateway.log` | Gateway activity |
| Error Log | `~/.clawdbot/logs/gateway.err.log` | Gateway errors |
| Runtime Log | `/tmp/clawdbot/clawdbot-YYYY-MM-DD.log` | Detailed runtime log |

### CRITICAL: Keep Both Config Files in Sync

Both `openclaw.json` and `clawdbot.json` are read. If they have different values, you'll get inconsistent behavior. The `agents.defaults.model.primary` field MUST match in both files.

---

## Custom Provider Schema

### Required Fields (from DeepWiki docs)

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "vibeproxy": {
        "baseUrl": "http://localhost:8317/v1",
        "apiKey": "vibeproxy",
        "api": "openai-completions",
        "models": [
          {
            "id": "claude-opus-4.5",
            "name": "Claude Opus 4.5",
            "input": ["text", "image"],
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
  }
}
```

### CRITICAL: The `api` Field

**Valid values:**
- `"openai-completions"` - For /v1/chat/completions endpoint **(USE THIS ONE FOR VIBEPROXY)**
- `"openai-responses"` - For /v1/responses endpoint (DO NOT USE - causes JSON errors with Claude)

**INVALID values that will fail:**
- `"openai-chat"` - Does not exist, validation error
- `"openai"` - Does not exist, validation error
- Omitting the field - Will cause auth lookup failures

### WARNING: openai-responses Breaks Claude Tool Calls

Using `api: "openai-responses"` with Claude models through VibeProxy causes JSON parsing errors:
```
Unexpected non-whitespace character after JSON at position 70
```

This happens because the `/v1/responses` endpoint's streaming format isn't correctly translated for Claude's tool call responses. The tool arguments get concatenated into invalid JSON like:
```
{"query": "test", "limit": 10}{"activeMinutes": 1440}
```

**Always use `api: "openai-completions"` for VibeProxy.**

### Full Working openclaw.json Example

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "vibeproxy": {
        "baseUrl": "http://localhost:8317/v1",
        "apiKey": "vibeproxy",
        "api": "openai-completions",
        "models": [
          {
            "id": "claude-opus-4.5",
            "name": "Claude Opus 4.5",
            "input": ["text", "image"],
            "contextWindow": 200000,
            "maxTokens": 8192
          },
          {
            "id": "claude-sonnet-4.5",
            "name": "Claude Sonnet 4.5",
            "input": ["text", "image"],
            "contextWindow": 200000,
            "maxTokens": 8192
          },
          {
            "id": "gpt-5.2",
            "name": "GPT 5.2",
            "input": ["text", "image"],
            "contextWindow": 200000,
            "maxTokens": 16384
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "vibeproxy/claude-opus-4.5",
        "fallbacks": [
          "vibeproxy/claude-sonnet-4.5",
          "vibeproxy/gpt-5.2"
        ]
      },
      "models": {
        "vibeproxy/claude-opus-4.5": { "alias": "opus" },
        "vibeproxy/claude-sonnet-4.5": { "alias": "sonnet" },
        "vibeproxy/gpt-5.2": { "alias": "gpt" }
      }
    }
  }
}
```

---

## Auth Profiles

### Location

`~/.clawdbot/agents/main/agent/auth-profiles.json`

### Required Entry for VibeProxy

```json
{
  "version": 1,
  "profiles": {
    "vibeproxy:default": {
      "type": "token",
      "provider": "vibeproxy",
      "token": "vibeproxy"
    }
  },
  "lastGood": {
    "vibeproxy": "vibeproxy:default"
  },
  "usageStats": {}
}
```

### CRITICAL: The vibeproxy:default Profile

Even though `apiKey` is set in the models config, the gateway's auth system ALSO requires an entry in auth-profiles.json. Without it, you get:

```
No API key found for provider "vibeproxy"
```

### Clearing Cooldowns

If a profile fails, OpenClaw puts it in "cooldown". To clear:

```json
"usageStats": {}
```

Or remove the specific entry with `cooldownUntil` timestamp.

---

## Gateway Management

### Starting the Gateway

```bash
# ALWAYS use nohup to prevent EPIPE crash
nohup openclaw gateway --force > /dev/null 2>&1 &

# Or with logging
nohup openclaw gateway --force > /tmp/openclaw-gateway.log 2>&1 &

# Wait and verify
sleep 5
pgrep -f "openclaw.*gateway" && echo "Gateway running"
```

### Stopping the Gateway

```bash
# Graceful stop
openclaw gateway stop

# Force kill
pkill -9 -f "openclaw.*gateway"
pkill -9 -f "clawdbot.*gateway"
```

### Checking Gateway Status

```bash
# Process check
pgrep -f "openclaw.*gateway"

# Port check
lsof -i :18789

# View current model
grep "agent model" ~/.clawdbot/logs/gateway.log | tail -1
```

### Gateway Won't Start?

```bash
# Kill everything and restart
pkill -9 -f "openclaw.*gateway"
pkill -9 -f "clawdbot.*gateway"
sleep 2
nohup openclaw gateway --force > /dev/null 2>&1 &
```

---

## Switching Between VibeProxy and Native OAuth

### To Use VibeProxy

1. Ensure SSH tunnel is running
2. Set in both config files:
   ```json
   "primary": "vibeproxy/claude-opus-4.5"
   ```
3. Ensure `vibeproxy:default` exists in auth-profiles.json
4. Restart gateway

### To Use Native OAuth (Anthropic/OpenAI direct)

1. Set in both config files:
   ```json
   "primary": "anthropic/claude-opus-4-5"
   ```
   or
   ```json
   "primary": "openai-codex/gpt-5.2"
   ```
2. Ensure OAuth tokens are valid:
   ```bash
   openclaw models  # Check token status
   claude login     # Refresh Anthropic OAuth
   codex login      # Refresh OpenAI Codex OAuth
   ```
3. Restart gateway

### Model Name Formats

| Provider | Format | Example |
|----------|--------|---------|
| VibeProxy | `vibeproxy/model-name` | `vibeproxy/claude-opus-4.5` |
| Anthropic | `anthropic/model-name` | `anthropic/claude-opus-4-5` |
| OpenAI Codex | `openai-codex/model-name` | `openai-codex/gpt-5.2` |

**Note:** Anthropic model IDs use dashes (`claude-opus-4-5`), VibeProxy uses dots (`claude-opus-4.5`).

---

## Common Errors and Fixes

### Error: "No API key found for provider vibeproxy"

**Cause:** Missing `vibeproxy:default` in auth-profiles.json

**Fix:** Add to `~/.clawdbot/agents/main/agent/auth-profiles.json`:
```json
"vibeproxy:default": {
  "type": "token",
  "provider": "vibeproxy",
  "token": "vibeproxy"
}
```

### Error: "Unknown model: openai:vibeproxy/claude-opus-4.5"

**Cause:** Invalid model prefix format

**Fix:** Use `vibeproxy/model-name`, NOT `openai:vibeproxy/model-name`

### Error: "400 tool_use.id: String should match pattern '^[a-zA-Z0-9_-]+$'"

**Cause:** Session contains tool call IDs with invalid characters. This happens because:
- VibeProxy is a transparent proxy - it doesn't transform requests
- OpenClaw generates tool IDs in OpenAI format (which allows more characters)
- Anthropic's API has stricter validation (only `^[a-zA-Z0-9_-]+$`)
- Tool IDs are stored in session history, so corrupted IDs persist

**Fix Option 1 - Clear the corrupted session (what we did):**
```bash
# Find the session ID from logs
grep "sessionId=" ~/.clawdbot/logs/gateway.log | tail -5

# Remove the session file
rm ~/.clawdbot/agents/main/sessions/<session-id>.jsonl
rm ~/.clawdbot/agents/main/sessions/<session-id>.jsonl.lock

# Restart gateway
pkill -9 -f "openclaw.*gateway" && nohup openclaw gateway --force > /dev/null 2>&1 &
```

**Fix Option 2 - Disable function calling? (Devin's suggestion - DOESN'T WORK):**

Devin suggested disabling tool calling, but:
1. **OpenClaw has NO `supportsToolCalling` compat field** - checked via DeepWiki, it doesn't exist
2. **Available compat fields are:** `supportsStore`, `supportsDeveloperRole`, `supportsReasoningEffort`, `maxTokensField`
3. **`tools.byProvider` exists** but restricts which tools are available - would cripple the agent
4. **Not needed anyway** - clearing the session fixes the issue and tools work fine after

**Verified working (2026-02-01):**
```
Provider: vibeproxy
Model: claude-opus-4.5
Tool used: exec
Result: Success - tools work correctly with fresh sessions
```

**Root Cause (from Devin's analysis):**
- VibeProxy doesn't inspect or modify requests - it's transparent
- This is an OpenClaw/Anthropic format mismatch, not a VibeProxy bug
- Switching `api` type doesn't fix it - the issue is tool ID generation, not endpoint selection

### Error: "All models in cooldown"

**Cause:** Previous failures triggered cooldown

**Fix:** Clear usageStats in auth-profiles.json:
```json
"usageStats": {}
```

### Error: Gateway shows wrong model

**Cause:** openclaw.json and clawdbot.json have different values

**Fix:** Ensure `agents.defaults.model.primary` matches in BOTH files, then restart gateway

### Error: "EPIPE" crash when terminal closes

**Cause:** Gateway not running with nohup

**Fix:** Always start with:
```bash
nohup openclaw gateway --force > /dev/null 2>&1 &
```

### Error: "api field invalid" or validation errors

**Cause:** Wrong value for `api` field in custom provider

**Fix:** Use `"api": "openai-completions"` (not `openai-chat` or `openai-responses`)

### Error: "quota exceeded" or "All credentials cooling down (rate_limit)"

**Cause:** VibeProxy upstream rate limiting. Can happen when:
1. Model goes haywire and spams requests
2. Actual API quota exhaustion
3. VibeProxy spam protection triggered

**Symptoms:**
- OpenClaw error: `All models failed: vibeproxy/claude-opus-4.5: 429 All credentials cooling down`
- Direct curl: `{"error":{"message":"quota exceeded","type":"rate_limit_error"}}`

**Fix:**
1. Clear OpenClaw cooldowns:
   ```bash
   # Edit auth-profiles.json, set usageStats to empty
   jq '.usageStats = {}' ~/.clawdbot/agents/main/agent/auth-profiles.json > /tmp/ap.json && \
   mv /tmp/ap.json ~/.clawdbot/agents/main/agent/auth-profiles.json
   ```

2. Test if upstream is actually rate limited:
   ```bash
   curl -s http://localhost:8317/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer vibeproxy" \
     -d '{"model":"claude-opus-4.5","messages":[{"role":"user","content":"Say OK"}],"max_tokens":10}'
   ```

3. If still `quota exceeded`, try a different model:
   ```bash
   # Test GPT
   curl -s http://localhost:8317/v1/chat/completions ... -d '{"model":"gpt-5.2",...}'

   # Test Gemini
   curl -s http://localhost:8317/v1/chat/completions ... -d '{"model":"gemini-3-pro-preview",...}'
   ```

4. Switch OpenClaw to working model temporarily:
   ```bash
   openclaw config set agents.defaults.model.primary vibeproxy/gpt-5.2
   pkill -9 -f "openclaw.*gateway" && nohup openclaw gateway --force > /dev/null 2>&1 &
   ```

**Note:** Anthropic usage dashboard may show low usage (e.g., 2%) but VibeProxy has its own rate limiting. The `quota exceeded` error often comes from VibeProxy spam protection, not actual Anthropic quota.

### Error: "deactivated_workspace" (GPT models)

**Cause:** VibeProxy credentials for OpenAI/Codex workspace are invalid or deactivated.

**Fix:** Update credentials on the VibeProxy host (DMBP14). This is a VibeProxy configuration issue, not OpenClaw.

### Problem: Model Goes Haywire (Duplicate Responses, Spam)

**Symptoms:**
- Bot sends multiple similar messages rapidly
- Session shows repeated assistant messages with same content rephrased
- Eventually hits rate limits
- Gateway log shows many `delivered reply` events in quick succession

**Example from session:**
```
08:20:55 - "The native memory indexer only indexes files..."
08:20:59 - "The native memory indexer only indexes 'memory' source..."
08:21:16 - "The native memory is only indexing from the memory source..."
08:21:22 - "The issue is clear now: the native memory indexer..."
```

**Root Causes:**
1. **Memory injection confusion** - `memory-memu: injecting N memories` can cause context confusion
2. **Tool result loops** - Tool calls returning results that trigger new similar responses
3. **Session state corruption** - Bad state causing model to restart its thought process

**Immediate Fix:**
1. Clear the session:
   ```bash
   rm ~/.clawdbot/agents/main/sessions/<session-id>.jsonl*
   ```

2. Clear rate limit cooldowns:
   ```bash
   jq '.usageStats = {}' ~/.clawdbot/agents/main/agent/auth-profiles.json > /tmp/ap.json && \
   mv /tmp/ap.json ~/.clawdbot/agents/main/agent/auth-profiles.json
   ```

3. Restart gateway:
   ```bash
   pkill -9 -f "openclaw.*gateway" && nohup openclaw gateway --force > /dev/null 2>&1 &
   ```

**Investigation:**
- Check session for duplicate messages: `tail -50 ~/.clawdbot/agents/main/sessions/*.jsonl | jq -r 'select(.message.role == "assistant")'`
- Check gateway logs: `grep "delivered reply" ~/.clawdbot/logs/gateway.log | tail -20`
- Check memory injection: `grep "memory-memu" ~/.clawdbot/logs/gateway.log | tail -10`

---

## Troubleshooting Checklist

When things break, check in this order:

### 1. SSH Tunnel
```bash
lsof -i :8317  # Should show ssh listening
curl -s "http://localhost:8317/v1/models" | head -1  # Should return JSON
```

### 2. VibeProxy Working
```bash
curl -s "http://localhost:8317/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer vibeproxy" \
  -d '{"model":"claude-opus-4.5","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
# Should return a response
```

### 3. Config Files in Sync
```bash
grep '"primary"' ~/.clawdbot/openclaw.json
grep '"primary"' ~/.clawdbot/clawdbot.json
# Should match
```

### 4. Auth Profile Exists
```bash
grep "vibeproxy:default" ~/.clawdbot/agents/main/agent/auth-profiles.json
# Should find the entry
```

### 5. No Cooldowns
```bash
grep "cooldownUntil" ~/.clawdbot/agents/main/agent/auth-profiles.json
# Should be empty or show past timestamps
```

### 6. Gateway Running with Correct Model
```bash
pgrep -f "openclaw.*gateway"  # Should return PID
grep "agent model" ~/.clawdbot/logs/gateway.log | tail -1  # Should show vibeproxy/claude-opus-4.5
```

### 7. Check for Errors
```bash
tail -50 ~/.clawdbot/logs/gateway.log | grep -iE "(error|fail)"
tail -20 ~/.clawdbot/logs/gateway.err.log
```

---

## Quick Reference Commands

```bash
# === SSH TUNNEL ===
# Start tunnel
ssh -f -N -L 8317:localhost:8317 danielba@192.168.50.71

# Check tunnel
lsof -i :8317

# === GATEWAY ===
# Start
nohup openclaw gateway --force > /dev/null 2>&1 &

# Stop
pkill -9 -f "openclaw.*gateway"

# Restart
pkill -9 -f "openclaw.*gateway" && sleep 2 && nohup openclaw gateway --force > /dev/null 2>&1 &

# Status
pgrep -f "openclaw.*gateway" && openclaw models

# === LOGS ===
tail -f ~/.clawdbot/logs/gateway.log
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log

# === CONFIG ===
# Check current model
openclaw models

# View config
cat ~/.clawdbot/openclaw.json | jq '.agents.defaults.model'

# === TEST ===
# Test via CLI
openclaw agent --local --session-id test -m "Say hello" --json

# Test vibeproxy directly
curl -s "http://localhost:8317/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-opus-4.5","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

---

## Root Cause Analysis (Complete Picture)

### The Request/Response Chain

```
OpenClaw → VibeProxy → Claude Code CLI → Anthropic API
   ↑           ↑              ↑               ↑
   |           |              |               |
   |           |              |               Returns responses
   |           |              |               in Anthropic format
   |           |              |
   |           |              Translates to/from
   |           |              Anthropic format
   |           |
   |           TRANSPARENT PROXY
   |           Does NOT modify requests/responses
   |           Just passes everything through
   |
   The `api` field controls how OpenClaw
   PARSES responses, not what VibeProxy does
```

### Why `api: "openai-completions"` Works But `api: "openai-responses"` Doesn't

**VibeProxy is completely transparent** - it doesn't handle tool calls at all. The actual proxy binaries (CLIProxyAPIPlus, ThinkingProxy) just pass requests/responses unchanged.

The issue is in **OpenClaw's response parsing**:

1. **`api: "openai-responses"`** expects complex SSE events with:
   - `event: response.output_item.added`
   - `data: {"type": "function_call", ...}`
   - Proper event/data line separation

   But VibeProxy's transparent passthrough doesn't provide this format. OpenClaw's parser gets confused and concatenates JSON objects.

2. **`api: "openai-completions"`** uses simpler parsing:
   - Only handles text content streaming
   - Tool calls are processed after the full response completes
   - No streaming tool call delta parsing = no concatenation bugs

**Bottom line:** Use `openai-completions` for VibeProxy because the transparent proxy doesn't provide the SSE format that `openai-responses` expects for tool calls.

---

## Root Cause Analysis (Why Tool IDs Break)

This was the hardest bug to diagnose. Here's what's actually happening:

### The Problem Chain

1. **OpenClaw generates tool call IDs** in OpenAI format when using tools
2. **These IDs may contain characters** like `/`, `+`, `=`, `|` (base64-ish)
3. **VibeProxy is transparent** - it forwards requests unchanged to Claude
4. **Anthropic's API rejects** IDs not matching `^[a-zA-Z0-9_-]+$`
5. **Session history stores** the bad IDs, so they persist across restarts

### Example of Bad Tool ID (from logs)

```
toolCallId=call_xoLSVDWBiGw70ROQ4E9dfPaH|jEKiVBqnRxK84UjD9AT/OYhAWLUd9Ovpk8G27l3PM7x...
```

The `|` and `/` characters cause Anthropic to reject the request.

### Why Fresh Sessions Work

When you clear the session, the next request generates NEW tool IDs. If the request goes directly to Claude (not replaying history with old IDs), the new IDs are compatible.

### Why GPT Doesn't Have This Problem

GPT models are more lenient with tool ID formats. So if you use `vibeproxy/gpt-5.2`, tool calls work fine. The issue only surfaces with Claude models.

### Long-term Solutions

1. **VibeProxy could sanitize tool IDs** when translating between formats (feature request)
2. **OpenClaw could generate Anthropic-compatible IDs** for custom providers (feature request)
3. **Disable tool calling** for vibeproxy Claude models (workaround)
4. **Clear sessions periodically** if using mixed models (manual workaround)

---

## DO NOTs (Things That Don't Work)

- **DO NOT** use `openai:vibeproxy/model` prefix - invalid format
- **DO NOT** set `baseUrl` in auth-profiles.json expecting it to route requests - it doesn't
- **DO NOT** use `api: "openai-chat"` - invalid enum value
- **DO NOT** run gateway without `nohup` - will crash with EPIPE
- **DO NOT** use `OPENAI_BASE_URL` env var - OpenClaw ignores it
- **DO NOT** mix GPT and Claude sessions - tool IDs are incompatible
- **DO NOT** forget to update BOTH config files - they must match

---

## Files Modified in This Setup

1. `~/.clawdbot/openclaw.json` - Added vibeproxy provider, set primary model
2. `~/.clawdbot/clawdbot.json` - Synced model settings
3. `~/.clawdbot/agents/main/agent/auth-profiles.json` - Added vibeproxy:default profile
4. `~/.clawdbot/agents/main/agent/models.json` - Auto-generated, don't edit directly

---

## Version Info

- openclaw CLI: 2026.1.29
- clawdbot CLI: 2026.1.24-3
- OpenClaw.app: 2026.1.29
- VibeProxy: Running on DMBP14

---

## Machine Info

- **This machine:** DMBP16 (MacBook Pro 16), user `molt`, IP 192.168.50.115
- **VibeProxy host:** DMBP14, user `danielba`, IP 192.168.50.71
- **Config symlink:** `~/.openclaw` -> `~/.clawdbot`

---

## Known Limitations and Caveats

### 1. Tool Call ID Format Incompatibility

When using Claude through VibeProxy, tool call IDs generated by OpenClaw may contain characters (`/`, `+`, `=`, `|`) that Anthropic rejects. VibeProxy is a transparent proxy and doesn't sanitize these IDs.

**Symptoms:**
- Error: `400 tool_use.id: String should match pattern '^[a-zA-Z0-9_-]+$'`
- Happens after multiple tool calls in a session

**Workaround:** Clear the corrupted session file:
```bash
rm ~/.clawdbot/agents/main/sessions/<session-id>.jsonl*
```

### 2. No Hot-Reload of Model Config

Changing `agents.defaults.model.primary` requires a gateway restart. The gateway does NOT detect config changes automatically.

### 3. Dual Config File Requirement

Both `openclaw.json` and `clawdbot.json` are read. If they disagree, behavior is undefined. Always update both.

### 4. Gemini Context Window

Gemini models advertise 1M token context, but actual usable context may be lower depending on the request structure.

### 5. VibeProxy Transparency

VibeProxy does NOT:
- Modify request bodies
- Modify response bodies
- Handle rate limiting
- Provide error translation
- Sanitize tool call IDs

It's literally just a TCP tunnel with minimal HTTP header handling.

### 6. OpenClaw Has No Tool Call Rate Limiting

**CRITICAL:** OpenClaw has NO built-in limit on tool calls. The agent can make unlimited rapid API calls until the provider returns 429.

**What happens on 429:**
1. OpenClaw immediately rotates to next auth profile (no wait)
2. If all profiles exhausted, falls back to next model in `fallbacks`
3. This can burn through ALL configured providers in minutes

**Evidence from 2026-02-01 incident:**
- Session made 107 tool calls vs 14 text responses (7.6:1 ratio)
- 14 API calls in 4 minutes exhausted Antigravity quota
- Agent got stuck in tool call loop, never responding to user

**Workarounds:**
1. Use `/new` to start fresh session (clears accumulated context)
2. Configure longer cooldowns in config:
```json
{
  "auth": {
    "cooldowns": {
      "billingBackoffHours": 12,
      "billingMaxHours": 48,
      "failureWindowHours": 48
    }
  }
}
```
3. Use GPT-5.2 as primary (higher rate limits than Claude/Antigravity)
4. Feature request: Ask OpenClaw maintainers for `max_tool_calls_per_minute`

### 7. Antigravity Models Have Tiny Quotas

The `gemini-claude-*` models route Claude through Google AI Studio (Antigravity provider). They have **much lower rate limits** than direct Anthropic API - approximately 10-15 requests per hour.

**NOT suitable for:**
- Agentic workloads with many tool calls
- Primary model for chat
- Early position in fallback chain

**Use only as:** Last-resort fallback when all other providers are exhausted.

---

3. **Actual cause:** Agent exploration loop with no termination point
   - Given open-ended task: "investigate memory systems"
   - Made rapid tool calls without natural stopping point

### Solution

1. Switched to `vibeproxy/gpt-5.2` (GitHub Copilot has higher limits)
2. Started fresh session with `/new`
3. Cleared cooldowns in auth-profiles.json

### Key Configuration Added

To register custom provider models properly, you MUST add `models.providers`:

```json
{
  "models": {
    "providers": {
      "vibeproxy": {
        "baseUrl": "http://localhost:8317/v1",
        "apiKey": "vibeproxy",
        "api": "openai-completions",
        "models": [
          {"id": "gemini-claude-opus-4-5-thinking", "name": "..."},
          {"id": "gpt-5.2", "name": "GPT 5.2"},
          {"id": "claude-opus-4.5", "name": "Claude Opus 4.5"}
        ]
      }
    }
  }
}
```

Without this, you get "Unknown model: vibeproxy/model-name" error.

### Local VibeProxy Setup

Moved from SSH tunnel (DMBP14) to local VibeProxy.app on DMBP16:

1. Copied auth config: `scp -r danielba@192.168.50.71:/Users/danielba/.cli-proxy-api ~/.cli-proxy-api`
2. Installed VibeProxy.app
3. Killed SSH tunnel: `kill $(pgrep -f "ssh.*8317")`
4. Started VibeProxy.app, clicked "Start Server"
5. Verified: `curl http://localhost:8317/v1/models`

### Lessons Learned

1. **Antigravity quotas are tiny** - ~10-15 requests/hour, NOT suitable for agentic work
2. **GPT-5.2 is reliable** - Higher limits via GitHub Copilot
3. **Fresh session fixes stuck loops** - `/new` clears accumulated tool call context
4. **Ask Devin for code questions** - Devin found the `models.providers` requirement quickly

---

## Appendix: DeepWiki Documentation Reference

OpenClaw's custom provider schema was documented via DeepWiki MCP. Key findings:

### Valid API Types
From `src/providers/index.ts`:
- `"openai-completions"` → `/v1/chat/completions`
- `"openai-responses"` → `/v1/responses`

### Model Schema Fields
```typescript
interface ModelConfig {
  id: string;           // Model identifier
  name: string;         // Display name
  input: string[];      // ["text"] or ["text", "image"]
  contextWindow: number;
  maxTokens: number;
}
```

### Provider Schema Fields
```typescript
interface ProviderConfig {
  baseUrl: string;      // API endpoint
  apiKey: string;       // Auth token
  api: "openai-completions" | "openai-responses";
  models: ModelConfig[];
}
```

---


### ~/.clawdbot/agents/main/agent/auth-profiles.json (Minimal for VibeProxy)

```json
{
  "version": 1,
  "profiles": {
    "vibeproxy:default": {
      "type": "token",
      "provider": "vibeproxy",
      "token": "vibeproxy"
    }
  },
  "lastGood": {
    "vibeproxy": "vibeproxy:default"
  },
  "usageStats": {}
}
```

---

## Quick Diagnostic Script

Save as `~/scripts/check-vibeproxy.sh`:

```bash
#!/bin/bash
echo "=== VibeProxy Diagnostic ==="

echo -e "\n1. SSH Tunnel:"
if lsof -i :8317 | grep -q ssh; then
    echo "   ✓ Port 8317 tunnel active"
else
    echo "   ✗ Port 8317 tunnel NOT active"
    echo "   Fix: ssh -f -N -L 8317:localhost:8317 danielba@192.168.50.71"
fi

echo -e "\n2. VibeProxy Response:"
MODELS=$(curl -s "http://localhost:8317/v1/models" 2>/dev/null)
if [ -n "$MODELS" ]; then
    echo "   ✓ VibeProxy responding"
    echo "   Models: $(echo $MODELS | jq -r '.data[].id' | head -3 | tr '\n' ', ')"
else
    echo "   ✗ VibeProxy not responding"
fi

echo -e "\n3. Gateway Process:"
if pgrep -f "openclaw.*gateway" > /dev/null; then
    echo "   ✓ Gateway running (PID: $(pgrep -f 'openclaw.*gateway'))"
else
    echo "   ✗ Gateway not running"
    echo "   Fix: nohup openclaw gateway --force > /dev/null 2>&1 &"
fi

echo -e "\n4. Config Primary Model:"
PRIMARY=$(grep -o '"primary"[^,]*' ~/.clawdbot/openclaw.json | head -1)
echo "   $PRIMARY"

echo -e "\n5. Auth Profile:"
if grep -q '"vibeproxy:default"' ~/.clawdbot/agents/main/agent/auth-profiles.json 2>/dev/null; then
    echo "   ✓ vibeproxy:default profile exists"
else
    echo "   ✗ vibeproxy:default profile MISSING"


### Answer

Based on my analysis of the VibeProxy repository, **YES, this is definitely worth adding**, but with some recommendations.

## Current State of the Repo

The VibeProxy repository currently has NO documentation about OpenClaw integration: VibeProxy:1-45

The existing documentation focuses on:
- Agent Zero (A0) integration: VibeProxy:1-1
- Factory Droid CLI integration: VibeProxy:61-65
- General VibeProxy setup: VibeProxy:1-30

## Why You Should Add It

### 1. **Pattern Consistency**
The repo already documents multiple client integrations (A0, Factory Droid), so adding OpenClaw fits this pattern perfectly VibeProxy:40-44

### 2. **Comprehensive & Battle-Tested**
Your guide is exceptionally detailed with:
- Real troubleshooting from actual debugging sessions (2026-01-31, 2026-02-01)
- Root cause analysis of tool call ID incompatibilities
- Complete configuration examples
- Production-tested SSH tunnel setups

### 3. **Fills a Gap**
VibeProxy's general integration guide covers the API basics VibeProxy:33-57 , but doesn't have client-specific configuration details like yours.

## Recommendations

### 1. **File Location**
Add as: `docs/OPENCLAW-VIBEPROXY-INTEGRATION.md`

This follows the pattern of `docs/A0-VIBEPROXY-FIXES.md` for client-specific guides.

### 2. **Update README.md**
Add OpenClaw to the supported clients section:

```markdown
## 🎯 Supported Clients

- ✅ **Agent Zero (A0)** - See [docs/A0-VIBEPROXY-FIXES.md](docs/A0-VIBEPROXY-FIXES.md)
- ✅ **Factory Droid CLI** - See main setup guide
- ✅ **OpenClaw/Clawdbot** - See [docs/OPENCLAW-VIBEPROXY-INTEGRATION.md](docs/OPENCLAW-VIBEPROXY-INTEGRATION.md)
```

### 3. **Consider Adding**
A brief OpenClaw section to the general integration guide VibeProxy:16-16  that links to your detailed guide.

### 4. **Minor Adjustments**
Your guide mentions SSH tunneling from DMBP14→DMBP16, but the repo is focused on Windows integration VibeProxy:3-3 . Consider adding a note that OpenClaw is Mac-based and this guide is for Mac→Mac setups (unlike the Windows focus of other docs).

## Bottom Line

**Add it.** It's high-quality documentation that makes the VibeProxy repo more valuable as a comprehensive resource for VibeProxy integration across multiple AI agent platforms.

### Notes

The VibeProxy repo appears to be an active fork focused on multi-client integration VibeProxy:1-3 . Your OpenClaw guide is more comprehensive than the existing A0 guide, which is a good sign that it will be a valuable addition. The only consideration is that it documents a Mac-to-Mac setup rather than Windows integration, but since VibeProxy itself runs on Mac, this is actually complementary to the existing Windows-side documentation.


### Citations


**File:** README.md (L1-45)

```markdown
# VibeProxy-Windows

> **Fork of [automazeio/vibeproxy](https://github.com/automazeio/vibeproxy)** focused on Windows integration, Agent Zero (A0), and Droid CLI management.

Use your **Claude Code** and **ChatGPT/Codex** subscriptions on Windows by tunneling to VibeProxy running on your Mac.

## 🎯 What This Does

- **Problem:** AI tools on Windows need API keys → pay-per-token billing
- **Solution:** VibeProxy bridges your subscriptions → use existing Claude Code/ChatGPT Plus/Pro access
- **This repo:** Windows-side management tools, configs, and integration with Agent Zero + Droid CLI

## 🚀 Quick Start

```powershell
# Launch the main manager CLI
.\VibeProxy-Manager.ps1
```

This gives you a menu to: start SSH tunnel, browse models, switch A0 configs, test connectivity, manage Droid models.

**Detailed guides:** See `docs/VIBEPROXY-QUICKSTART.md` and `docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md`

## 📂 Key Files

### Launchers
- **VibeProxy-Manager.ps1** - All-in-one CLI manager (tunnel, models, configs, testing)
- **start-tui.bat** - Launch Python TUI with auto-tunnel (alternative interface)

### Scripts
- **ssh-tunnel-intelligent.py** - Smart tunnel with auto-reconnect and Mac discovery
- **ssh-tunnel-vibeproxy.ps1** - PowerShell tunnel script
- **scripts/** - Additional utilities (sync models, test connection, etc.)

### Configuration
- **vibeproxy-config.json** - Your Mac IP, SSH credentials, favorites (gitignored)
- **configs/a0-*.json** - Agent Zero model presets
- **factory-config-example.json** - Template for `~/.factory/config.json`

### Documentation
- **docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md** - Comprehensive integration guide
- **docs/VIBEPROXY-QUICKSTART.md** - Quick setup reference
- **CLAUDE.md** - AI assistant instructions for this codebase

## 🎬 Setup Overview
```

**File:** README.md (L61-65)

```markdown

# 2. Use Factory Droid
droid
/model  # Select VibeProxy model
```
```

**File:** docs/A0-VIBEPROXY-FIXES.md (L1-1)

```markdown
# Agent Zero (A0) + VibeProxy Configuration Fixes
```

**File:** docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md (L1-30)

```markdown
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

```

**File:** docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md (L33-57)

```markdown
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

```

