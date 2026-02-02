# Session Handoff: VibeProxy LLM Integration Guide - VALIDATION NEEDED

Created: 2026-01-25 13:30
Updated: 2026-01-25 14:00

---

## Goal

Create a comprehensive, single-file Markdown documentation that serves as a detailed guide for LLMs on VibeProxy integration. **NOW NEEDS VALIDATION.**

## Goal Clarifications

- **Scope:** LLM-focused documentation (not just human-readable quick start)
- **NEW:** Guide is ~2000 lines - need a Quick Start version (~100-200 lines)
- **NEW:** Endpoint routing needs empirical validation before guide is reliable

## User Emphasis (IMPORTANT)

> These are things the user repeated or stressed as critical.

- ⚠️ **UNVALIDATED: Base URL routing** - DeepWiki says Claude uses `http://localhost:8317` (no /v1), but ThinkingProxy code shows non-/v1 paths go to ampcode.com. **NEEDS TESTING**
- ⚠️ **No capabilities API exists** - `/v1/models` doesn't return vision/capability info, must use pattern matching
- ⚠️ **Vision is transparent** - VibeProxy passes vision data through unchanged, no special config needed
- ⚠️ **GPT-5 temperature=1** - All GPT-5 models require temperature=1 (LiteLLM enforces this)
- ⚠️ **Guide is too long** - User wants a Quick Start guide created

## Current State

- **Status:** NEEDS VALIDATION
- **What's done:**
  - Created comprehensive guide at `docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md` (~2000 lines)
  - Documented base URL differences based on DeepWiki (but UNVALIDATED)
- **What's broken/pending:**
  - Endpoint routing info may be WRONG - needs curl testing
  - No Quick Start guide exists yet
- **Active file(s):** `F:\claude\VibeProxy\docs\VIBEPROXY-LLM-INTEGRATION-GUIDE.md`

## Key Decisions

- **Pattern matching for vision detection:** Since VibeProxy has no capabilities API, use known model patterns (claude-3+, gpt-4+, gemini-*) to infer vision support
- **Dual base URL system:** Document that Claude models use `http://localhost:8317` while all other models use `http://localhost:8317/v1`
- **Extended thinking via model suffix:** Document the `-thinking-NUMBER` suffix for Claude models (e.g., `claude-sonnet-4-5-20250929-thinking-5000`)
- **Maintain local capabilities database:** Guide recommends maintaining your own `MODEL_CAPABILITIES` dict since API doesn't provide this

## Files Modified

- `docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md` - **Created** comprehensive LLM integration guide with:
  - 19 major sections
  - Complete API reference
  - Python/JavaScript/curl code examples
  - Configuration examples for A0, Droid CLI, LangChain, LiteLLM, OpenAI SDK
  - Model capability tables
  - Troubleshooting guides

## Related Work

The user was also helping someone implement VibeProxy in another project (`image-manipulator`). Key learnings applied:

- The `detectVisionCapability()` pattern matching approach was validated
- Claude Haiku 4.5 pattern was missing - fixed with simpler `id.startsWith("claude-")` approach
- Grok pattern was too restrictive - removed the `&& id.includes("vision")` requirement

## DO NOTs & Constraints

- ❌ **DO NOT** assume `/v1/models` returns capability metadata - it doesn't for VibeProxy
- ❌ **DO NOT** use `http://localhost:8317/v1` for Claude models - they use `http://localhost:8317` (no /v1)
- ❌ **DO NOT** set temperature != 1 for GPT-5 models - they require exactly temperature=1
- ⚠️ **Constraint:** VibeProxy only runs on Apple Silicon Macs (M1+)

## Relevant Artifacts

### Base URL by Provider (Critical)

| Provider | Base URL | Provider Setting |
|----------|----------|------------------|
| Claude (Anthropic) | `http://localhost:8317` | `"provider": "anthropic"` |
| GPT (OpenAI) | `http://localhost:8317/v1` | `"provider": "openai"` |
| Gemini (Google) | `http://localhost:8317/v1` | `"provider": "openai"` |
| All others | `http://localhost:8317/v1` | `"provider": "openai"` |

### Vision Detection Pattern (for implementations)

```python
# Simplified Claude pattern that catches all modern variants
if id.startswith("claude-"):
    if not id.includes("claude-2") and not id.includes("claude-instant"):
        return True  # All Claude 3+ have vision
```

## Attempted Approaches

- **DeepWiki research:** Found that Factory CLI configs use different base URLs for Claude vs others
- **But:** ThinkingProxy source shows non-/v1 paths go to ampcode.com, creating confusion
- **Lesson:** Don't trust config file conventions - need empirical testing

## Assumptions to Validate

> CRITICAL: These must be tested with curl before guide is reliable

- 🔍 Does `/v1/chat/completions` work for Claude models? (probably yes)
- 🔍 Does `/chat/completions` (no /v1) work or route to ampcode.com? (probably fails)
- 🔍 Does CLIProxyAPIPlus auto-detect provider from model name?
- 🔍 Is the base URL difference real, or just a LiteLLM configuration convention?

## Next Action

1. **Start SSH tunnel** to Mac running VibeProxy
2. **Run validation curl tests:**
```bash
# Test Claude with /v1
curl -s -X POST http://localhost:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20250929","messages":[{"role":"user","content":"Reply OK"}],"max_tokens":10}'

# Test Claude WITHOUT /v1 (what happens?)
curl -s -X POST http://localhost:8317/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20250929","messages":[{"role":"user","content":"Reply OK"}],"max_tokens":10}'

# Test GPT with /v1
curl -s -X POST http://localhost:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.2-codex","messages":[{"role":"user","content":"Reply OK"}],"max_tokens":10,"temperature":1}'
```
3. **Update guide** based on actual results
4. **Create Quick Start guide** (`docs/VIBEPROXY-QUICKSTART.md`, ~100-200 lines)

---

## Resume Instructions

To continue this work in a fresh session:
```
Read F:\claude\VibeProxy\handoffs\2026-01-25_1330_vibeproxy-llm-integration-guide.md and resume the work.
```

CRITICAL:
- **FIRST:** Run the validation curl tests in "Next Action" - the guide has UNVALIDATED info
- Check "Assumptions to Validate" - don't build on shaky ground
- The base URL documentation may be WRONG - test before trusting
- User wants a Quick Start guide created (guide is too long at 2000 lines)
