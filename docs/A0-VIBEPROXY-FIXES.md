# Agent Zero (A0) + VibeProxy Configuration Fixes

## Quick Summary

This document describes the fixes implemented to resolve configuration issues when using Agent Zero with VibeProxy.

## Issues Fixed

### Issue 1: "Unknown Provider" Error (FIXED)

**Error Message:**

```
litellm.BadRequestError: OpenAIException - unknown provider for model claude-sonnet-4-5-20251101
```

**Root Cause:**

- PowerShell script was not setting the `chat_model_provider` field
- LiteLLM couldn't auto-detect the provider for VibeProxy models
- Empty/null provider field caused initialization failure

**Fix Applied:**
Added `Apply-ProviderRules` function to `VibeProxy-Manager.ps1` (lines 1062-1085) that automatically sets `provider: "other"` for all models using VibeProxy (port 8317).

**Location:** `F:/claude/VibeProxy/VibeProxy-Manager.ps1:1062-1085,1760`

**What Changed:**

```powershell
function Apply-ProviderRules {
    param($Cfg)

    # If using VibeProxy (api_base contains 8317), ensure provider is set to "other"
    if ($Cfg.chat_model_api_base -and $Cfg.chat_model_api_base -like "*8317*") {
        if (-not $Cfg.chat_model_provider) {
            $Cfg | Add-Member -NotePropertyName "chat_model_provider" -NotePropertyValue "other" -Force
        }
    }
    # Same for util_model and browser_model...
}
```

**Result:** ✅ All VibeProxy configs now have correct provider set automatically

---

### Issue 2: Memory Recall "/v1/responses" Error (WORKAROUND APPLIED)

**Error Message:**

```
litellm.exceptions.InternalServerError: InternalServerError: OpenAIException -
{"error":{"message":"auth_unavailable: no auth available","type":"server_error","code":"internal_server_error"}}

File "/a0/python/extensions/monologue_end/_51_memorize_solutions.py", line 46, in memorize
File "/opt/venv-a0/lib/python3.12/site-packages/litellm/responses/main.py", line 458, in aresponses
```

**Root Cause:**

- A0's memory system uses LiteLLM's **Responses API** for structured outputs
- Responses API calls `/v1/responses` endpoint
- **VibeProxy does NOT implement `/v1/responses`** (only supports `/v1/models` and `/v1/chat/completions`)
- LiteLLM tries to use advanced features that VibeProxy doesn't support

**Workaround Applied:**
Added parameters to `util_model_kwargs` in `settings.json` to force fallback to standard completions:

```json
"util_model_kwargs": {
  "temperature": "1",
  "drop_params": true,
  "supports_response_schema": false
}
```

**Location:** `C:/claude/agent-zero-data/tmp/settings.json:20-24`

**What This Does:**

- `drop_params: true` - Tells LiteLLM to ignore unsupported parameters
- `supports_response_schema: false` - Explicitly disables Responses API usage

**Result:** ⚠️ **NEEDS TESTING** - Restart A0 container and verify memory works

---

## Testing Instructions

### Step 1: Restart A0 Container

```bash
docker restart agent-zero
```

Wait 30 seconds for A0 to fully restart.

### Step 2: Test Chat Functionality

1. Open A0 UI: http://localhost:5080
2. Send message: "Hello, can you help me?"
3. **Expected:** Response from Claude Sonnet 4.5 without errors

### Step 3: Test Memory Recall

1. Send message: "Remember that my favorite color is blue"
2. Wait for confirmation
3. Send message: "What's my favorite color?"
4. **Expected:** Response correctly recalling "blue" without "Recall memories extension error"

### Step 4: Monitor Docker Logs

Open a terminal and watch logs in real-time:

```bash
docker logs -f agent-zero
```

**Look for:**

- ✅ No "Recall memories extension error"
- ✅ No "auth_unavailable" errors
- ✅ Successful model calls
- ❌ Any LiteLLM errors

**If you see errors:**

- Copy the full error message
- Check "Alternative Workarounds" section below

---

## Alternative Workarounds (If Testing Fails)

### Option A: Use Claude Haiku for Utility Model

GPT-5 models might be triggering the Responses API. Try switching to Claude Haiku:

**Edit:** `C:/claude/agent-zero-data/tmp/settings.json`

```json
"util_model_provider": "other",
"util_model_name": "claude-haiku-4-5-20251001",
"util_model_api_base": "http://host.docker.internal:8317/v1",
"util_model_kwargs": {
  "temperature": "0",
  "drop_params": true,
  "supports_response_schema": false
}
```

**Then restart A0:**

```bash
docker restart agent-zero
```

### Option B: Disable Memory Auto-Recall (Temporary)

If memory keeps failing, disable auto-recall as a temporary measure:

1. Open A0 Web UI: http://localhost:5080
2. Click Settings (gear icon)
3. Find "Memory" section
4. **Uncheck** "Memory auto-recall enabled"
5. Save settings

**Trade-off:** A0 still works for chat, but won't automatically retrieve memories. You can still manually save/recall via tools.

### Option C: Add More Fallback Parameters

If the above don't work, try adding more LiteLLM compatibility flags:

```json
"util_model_kwargs": {
  "temperature": "1",
  "drop_params": true,
  "supports_response_schema": false,
  "supports_function_calling": false,
  "supports_vision": false,
  "mode": "completion"
}
```

### Option D: Report to VibeProxy Developers

If none of the workarounds solve the issue, the long-term solution is to add `/v1/responses` support to VibeProxy.

**GitHub Issue Template:**

```markdown
**Title:** Add support for LiteLLM Responses API endpoint

**Description:**
Agent Zero's memory system uses LiteLLM's Responses API which requires the `/v1/responses` endpoint.
Currently VibeProxy only supports:

- `/v1/models` ✅
- `/v1/chat/completions` ✅
- `/v1/responses` ❌ (missing)

**Error:**
```

{"error":{"message":"auth_unavailable: no auth available","type":"server_error","code":"internal_server_error"}}

```

**Use Case:** Structured outputs for AI agents (A0, other frameworks)

**Request:** Implement `/v1/responses` endpoint as a wrapper around chat completions
```

---

## Files Modified

| File                    | Line(s)   | Change                                      |
| ----------------------- | --------- | ------------------------------------------- |
| `VibeProxy-Manager.ps1` | 1062-1085 | Added `Apply-ProviderRules` function        |
| `VibeProxy-Manager.ps1` | 1760      | Call `Apply-ProviderRules` in config switch |
| `tmp/settings.json`     | 20-24     | Added LiteLLM fallback parameters           |

---

## Verification Checklist

After applying all fixes:

- [ ] PowerShell script has `Apply-ProviderRules` function
- [ ] PowerShell script calls `Apply-ProviderRules` in `Switch-A0Config`
- [ ] `settings.json` has `drop_params: true` and `supports_response_schema: false`
- [ ] A0 container restarted successfully
- [ ] Chat messages work without errors
- [ ] Memory recall works without "extension error"
- [ ] Docker logs show no LiteLLM errors

---

## Rollback Instructions

If these fixes cause problems:

### Rollback PowerShell Script

```bash
cd F:/claude/VibeProxy
git checkout VibeProxy-Manager.ps1
```

### Restore Previous Settings

```bash
cd F:/claude/VibeProxy/configs/backups
# Find latest backup
ls -lt | head

# Copy back (replace TIMESTAMP with actual backup filename)
cp a0-backup-TIMESTAMP.json C:/claude/agent-zero-data/tmp/settings.json

# Restart A0
docker restart agent-zero
```

---

## Support

If issues persist after trying all workarounds:

1. **Check SSH Tunnel:**

   ```bash
   netstat -an | findstr 8317
   curl http://localhost:8317/v1/models
   ```

2. **Verify VibeProxy on Mac:**

   ```bash
   ssh your-mac "curl -s http://localhost:8317/v1/models"
   ```

3. **Check A0 Logs:**

   ```bash
   docker logs agent-zero --tail 200 > a0-debug.log
   ```

4. **Test Direct API Call:**
   ```bash
   curl -X POST http://localhost:8317/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "claude-sonnet-4-5-20250929", "messages": [{"role": "user", "content": "test"}], "max_tokens": 10}'
   ```

---

## Next Steps

1. **Test the fixes** following the Testing Instructions above
2. **Report results** - Does memory work now?
3. **If it fails**, try Alternative Workarounds in order (A → B → C → D)
4. **Update CLAUDE.md** if a specific workaround becomes the permanent solution

---

**Last Updated:** 2026-01-22
**Fixes Implemented By:** Claude Code
**Status:** ✅ Applied, ⚠️ Needs Testing
