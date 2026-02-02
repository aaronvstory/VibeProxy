# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VibeProxy Manager is a Python TUI (Terminal User Interface) application for managing AI model access through a Mac-hosted proxy. It enables Windows/Docker clients to use multiple AI providers (OpenAI, Anthropic, Google) via a single SSH tunnel.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the TUI application
python -m vibeproxy_manager
# Or: python run.py
# Or on Windows: run.bat

# Run tests
pytest tests/

# Run a single test
pytest tests/test_api.py::test_vibeproxy_client_init -v
```

## Critical Constraints

### GPT-5 Temperature Restriction

**LiteLLM enforces `temperature=1` for ALL GPT-5 models.** This is hardcoded and cannot be changed.

```python
# WRONG - will raise UnsupportedParamsError
"chat_model_kwargs": { "temperature": "0.1" }

# CORRECT for GPT-5 models
"chat_model_kwargs": { "temperature": "1" }

# Claude models CAN use any temperature (0-1)
```

Affected models: `gpt-5.2-codex`, `gpt-5.1-codex`, `gpt-5.1-codex-max`, `gpt-5.1-codex-mini`, `gpt-5-codex-mini`, `gpt-5-mini`, `gpt-5`, and any model containing "gpt-5".

### A0 Path Mismatch

Agent Zero has TWO directory structures:
- `/a0/usr/projects/<name>/` - A0's internal project metadata
- `/a0/claude/<name>/` - Actual code files (mounted from Windows `C:\claude`)

**A0 defaults to the wrong path.** Always specify: `Working directory: /a0/claude/<project-name>/`

## Architecture

```
vibeproxy_manager/           # Main Python package
├── app.py                   # VibeProxyApp - main Textual application entry
├── api.py                   # VibeProxyClient - async HTTP client for model API
├── config.py                # ConfigManager - handles all config files
├── models.py                # Pydantic models (Model, ChatMessage, A0Config)
├── docker.py                # DockerManager - Agent Zero container control
├── tunnel.py                # TunnelManager - SSH tunnel with auto-discovery
├── screens/                 # Textual Screen classes
│   ├── main_menu.py         # MainMenuScreen - primary navigation
│   ├── browse_models.py     # BrowseModelsScreen - model selection/actions
│   ├── chat.py              # ChatScreen - interactive chat mode
│   ├── config_menu.py       # ConfigMenuScreen - A0 preset switching
│   ├── droid_models.py      # DroidModelsScreen - Factory CLI integration
│   └── network_settings.py  # NetworkSettingsScreen - SSH/tunnel config
├── widgets/
│   └── status_bar.py        # StatusBar widget for connection status
└── styles/
    └── app.tcss             # Textual CSS styling
```

### Key Components

**VibeProxyClient** (`api.py`):
- Async HTTP client using `httpx`
- 30-second model cache to prevent UI blocking
- Auto-detects GPT-5 models and sets `temperature=1`
- Methods: `list_models()`, `chat()`, `preflight()`, `test_connection()`

**ConfigManager** (`config.py`):
- Manages `vibeproxy-config.json` (SSH key path, favorites, max_tokens)
- Handles A0 config presets in `configs/a0-*.json`
- Manages Factory/Droid CLI integration via `~/.factory/config.json`
- Key paths:
  - A0 settings: `C:/claude/agent-zero-data/tmp/settings.json`
  - Factory config: `~/.factory/config.json`

**TunnelManager** (`tunnel.py`):
- Multi-layer tunnel verification (PID + port check)
- Auto-discovery: scans network to find Mac when IP changes
- Smart error classification (IP_CHANGED, SSH_DOWN, AUTH_FAILED)
- Key-based SSH authentication (password auth removed for security)

### Data Flow

```
Windows TUI → SSH Tunnel (port 8317) → Mac VibeProxy → AI Provider APIs
                                                    ↓
Docker (A0) → host.docker.internal:8317 ────────────┘
```

## File Locations

| File | Purpose |
|------|---------|
| `vibeproxy-config.json` | SSH key path, favorites, settings |
| `configs/a0-*.json` | A0 model presets (created via TUI) |
| `configs/backups/` | A0 settings backups before changes |
| `~/.factory/config.json` | Droid CLI custom models |

## Key Model Names

Model display names are defined in `vibeproxy_manager/models.py:MODEL_DISPLAY_NAMES`. Provider detection uses simple string matching on model ID (claude→Anthropic, gpt→OpenAI, gemini→Google).

## Testing Notes

The test suite is minimal. Tests require:
- No running tunnel (tests mock/unit only)
- Windows environment for `find_ssh()` tests to pass fully
