#!/usr/bin/env python3
"""Sync VibeProxy models to Droid CLI (headless).

Usage:
    python sync-models-to-droid.py [--list] [--clear]

Fetches all models from VibeProxy API and adds them to ~/.factory/config.json.
Requires SSH tunnel to be running.
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path


def load_vibeproxy_config() -> dict:
    """Load VibeProxy config."""
    config_path = Path(__file__).parent.parent / "vibeproxy-config.json"
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def load_factory_settings() -> dict:
    """Load Droid/Factory settings.json (where custom models are stored)."""
    settings_path = Path.home() / ".factory" / "settings.json"
    if not settings_path.exists():
        return {"customModels": []}

    try:
        with open(settings_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"customModels": []}


def save_factory_settings(data: dict) -> None:
    """Save Droid/Factory settings.json."""
    settings_path = Path.home() / ".factory" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# Keep old functions for backwards compatibility with config.json
def load_factory_config() -> dict:
    """Load Droid/Factory config.json (legacy)."""
    config_path = Path.home() / ".factory" / "config.json"
    if not config_path.exists():
        return {"custom_models": []}

    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"custom_models": []}


def save_factory_config(data: dict) -> None:
    """Save Droid/Factory config.json (legacy)."""
    config_path = Path.home() / ".factory" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fetch_vibeproxy_models(port: int) -> list[dict]:
    """Fetch available models from VibeProxy API.

    Returns list of dicts with 'id' and 'owned_by' (provider) fields.
    """
    url = f"http://localhost:{port}/v1/models"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("data", [])
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot reach VibeProxy at {url}", file=sys.stderr)
        print(f"       Is the SSH tunnel running?", file=sys.stderr)
        print(f"       Error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to fetch models: {e}", file=sys.stderr)
        sys.exit(1)


def get_provider_short(provider: str) -> str:
    """Get short provider name for display."""
    mappings = {
        "anthropic": "anthropic",
        "github-copilot": "copilot",
        "google": "google",
        "openai": "openai",
        "qwen": "qwen",
    }
    return mappings.get(provider, provider)


def get_display_name(model_id: str) -> str:
    """Generate a human-readable display name from model ID."""
    # Common mappings
    mappings = {
        "claude-opus-4-5-20251101": "Claude Opus 4.5",
        "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
        "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
        "gpt-5.2-codex": "GPT-5.2 Codex",
        "gpt-5.2": "GPT-5.2",
        "gpt-5.1-codex-max": "GPT-5.1 Codex Max",
        "gpt-5.1-codex-mini": "GPT-5.1 Codex Mini",
        "gpt-5.1-codex": "GPT-5.1 Codex",
        "gpt-5-mini": "GPT-5 Mini",
        "gpt-5": "GPT-5",
        "gpt-4.1": "GPT-4.1",
        "gpt-4.1-mini": "GPT-4.1 Mini",
        "gemini-3-pro": "Gemini 3 Pro",
        "gemini-2.5-pro": "Gemini 2.5 Pro",
        "gemini-2.5-flash": "Gemini 2.5 Flash",
    }

    if model_id in mappings:
        return mappings[model_id]

    # Auto-generate: replace dashes/underscores with spaces, title case
    return model_id.replace("-", " ").replace("_", " ").title()


def sync_models(port: int, clear_first: bool = False) -> tuple[int, int]:
    """Sync VibeProxy models to Droid settings.json.

    Returns (added_count, total_count).
    """
    # Fetch models from VibeProxy
    vp_models = fetch_vibeproxy_models(port)
    print(f"Found {len(vp_models)} models from VibeProxy")

    # Load existing Factory settings (where Droid stores customModels)
    factory_settings = load_factory_settings()
    existing_models = factory_settings.get("customModels", [])

    if clear_first:
        print(f"Clearing {len(existing_models)} existing models")
        existing_models = []

    # Get existing model IDs
    existing_ids = {m.get("model") for m in existing_models}

    # Add new models
    base_url = f"http://localhost:{port}/v1"
    added_count = 0
    next_index = len(existing_models)

    for model in vp_models:
        model_id = model.get("id")
        if not model_id:
            continue

        if model_id not in existing_ids:
            display_name = get_display_name(model_id)
            provider = model.get("owned_by", "unknown")
            provider_short = get_provider_short(provider)
            full_display = f"{display_name} [{provider_short}]"

            # Droid settings.json format (camelCase fields)
            entry = {
                "model": model_id,
                "id": f"custom:{full_display.replace(' ', '-')}-{next_index}",
                "index": next_index,
                "baseUrl": base_url,
                "apiKey": "dummy-not-used",
                "displayName": full_display,
                "noImageSupport": False,
                "provider": "openai",
            }
            existing_models.append(entry)
            existing_ids.add(model_id)
            added_count += 1
            next_index += 1
            print(f"  + Added: {model_id} [{provider_short}]")

    # Save to settings.json (where Droid reads from)
    factory_settings["customModels"] = existing_models
    save_factory_settings(factory_settings)

    return added_count, len(existing_models)


def list_models() -> None:
    """List current Droid custom models."""
    settings = load_factory_settings()
    models = settings.get("customModels", [])

    if not models:
        print("No custom models configured in Droid")
        return

    print(f"Droid Custom Models ({len(models)}):")
    print("-" * 60)
    for m in models:
        model_id = m.get("model", "?")
        display = m.get("displayName", model_id)
        print(f"  custom:{model_id}")
        print(f"    Display: {display}")
    print("-" * 60)
    print(f'\nUsage: droid exec -m custom:<model-id> "prompt"')


def clear_models() -> None:
    """Clear all custom models from Droid."""
    settings = load_factory_settings()
    count = len(settings.get("customModels", []))
    settings["customModels"] = []
    save_factory_settings(settings)
    print(f"Cleared {count} custom models from Droid")


def main():
    parser = argparse.ArgumentParser(description="Sync VibeProxy models to Droid CLI")
    parser.add_argument(
        "--list", action="store_true", help="List current Droid models (no sync)"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear all models before syncing"
    )
    parser.add_argument(
        "--clear-only", action="store_true", help="Only clear models (no sync)"
    )
    args = parser.parse_args()

    if args.list:
        list_models()
        return

    if args.clear_only:
        clear_models()
        return

    # Load config for port
    vp_config = load_vibeproxy_config()
    port = vp_config.get("LocalPort", 8317)

    # Sync models
    added, total = sync_models(port, clear_first=args.clear)
    print(f"\nSync complete: {added} added, {total} total models")
    print(f'\nUsage: droid exec -m custom:<model-id> "prompt"')


if __name__ == "__main__":
    main()
