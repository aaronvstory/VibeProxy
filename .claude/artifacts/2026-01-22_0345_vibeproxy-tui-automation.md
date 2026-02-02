# Session Handoff: VibeProxy TUI Updates & Automation Scripts

Created: 2026-01-22 03:45

---

## Goal

Implement Python TUI updates for VibeProxy Manager:
1. Add Droid model management screen (same as PowerShell TUI)
2. Fix SSH tunnel window launch not opening properly
3. Create automation scripts for headless workflows
4. Document everything properly with provider information

## Goal Clarifications

- **Expanded scope:** User wanted not just TUI updates but full automation scripts for Droid CLI headless mode
- **Model sync requirement:** "Sync all" functionality to both Droid and A0 (Agent Zero)
- **Provider visibility:** User emphasized needing to know which provider (anthropic, copilot, google, openai, qwen) each model routes through
- **Documentation:** All changes need comprehensive docs in `docs/` folder

## User Emphasis (IMPORTANT)

> These are things the user repeated or stressed as critical.

- ⚠️ **Provider tags on models:** User repeatedly asked "how do I know which provider?" - models MUST show `[provider]` tags like `[anthropic]`, `[copilot]`, `[google]`
- ⚠️ **Exact model IDs in docs:** The display names don't matter for usage - docs must have exact model IDs to use with `custom:` prefix
- ⚠️ **Droid uses settings.json, NOT config.json:** Critical discovery - Droid reads `customModels` from `~/.factory/settings.json` with camelCase field names
- ⚠️ **A0 requires restart to switch models:** Cannot hot-swap models in A0, must restart container

## Current State

- **Status:** Completed with one verification needed
- **What's done:**
  - Python TUI: Droid management screen (`vibeproxy_manager/screens/droid_models.py`)
  - Python TUI: SSH tunnel fix using `CREATE_NEW_CONSOLE`
  - Config helper methods in `config.py` for Factory/Droid
  - Automation scripts: `scripts/start-tunnel-headless.py`, `scripts/sync-models-to-droid.py`, `scripts/sync-models-to-a0.py`, `scripts/droid-vibeproxy.ps1`
  - Documentation: `docs/DROID-AUTOMATION.md`, `docs/VIBEPROXY-MODELS.md`
  - Model sync with provider tags now writes to correct location (`settings.json`)
- **What needs verification:**
  - User should run `droid` CLI and verify models now show `[provider]` tags
  - The sync was just fixed to write to `settings.json` instead of `config.json`

## Key Decisions

- **Droid config location:** `~/.factory/settings.json` with `customModels` array (camelCase), NOT `config.json`
- **Model format for Droid:** Must include `id`, `index`, `baseUrl`, `apiKey`, `displayName`, `noImageSupport`, `provider`, `model` fields
- **Provider short names:** `anthropic`, `copilot` (for github-copilot), `google`, `openai`, `qwen`
- **A0 presets:** One JSON file per model in `configs/a0-*.json`

## Files Modified

- `vibeproxy_manager/config.py` - Added 4 new Factory helper methods + settings.json functions
- `vibeproxy_manager/screens/droid_models.py` - **NEW** Droid management screen
- `vibeproxy_manager/screens/main_menu.py` - Added option 8 for Droid, updated help
- `vibeproxy_manager/screens/__init__.py` - Export DroidModelsScreen
- `vibeproxy_manager/tunnel.py` - Fixed `start_in_window()` to use CREATE_NEW_CONSOLE
- `scripts/start-tunnel-headless.py` - **NEW** Headless tunnel launcher
- `scripts/sync-models-to-droid.py` - **NEW** Droid model sync (fixed to use settings.json)
- `scripts/sync-models-to-a0.py` - **NEW** A0 preset generator
- `scripts/droid-vibeproxy.ps1` - **NEW** All-in-one wrapper
- `docs/DROID-AUTOMATION.md` - **NEW** Full automation guide
- `docs/VIBEPROXY-MODELS.md` - **NEW** All models by provider

## DO NOTs & Constraints

- ❌ **DO NOT:** Write Droid models to `config.json` - Droid reads from `settings.json`
- ❌ **DO NOT:** Use snake_case fields for Droid - must be camelCase (`displayName`, `baseUrl`, `apiKey`)
- ❌ **DO NOT:** Forget the `custom:` prefix when calling Droid models
- ❌ **DO NOT:** Expect A0 to hot-swap models - requires container restart
- ⚠️ **Constraint:** GPT-5 models require `temperature=1` (handled by VibeProxy)

## Attempted Approaches

- **Approach 1:** Writing to `~/.factory/config.json` with `custom_models` field
  - **Result:** Failed - Droid didn't see the models
  - **Why:** Droid actually reads from `settings.json` with `customModels` (camelCase)
  - **Lesson:** Always verify where the target app reads its config from

## Assumptions to Validate

- 🔍 **Droid reload works:** User ran `droid config --reload` but models still showed old format - need to verify fresh sync fixed it
- 🔍 **Provider API field:** Assuming VibeProxy API always returns `owned_by` field - verify this persists

## Relevant Artifacts

### Droid settings.json model format (CORRECT)
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "id": "custom:Claude-Sonnet-4.5-[anthropic]-0",
  "index": 0,
  "baseUrl": "http://localhost:8317/v1",
  "apiKey": "dummy-not-used",
  "displayName": "Claude Sonnet 4.5 [anthropic]",
  "noImageSupport": false,
  "provider": "openai"
}
```

### Provider mappings
```
anthropic      → Claude models with dated IDs (direct API)
github-copilot → Most GPT-5.x, short Claude names, Gemini 3 (via Copilot)
google         → gemini-2.5-flash, gemini-2.5-flash-lite (direct)
openai         → gpt-5-codex-mini (direct)
qwen           → Qwen models, vision-model
```

## Next Action

**Verify the fix worked:**
1. Have user open Droid CLI and check model list
2. All models should now show `[provider]` tags like `Claude Sonnet 4.5 [anthropic]`
3. If still showing old `(VibeProxy)` format, may need to fully restart Droid or check for additional caching

---

## Resume Instructions

To continue this work in a fresh session:
```
Read handoffs/2026-01-22_0345_vibeproxy-tui-automation.md and resume the work.
```

CRITICAL:
- Check "User Emphasis (IMPORTANT)" first - these are things I had to repeat.
- Check "DO NOTs & Constraints" to avoid regressions.
- Check "Attempted Approaches" to avoid repeating failed attempts.
- Validate "Assumptions to Validate" early - don't build on shaky ground.
- Start with "Next Action".
