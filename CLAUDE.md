# VibeProxy Integration for Agent Zero (A0)

This project contains configuration files and management scripts for using VibeProxy with Agent Zero.

## CRITICAL: GPT-5 Models Temperature Constraint

**LiteLLM enforces `temperature=1` for ALL GPT-5 models.** This is hardcoded in `litellm/llms/openai/chat/gpt_5_transformation.py`.

### Error You'll See If Wrong:
```
litellm.UnsupportedParamsError: gpt-5 models (including gpt-5-codex) don't support temperature=0.1.
Only temperature=1 is supported. To drop unsupported params set `litellm.drop_params = True`
```

### Solution:
**Always use `temperature: "1"` for GPT-5 models in A0 configs:**
- `gpt-5.2-codex`
- `gpt-5.1-codex`
- `gpt-5.1-codex-max`
- `gpt-5.1-codex-mini`
- `gpt-5-codex-mini`
- `gpt-5-mini`
- `gpt-5`
- Any model name containing "gpt-5"

### Claude Models Are Different:
Claude models (via VibeProxy) **CAN** use any temperature (0-1). Only GPT-5 has this restriction.

```json
// GPT-5 - MUST be temperature 1
"chat_model_kwargs": { "temperature": "1" }

// Claude - Can be any value
"chat_model_kwargs": { "temperature": "0" }
```

## Official Context Window Sizes (2025)

| Model | Context Window | Max Output | Temperature |
|-------|---------------|------------|-------------|
| **GPT-5.2 Codex** | 400,000 | 128,000 | 1 only |
| **GPT-5.1-Codex-Max** | 400,000 | 128,000 | 1 only |
| **GPT-5.1-Codex-Mini** | 400,000 | 128,000 | 1 only |
| **GPT-5 / GPT-5-Mini** | 400,000 | 128,000 | 1 only |
| **Claude Opus 4.5** | 200,000 | 32,000 | 0-1 |
| **Claude Sonnet 4.5** | 200,000 | 32,000 | 0-1 |
| **Claude Haiku 4.5** | 200,000 | 8,192 | 0-1 |
| **Gemini 2.5 Pro** | 1,000,000 | 65,536 | 0-2 |
| **Gemini 3 Pro** | 1,000,000 | 65,536 | 0-2 |

**Sources:** OpenAI API docs, OpenRouter, Anthropic docs

## Architecture

```
Mac (VibeProxy)          Windows (A0 Docker)
localhost:8317    <---   host.docker.internal:8317
     |                          |
  OAuth proxy              SSH Tunnel
     |                          |
  AI APIs                  A0 Container
```

## Files

- `configs/` - A0 settings.json presets for different models
- `vibeproxy_manager/` - **Python TUI manager** (Textual-based, recommended)
- `VibeProxy-Manager.ps1` - Legacy PowerShell manager (deprecated)

## Usage

### Python TUI Manager (Recommended)

Professional keyboard-navigable interface using Textual framework:

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Run the manager
python -m vibeproxy_manager
# Or:
python run.py
# Or on Windows:
run.bat
```

**Key bindings:**
- `↑↓` Navigate
- `Enter` Select
- `Space` Toggle selection
- `Q` Quit
- `Esc` Back

**Features:**
- Browse all available models with search/filter
- Interactive chat mode with any model
- SSH tunnel management
- A0 config switching
- Favorites and max_tokens settings

### Legacy PowerShell Manager

```powershell
# Run the legacy manager
powershell -ExecutionPolicy Bypass -File "F:\claude\VibeProxy\VibeProxy-Manager.ps1"
```

## A0 Settings Location

A0 reads from: `C:\claude\agent-zero-data\tmp\settings.json`

The manager copies selected configs to this location.

## CRITICAL: A0 Path Mismatch Issue

**Problem:** A0 has TWO separate directory structures:

| Path | Purpose |
|------|---------|
| `/a0/usr/projects/<name>/` | A0's internal project metadata, instructions, memory |
| `/a0/claude/<name>/` | **Actual code files** (mounted from Windows C:\claude) |

**A0 defaults to `/a0/usr/projects/` but your code is at `/a0/claude/`!**

### Solution: Always tell A0 the correct path

When starting a task, ALWAYS include:
```
Working directory: /a0/claude/<project-name>/
```

### Permanent Fix: Create symlinks

Run this in A0's terminal to link projects:
```bash
# For each project, create a symlink:
ln -sf /a0/claude/<project-name> /a0/usr/projects/<project-name>
```

### Example A0 prompt:
```
Working directory: /a0/claude/email-management-tool-2-main

Check the current state of the project, try running it...
```
