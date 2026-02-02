# Troubleshooting 404 Errors When Connecting to VibeProxy

This guide helps diagnose and resolve "404 page not found" errors when using VibeProxy.

---

## Quick Diagnosis

If you're getting 404 errors with 0 API time and $0.00 cost, the issue is almost certainly an **invalid model ID**. VibeProxy is running and responding, but it doesn't recognize the model you're requesting.

---

## Common Causes of 404 Errors

### 1. Invalid Model ID Format

**Problem:** Using model IDs that don't exist in VibeProxy.

**Examples of INVALID model IDs:**
```
gemini-claude-sonnet-4-5-thinking    # Mixed provider names - doesn't exist
anthropic/claude-opus-4-5            # Provider prefix format not supported
claude-opus-4.5                      # Missing date suffix for direct API
gpt5-codex                           # Wrong format (missing dot)
```

**Examples of VALID model IDs:**
```
claude-opus-4-5-20251101             # Anthropic direct API (with date)
claude-sonnet-4-5-20250929           # Anthropic direct API (with date)
claude-haiku-4-5-20251001            # Anthropic direct API (with date)
gpt-5.2-codex                        # OpenAI via Copilot
gpt-5.1-codex-max                    # OpenAI via Copilot
gemini-3-flash-preview               # Google Gemini
```

### 2. Extended Thinking Suffix Mistakes

**Problem:** Incorrect format for Claude's extended thinking mode.

**WRONG:**
```
gemini-claude-sonnet-4-5-thinking    # Invalid - mixed providers
claude-sonnet-thinking               # Invalid - missing date and token budget
claude-sonnet-4-5-thinking           # Invalid - missing date suffix
```

**CORRECT:**
```
claude-sonnet-4-5-20250929-thinking-5000    # Base model + -thinking- + token budget
claude-opus-4-5-20251101-thinking-10000     # Works with any Claude model
```

The format is: `<base-model-id>-thinking-<token-budget>`

### 3. Provider Prefix Format Not Supported

**Problem:** Using `provider/model` format (common in OpenRouter) which VibeProxy doesn't support.

**WRONG:**
```
anthropic/claude-opus-4-5
openai/gpt-5.2-codex
google/gemini-3-pro
```

**CORRECT:**
```
claude-opus-4-5-20251101
gpt-5.2-codex
gemini-3-pro-preview
```

---

## Step-by-Step Diagnosis

### Step 1: Verify VibeProxy is Running

Test the models endpoint to confirm VibeProxy is responding:

**Using curl (Mac/Linux):**
```bash
curl -s http://localhost:8317/v1/models | head -c 100
```

**Using PowerShell (Windows):**
```powershell
Invoke-RestMethod -Uri "http://localhost:8317/v1/models" -TimeoutSec 5
```

**Expected Response:** JSON starting with `{"object":"list","data":[`

If you get "Connection refused", VibeProxy isn't running or the SSH tunnel is down.

### Step 2: Get the List of Available Models

Retrieve the exact model IDs that VibeProxy supports:

**Using curl:**
```bash
curl -s http://localhost:8317/v1/models | jq '.data[].id'
```

**Using PowerShell:**
```powershell
$models = Invoke-RestMethod -Uri "http://localhost:8317/v1/models"
$models.data | ForEach-Object { $_.id }
```

**Sample Output:**
```
"claude-opus-4-5-20251101"
"claude-sonnet-4-5-20250929"
"claude-haiku-4-5-20251001"
"gpt-5.2-codex"
"gpt-5.1-codex-max"
"gemini-3-flash-preview"
...
```

### Step 3: Test with a Valid Model

Make a test request using an exact model ID from the list:

**Using curl:**
```bash
curl -X POST http://localhost:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "messages": [{"role": "user", "content": "Say OK"}],
    "max_tokens": 10
  }'
```

**Using PowerShell:**
```powershell
$body = @{
    model = "claude-sonnet-4-5-20250929"
    messages = @(@{role = "user"; content = "Say OK"})
    max_tokens = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8317/v1/chat/completions" `
    -Method POST `
    -Headers @{"Content-Type" = "application/json"} `
    -Body $body
```

---

## Using Built-in Diagnostic Tools

### PowerShell Test Script

Run the connection test script:

```powershell
.\scripts\test-connection.ps1
```

This performs three tests:
1. Port 8317 listening check
2. API endpoint response check
3. SSH tunnel process verification

### VibeProxy Manager Diagnostics

Launch the manager and use option 8 (Setup Diagnostics):

```powershell
.\VibeProxy-Manager.ps1
```

Then select `[8] Setup Diagnostics` which tests:
- Health endpoint connectivity
- Model list retrieval
- Actual API call with a working model

---

## Model ID Reference

### Claude Models (Anthropic Direct API)

These require the date suffix for direct API access:

| Model ID | Description |
|----------|-------------|
| `claude-opus-4-5-20251101` | Claude Opus 4.5 (Most capable) |
| `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 (Best value) |
| `claude-haiku-4-5-20251001` | Claude Haiku 4.5 (Fastest) |
| `claude-opus-4-1-20250805` | Claude Opus 4.1 |
| `claude-sonnet-4-20250514` | Claude Sonnet 4 |
| `claude-3-7-sonnet-20250219` | Claude 3.7 Sonnet |
| `claude-3-5-haiku-20241022` | Claude 3.5 Haiku |

### Claude Models (via GitHub Copilot)

These work without date suffix when routed through Copilot:

| Model ID | Description |
|----------|-------------|
| `claude-opus-4.5` | Claude Opus 4.5 (Copilot) |
| `claude-sonnet-4.5` | Claude Sonnet 4.5 (Copilot) |
| `claude-haiku-4.5` | Claude Haiku 4.5 (Copilot) |

### GPT Models

| Model ID | Description |
|----------|-------------|
| `gpt-5.2-codex` | GPT-5.2 Codex (Best reasoning) |
| `gpt-5.2` | GPT-5.2 |
| `gpt-5.1-codex-max` | GPT-5.1 Codex Max (Deep analysis) |
| `gpt-5.1-codex` | GPT-5.1 Codex |
| `gpt-5.1-codex-mini` | GPT-5.1 Codex Mini |
| `gpt-5.1` | GPT-5.1 |
| `gpt-5-codex` | GPT-5 Codex |
| `gpt-5-mini` | GPT-5 Mini |
| `gpt-5` | GPT-5 |
| `gpt-4.1` | GPT-4.1 |

### Gemini Models

| Model ID | Description |
|----------|-------------|
| `gemini-3-pro-preview` | Gemini 3 Pro Preview |
| `gemini-3-flash-preview` | Gemini 3 Flash Preview (Fast) |
| `gemini-3-pro-image-preview` | Gemini 3 Pro (Enhanced vision) |
| `gemini-2.5-pro` | Gemini 2.5 Pro |
| `gemini-2.5-flash` | Gemini 2.5 Flash |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite |

---

## Extended Thinking Mode

To enable Claude's extended thinking, append `-thinking-<tokens>` to a valid Claude model ID:

```
claude-sonnet-4-5-20250929-thinking-5000
claude-opus-4-5-20251101-thinking-10000
```

**Token Budget Guidelines:**
- Simple reasoning: 2,000 - 3,000
- Complex analysis: 5,000 - 8,000
- Deep problem solving: 10,000+

---

## Configuration for External Applications

When configuring external applications to use VibeProxy:

### Required Settings

| Setting | Value |
|---------|-------|
| Base URL | `http://localhost:8317/v1` |
| API Key | Any non-empty string (e.g., `vibeproxy`, `dummy`, `x`) |
| Model | Exact ID from `/v1/models` endpoint |

### Docker Containers

Use `host.docker.internal` instead of `localhost`:

```
http://host.docker.internal:8317/v1
```

### Example Configuration

```json
{
  "api_base": "http://localhost:8317/v1",
  "api_key": "vibeproxy",
  "model": "claude-sonnet-4-5-20250929"
}
```

---

## Quick Checklist

When you get a 404 error:

1. **Is VibeProxy running?** Test with `curl http://localhost:8317/v1/models`
2. **Is the model ID exact?** Copy it directly from the `/v1/models` response
3. **Are you using provider prefixes?** Remove any `anthropic/` or `openai/` prefixes
4. **Is the thinking suffix correct?** Format: `<model>-thinking-<number>`
5. **Is the date suffix present?** Direct API Claude models need dates like `-20250929`

---

## Related Documentation

- [VIBEPROXY-QUICKSTART.md](./VIBEPROXY-QUICKSTART.md) - Quick setup guide
- [VIBEPROXY-LLM-INTEGRATION-GUIDE.md](./VIBEPROXY-LLM-INTEGRATION-GUIDE.md) - Comprehensive integration guide
- [A0-VIBEPROXY-FIXES.md](./A0-VIBEPROXY-FIXES.md) - Agent Zero specific troubleshooting
