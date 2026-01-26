#!/usr/bin/env python3
"""Generate A0 config presets for all VibeProxy models.

Usage:
    python sync-models-to-a0.py [--list] [--clear]

Creates a0-<model-id>.json preset files in configs/ directory.
"""

import argparse
import json
import re
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


def fetch_vibeproxy_models(port: int) -> list[dict]:
    """Fetch available models from VibeProxy API."""
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


def get_display_name(model_id: str) -> str:
    """Generate a human-readable display name from model ID."""
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
        "gemini-3-pro": "Gemini 3 Pro",
        "gemini-2.5-pro": "Gemini 2.5 Pro",
        "gemini-2.5-flash": "Gemini 2.5 Flash",
    }

    if model_id in mappings:
        return mappings[model_id]

    return model_id.replace("-", " ").replace("_", " ").title()


def create_a0_config(model_id: str, provider: str, port: int) -> dict:
    """Create A0 config structure for a model."""
    # GPT-5 models require temperature=1
    is_gpt5 = "gpt-5" in model_id.lower()

    return {
        "_comment": f"Auto-generated for {model_id} via {provider}",
        "chat": {
            "model": model_id,
            "api_base": f"http://host.docker.internal:{port}/v1",
        },
        "chat_model_kwargs": {
            "temperature": "1" if is_gpt5 else "0",
        },
    }


def sync_models(
    port: int, configs_dir: Path, clear_first: bool = False
) -> tuple[int, int]:
    """Generate A0 config presets for all VibeProxy models.

    Returns (created_count, total_count).
    """
    # Fetch models from VibeProxy
    vp_models = fetch_vibeproxy_models(port)
    print(f"Found {len(vp_models)} models from VibeProxy")

    # Ensure configs directory exists
    configs_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing a0-*.json files if requested
    if clear_first:
        existing = list(configs_dir.glob("a0-*.json"))
        for f in existing:
            f.unlink()
        print(f"Cleared {len(existing)} existing A0 presets")

    # Get existing preset names
    existing_presets = {f.stem for f in configs_dir.glob("a0-*.json")}

    created_count = 0
    for model in vp_models:
        model_id = model.get("id")
        provider = model.get("owned_by", "unknown")
        if not model_id:
            continue

        # Generate safe filename
        safe_name = re.sub(r"[^a-z0-9-]", "-", model_id.lower())
        safe_name = re.sub(r"-+", "-", safe_name).strip("-")
        preset_name = f"a0-{safe_name}"

        if preset_name in existing_presets:
            continue  # Skip existing

        # Create config
        config = create_a0_config(model_id, provider, port)
        config_path = configs_dir / f"{preset_name}.json"

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        display_name = get_display_name(model_id)
        print(f"  + Created: {preset_name}.json ({display_name})")
        created_count += 1

    total = len(list(configs_dir.glob("a0-*.json")))
    return created_count, total


def list_presets(configs_dir: Path) -> None:
    """List current A0 presets."""
    presets = sorted(configs_dir.glob("a0-*.json"))

    if not presets:
        print("No A0 presets found in configs/")
        return

    print(f"A0 Presets ({len(presets)}):")
    print("-" * 60)
    for preset in presets:
        try:
            with open(preset, encoding="utf-8") as f:
                config = json.load(f)
            model = config.get("chat", {}).get("model", "?")
            temp = config.get("chat_model_kwargs", {}).get("temperature", "?")
            print(f"  {preset.name}")
            print(f"    Model: {model}")
            print(f"    Temperature: {temp}")
        except Exception:
            print(f"  {preset.name} (error reading)")
    print("-" * 60)
    print(f"\nSwitch via TUI: Option 3 (Switch A0 Config)")


def clear_presets(configs_dir: Path) -> None:
    """Clear all A0 presets."""
    presets = list(configs_dir.glob("a0-*.json"))
    for f in presets:
        f.unlink()
    print(f"Cleared {len(presets)} A0 presets")


def main():
    parser = argparse.ArgumentParser(
        description="Generate A0 config presets for VibeProxy models"
    )
    parser.add_argument(
        "--list", action="store_true", help="List current A0 presets (no sync)"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear existing presets before syncing"
    )
    parser.add_argument(
        "--clear-only", action="store_true", help="Only clear presets (no sync)"
    )
    args = parser.parse_args()

    # Paths
    project_dir = Path(__file__).parent.parent
    configs_dir = project_dir / "configs"

    if args.list:
        list_presets(configs_dir)
        return

    if args.clear_only:
        clear_presets(configs_dir)
        return

    # Load config for port
    vp_config = load_vibeproxy_config()
    port = vp_config.get("LocalPort", 8317)

    # Sync models
    created, total = sync_models(port, configs_dir, clear_first=args.clear)
    print(f"\nSync complete: {created} created, {total} total presets")
    print(f"\nSwitch via TUI: Option 3 (Switch A0 Config)")
    print(f"Or apply directly: Option 5 (Browse Models) → 'a' key")


if __name__ == "__main__":
    main()
