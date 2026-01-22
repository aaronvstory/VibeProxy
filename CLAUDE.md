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

| Model                  | Context Window | Max Output | Temperature | Notes           |
| ---------------------- | -------------- | ---------- | ----------- | --------------- |
| **GPT-5.2 Codex**      | 400,000        | 128,000    | 1 only      | Best reasoning  |
| **GPT-5.1-Codex-Max**  | 400,000        | 128,000    | 1 only      | Deep analysis   |
| **GPT-5.1-Codex-Mini** | 400,000        | 128,000    | 1 only      | Fast coding     |
| **GPT-5 / GPT-5-Mini** | 400,000        | 128,000    | 1 only      | General purpose |
| **Claude Opus 4.5**    | 200,000        | 32,000     | 0-1         | Most capable    |
| **Claude Sonnet 4.5**  | 200,000        | 32,000     | 0-1         | Best value      |
| **Claude Haiku 4.5**   | 200,000        | 8,192      | 0-1         | Fastest         |
| **Gemini 2.5 Pro**     | 1,000,000      | 65,536     | 0-2         | Large context   |
| **Gemini 3 Pro**       | 1,000,000      | 65,536     | 0-2         | Latest Gemini   |

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
- **SSH tunnel launcher** - Opens in new window with auto-reconnect & password storage
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

| Path                       | Purpose                                                |
| -------------------------- | ------------------------------------------------------ |
| `/a0/usr/projects/<name>/` | A0's internal project metadata, instructions, memory   |
| `/a0/claude/<name>/`       | **Actual code files** (mounted from Windows C:\claude) |

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

## SSH Tunnel Management

### TUI Tunnel Launcher (NEW)

The TUI now launches the SSH tunnel in a **new terminal window** (same as CLI launcher) with:

- ✅ **Auto-reconnect** on connection drop
- ✅ **Password auto-login** (saved in `vibeproxy-config.json`)
- ✅ **Live connection status** with timestamps
- ✅ **Auto-recovery** from network interruptions
- ✅ **Visible debugging** - you can see what's happening!

**How to use:**

1. From TUI Main Menu → Select "🔌 Start SSH Tunnel" (option 1)
2. A new PowerShell window opens automatically
3. **First time only:** Enter your SSH password when prompted
4. Password is saved and auto-used for future connections
5. Keep the tunnel window open while using VibeProxy

**Password Storage:**

- Stored in `vibeproxy-config.json` under `SSHPassword` field
- **Security note:** Password is plain text (same as CLI launcher)
- To change password: delete the `SSHPassword` field and restart tunnel
- To use SSH keys instead: set up key-based auth on Mac and leave password blank

**Troubleshooting:**

### SSH Tunnel Issues

**Symptom:** "Connection refused" or models not responding

**Solutions:**

1. Check if tunnel is running:
   ```powershell
   netstat -an | findstr 8317
   ```
2. Look at the tunnel window for errors (new window-based launcher shows live status)
3. If tunnel window shows password errors:
   - Delete `SSHPassword` from `vibeproxy-config.json`
   - Restart tunnel from TUI
4. Verify Mac VibeProxy is running:
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

## Droid CLI Integration

### Custom Models via VibeProxy

Droid CLI can use any VibeProxy model through its custom models feature. Models are configured in `~/.factory/config.json` under the `custom_models` array.

**Config Location:** `C:\Users\<username>\.factory\config.json`

### Managing Droid Models

Use the **PowerShell TUI Manager** → **[7] Manage Droid Models** to:

- View all custom models configured in Droid
- Remove stale/unwanted models
- Sync all VibeProxy models to Droid (bulk add)
- Clear all custom models

Alternatively, when browsing models in either TUI, press `P` (Pick) to add a model to both A0 and Droid.

### Droid Headless Mode (Non-Interactive)

**Syntax:** `droid exec -m custom:<model-id> "your prompt"`

The `custom:` prefix is **required** for all VibeProxy models.

**Examples:**

```powershell
# Use Claude Sonnet 4.5 via VibeProxy
droid exec -m custom:claude-sonnet-4-5-20250929 "analyze this code"

# Use GPT-5.2 Codex via VibeProxy with medium autonomy
droid exec --auto medium -m custom:gpt-5.2-codex "fix the bug in main.py"

# Use Claude Opus 4.5 for architecture review
droid exec -m custom:claude-opus-4-5-20251101 "review the architecture"

# Use Gemini 3 Pro with high autonomy
droid exec --auto high -m custom:gemini-3-pro "refactor this function"

# Pipe file content to Droid
cat app.py | droid exec -m custom:claude-sonnet-4-5-20250929 "explain this code"

# Read prompt from file
droid exec -m custom:gpt-5.2-codex - < prompt.txt
```

### Available Custom Model IDs

After syncing via the TUI, these models are available (prefix with `custom:`):

| Model ID                     | Display Name             |
| ---------------------------- | ------------------------ |
| `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5        |
| `claude-opus-4-5-20251101`   | Claude Opus 4.5 (Latest) |
| `claude-haiku-4-5-20251001`  | Claude Haiku 4.5         |
| `gpt-5.2-codex`              | GPT-5.2 Codex            |
| `gpt-5.2`                    | GPT-5.2                  |
| `gpt-5.1-codex-max`          | GPT-5.1 Codex Max        |
| `gpt-4.1`                    | GPT-4.1                  |
| `gemini-3-pro`               | Gemini 3 Pro             |

**Note:** The full list depends on what VibeProxy exposes. Use `[7] Manage Droid Models → [1] View Models` in the PowerShell TUI to see all configured models.

### Autonomy Levels

The `--auto` flag controls how much Droid can do without confirmation:

| Level    | Description                      |
| -------- | -------------------------------- |
| `low`    | Ask before most actions (safest) |
| `medium` | Ask before destructive actions   |
| `high`   | Minimal prompts, more autonomous |

### Common Droid Exec Options

```powershell
droid exec --help                    # Show all options
droid exec -m custom:MODEL           # Specify model
droid exec --auto medium             # Set autonomy level
droid exec --no-tools                # Disable tool use (text-only mode)
droid exec --verbose                 # Verbose output
```

### Troubleshooting Droid

**Model not found:**

```
Error: Model "custom:claude-sonnet" not found
```

- Check model ID is exact (use full model name)
- Verify model is in `~/.factory/config.json`
- Use TUI `[7] Manage Droid Models → [3] Sync All VibeProxy Models` to add missing models

**Connection refused:**

- Ensure SSH tunnel is running: `netstat -an | findstr 8317`
- Start tunnel via TUI `[1] Start SSH Tunnel`

**Empty response:**

- For GPT-5 models, temperature must be 1 (handled automatically by VibeProxy)
