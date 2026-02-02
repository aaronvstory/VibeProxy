# Deep Dive: Agent Zero Docker + VibeProxy Integration

## Strategic Summary

Agent Zero works with VibeProxy through LiteLLM's OpenAI-compatible interface. The key configuration is setting `chat_model_provider: "other"` and using `host.docker.internal:8317` for Docker→host networking. The image-manipulator Electron app already has built-in VibeProxy support - only environment variable changes are needed.

### Key Insight
This is primarily a **configuration task**, not a code modification task. Both A0 and image-manipulator already support VibeProxy.

---

## Key Questions

- How to configure A0 in Docker to use VibeProxy?
- How to integrate image-manipulator with VibeProxy?
- What are the containerization best practices?
- What model constraints exist (temperature, context)?

---

## Overview

Agent Zero is an autonomous AI agent framework that runs in Docker containers. It uses LiteLLM as its model abstraction layer, which means any OpenAI-compatible endpoint works out of the box. VibeProxy exposes exactly this interface at `localhost:8317/v1`.

The image-manipulator is an Electron app for OCR processing. It was designed with provider abstraction from the start, with explicit VibeProxy support in its `ocr-config.js` file.

Both applications follow the same integration pattern: point the API base URL to VibeProxy and use `"dummy-not-used"` for API keys (since VibeProxy handles OAuth authentication on the Mac).

---

## How It Works

### Agent Zero Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ Docker Container                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Agent Zero Framework                                     │ │
│  │  ├── models/                                             │ │
│  │  │   └── LiteLLM abstraction                             │ │
│  │  ├── tmp/settings.json  ← Configuration                  │ │
│  │  ├── memory/            ← Persistent storage             │ │
│  │  └── knowledge/         ← Knowledge base                 │ │
│  └───────────────────┬─────────────────────────────────────┘ │
│                      │ HTTP requests                          │
│                      ▼                                        │
│  host.docker.internal:8317 (resolves to Windows host)        │
└──────────────────────────────────────────────────────────────┘
```

### Image-Manipulator Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Electron App                                                 │
│  ├── electron-main.js     (Window management)               │
│  ├── server.js            (Express REST API)                │
│  ├── server-ocr.js        (OCR Service - LLM calls)         │
│  └── utils/ocr-config.js  (Provider routing)                │
│                    │                                         │
│                    ▼                                         │
│  localhost:8317/v1/chat/completions                         │
└─────────────────────────────────────────────────────────────┘
```

---

## History & Context

Agent Zero was created by frdel (now agent0ai organization) as an open-source autonomous agent framework. Version 1.0+ standardized on LiteLLM for model abstraction, enabling easy provider switching.

VibeProxy was created to provide OAuth-authenticated access to multiple AI providers through a single local endpoint. It eliminates the need for individual API keys by using browser-based OAuth flows.

The combination enables free-tier access to premium models (via GitHub Copilot, Google AI Studio) without managing API keys.

---

## Patterns & Best Practices

### 1. Provider Configuration
- **When:** Configuring any non-native LiteLLM provider
- **Pattern:** Set `provider: "other"` and explicit `api_base`
- **Why:** LiteLLM requires explicit endpoint when not using known providers

### 2. Docker Networking
- **When:** Container needs to access host services
- **Pattern:** Use `host.docker.internal` instead of `localhost`
- **Why:** `localhost` inside Docker refers to container, not host

### 3. Temperature Constraints
- **When:** Using GPT-5 models via LiteLLM
- **Pattern:** Always set `temperature: "1"`
- **Why:** LiteLLM hardcodes this constraint in `gpt_5_transformation.py`

### 4. Embedding Separation
- **When:** Configuring Agent Zero
- **Pattern:** Keep embeddings on local HuggingFace model
- **Why:** VibeProxy only supports chat completions, not embeddings

### 5. API Key Placeholder
- **When:** Configuring any VibeProxy client
- **Pattern:** Use `"dummy-not-used"` for API key fields
- **Why:** VibeProxy handles auth via OAuth, but clients may require non-empty values

---

## Limitations & Edge Cases

### VibeProxy Limitations
- **No embeddings API** → Use local HuggingFace for A0 embeddings
- **No `/v1/responses` endpoint** → Set `supports_response_schema: false`
- **SSH tunnel dependency** → Must be running for all operations

### GPT-5 Model Constraints
- **Temperature locked to 1** → Cannot use low temperature for deterministic output
- **Workaround:** Use Claude models for deterministic tasks

### Docker Networking
- **`host.docker.internal` Windows-only** → macOS/Linux may need different approach
- **Firewall rules** → Windows Defender may block Docker→host connections

### Image-Manipulator OCR
- **Vision model required** → Not all VibeProxy models support images
- **Model name format** → Must use exact VibeProxy model IDs, not OpenRouter names

---

## Current State & Trends

### Agent Zero (Jan 2025)
- Version 1.x stable with LiteLLM integration
- Active development on memory and tool systems
- Docker is primary deployment method
- Community growing (12k+ GitHub stars)

### VibeProxy Ecosystem
- Supports 35+ models via multiple providers
- GitHub Copilot integration provides free GPT-5/Claude access
- Windows TUI manager for easy configuration
- Growing adoption in local AI setups

### Industry Direction
- Local-first AI tooling increasing
- OAuth-based model access becoming standard
- Multi-provider abstraction layers (LiteLLM, Portkey) maturing

---

## Key Takeaways

1. **Both apps already support VibeProxy** - This is configuration, not coding
2. **Provider must be "other"** for A0 - Required for custom endpoints
3. **Temperature=1 for GPT-5** - Non-negotiable LiteLLM constraint
4. **Use host.docker.internal** - Docker container→host networking
5. **Embeddings stay local** - VibeProxy doesn't support embedding endpoints

---

## Remaining Unknowns

- [ ] Performance comparison: VibeProxy vs direct API latency
- [ ] Stability of SSH tunnel under heavy A0 usage
- [ ] Memory consumption with large context models (400K GPT-5)
- [ ] Image-manipulator behavior with different vision models

---

## Implementation Context

<claude_context>
<application>

- when_to_use: Local AI development without managing API keys
- when_not_to_use: Production systems requiring guaranteed uptime (SSH tunnel dependency)
- prerequisites: Mac with VibeProxy, SSH tunnel, Docker Desktop
</application>

<technical>

- libraries: LiteLLM (A0), node-fetch (image-manipulator)
- patterns: OpenAI-compatible `/v1/chat/completions` endpoint
- gotchas: GPT-5 temperature=1 only, no embeddings, host.docker.internal for Docker
</technical>

<integration>

- works_with: Any OpenAI-compatible client, LiteLLM, LangChain
- conflicts_with: Direct Anthropic SDK (different endpoint format)
- alternatives: OpenRouter (paid), direct API keys (per-provider)
</integration>
</claude_context>

---

## Sources

- [Agent Zero Documentation](https://www.agent-zero.ai/p/docs/get-started/)
- [Agent Zero GitHub](https://github.com/agent0ai/agent-zero)
- [Agent Zero Installation Guide](https://github.com/agent0ai/agent-zero/blob/main/docs/installation.md)
- [DeepWiki - A0 Docker Setup](https://deepwiki.com/agent0ai/agent-zero/14.1-docker-setup)
- [DeepWiki - A0 Configuration Reference](https://deepwiki.com/agent0ai/agent-zero/15.4-configuration-reference)
- [LiteLLM Docker Deployment](https://docs.litellm.ai/docs/proxy/deploy)
- Local: `F:\claude\VibeProxy\CLAUDE.md`
- Local: `C:\claude\image-manipulator-main\backend\utils\ocr-config.js`
