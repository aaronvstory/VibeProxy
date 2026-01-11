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

| Model | Context Window | Max Output | Temperature | Notes |
|-------|---------------|------------|-------------|-------|
| **GPT-5.2 Codex** | 400,000 | 128,000 | 1 only | Best reasoning |
| **GPT-5.1-Codex-Max** | 400,000 | 128,000 | 1 only | Deep analysis |
| **GPT-5.1-Codex-Mini** | 400,000 | 128,000 | 1 only | Fast coding |
| **GPT-5 / GPT-5-Mini** | 400,000 | 128,000 | 1 only | General purpose |
| **Claude Opus 4.5** | 200,000 | 32,000 | 0-1 | Most capable |
| **Claude Sonnet 4.5** | 200,000 | 32,000 | 0-1 | Best value |
| **Claude Haiku 4.5** | 200,000 | 8,192 | 0-1 | Fastest |
| **Gemini 2.5 Pro** | 1,000,000 | 65,536 | 0-2 | Large context |
| **Gemini 3 Pro** | 1,000,000 | 65,536 | 0-2 | Latest Gemini |

**Sources:** OpenAI API docs, OpenRouter, Anthropic docs

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     WINDOWS (This Machine)                       │
│  ┌─────────────────┐     ┌─────────────────────────────────┐   │
│  │ VibeProxy       │     │     Docker Desktop               │   │
│  │ Manager TUI     │     │  ┌───────────────────────────┐  │   │
│  │ (Python)        │     │  │   Agent Zero (A0)         │  │   │
│  │                 │     │  │   host.docker.internal    │  │   │
│  │ - Browse models │     │  │   :8317 ────────────────┐ │  │   │
│  │ - Chat/test     │     │  │                         │ │  │   │
│  │ - Apply configs │     │  │   /a0/claude/ (mounted) │ │  │   │
│  └────────┬────────┘     │  └───────────────────────┴─┘  │   │
│           │              └─────────────────────────│─────┘   │
│           │                                        │         │
│  ┌────────┴────────────────────────────────────────┴───┐     │
│  │            SSH Tunnel (port 8317)                    │     │
│  │            localhost:8317 ◄──── Mac via SSH          │     │
│  └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              │
                    SSH Connection
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        MAC (VibeProxy Host)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    VibeProxy                             │   │
│  │                  localhost:8317                          │   │
│  │                                                          │   │
│  │  OAuth Proxy ───► OpenAI, Anthropic, Google APIs         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
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

**Model Actions (in Browse Models screen):**
- `c` or `Enter` - Chat with selected model
- `t` - Test model connectivity
- `p` - Create A0 preset (saves to configs/)
- `a` - Apply to A0 (create + activate immediately)
- `d` - Set as Droid/Factory default model
- `f` - Toggle favorite

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

## Troubleshooting

### SSH Tunnel Issues

**Symptom:** "Connection refused" or models not responding

**Solutions:**
1. Check if tunnel is running:
   ```powershell
   netstat -an | findstr 8317
   ```
2. Restart the tunnel:
   ```powershell
   ./ssh-tunnel-vibeproxy.ps1
   ```
3. Verify Mac VibeProxy is running:
   ```bash
   ssh your-mac "curl -s http://localhost:8317/v1/models"
   ```

### Model Returns Empty Response

**Symptom:** Chat returns empty or model doesn't respond

**Solutions:**
1. Verify temperature for GPT-5 models (MUST be `"1"`)
2. Check model name spelling matches exactly
3. Test with the TUI's `t` (test) command

### A0 Can't Find Files

**Symptom:** A0 says "file not found" or uses wrong directory

**Solutions:**
1. Always specify: `Working directory: /a0/claude/<project>/`
2. Create symlinks (one-time fix):
   ```bash
   ln -sf /a0/claude/<project> /a0/usr/projects/<project>
   ```

### Docker Container Issues

**Symptom:** A0 container not starting or unhealthy

**Solutions:**
1. Check Docker Desktop is running
2. Restart A0 container:
   ```powershell
   docker restart agent-zero
   ```
3. Check logs:
   ```powershell
   docker logs agent-zero --tail 50
   ```

### TUI Won't Start

**Symptom:** Python errors or missing dependencies

**Solutions:**
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Use Python 3.10+
3. Try the launcher:
   ```bash
   run.bat
   ```
