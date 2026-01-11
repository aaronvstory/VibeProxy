"""Configuration management for VibeProxy Manager."""

from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
import json
import re

from .models import A0Config


class VibeProxyConfig(BaseModel):
    """Main configuration for VibeProxy Manager."""

    mac_user: str = "danielba"
    mac_ip: str = "192.168.50.70"
    local_port: int = 8317
    remote_port: int = 8317
    ssh_password: str = ""
    favorites: list[str] = Field(default_factory=list)
    disabled_models: list[str] = Field(default_factory=list)
    max_tokens: int = 500


class ConfigManager:
    """Manages configuration files and A0 presets."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize with optional custom base path."""
        self.base_path = base_path or Path(__file__).parent.parent
        self.config_path = self.base_path / "vibeproxy-config.json"
        self.configs_dir = self.base_path / "configs"
        # A0 settings path on Windows
        self.a0_settings_path = Path("C:/claude/agent-zero-data/tmp/settings.json")
        # Factory (droid-cli) config path
        self.factory_config_path = Path.home() / ".factory" / "config.json"
        self._config: Optional[VibeProxyConfig] = None

    def load(self) -> VibeProxyConfig:
        """Load configuration from file, using defaults if missing."""
        if self._config is not None:
            return self._config

        config = VibeProxyConfig()

        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                # Map JSON keys to pydantic fields (handle camelCase/PascalCase)
                mapped = {
                    "mac_user": data.get("MacUser", data.get("mac_user", config.mac_user)),
                    "mac_ip": data.get("MacIP", data.get("mac_ip", config.mac_ip)),
                    "local_port": data.get("LocalPort", data.get("local_port", config.local_port)),
                    "remote_port": data.get("RemotePort", data.get("remote_port", config.remote_port)),
                    "ssh_password": data.get("SSHPassword", data.get("ssh_password", config.ssh_password)),
                    "favorites": data.get("Favorites", data.get("favorites", [])),
                    "disabled_models": data.get("DisabledModels", data.get("disabled_models", [])),
                    "max_tokens": data.get("MaxTokens", data.get("max_tokens", config.max_tokens)),
                }
                config = VibeProxyConfig(**mapped)
            except (json.JSONDecodeError, Exception):
                pass  # Use defaults on error

        self._config = config
        return config

    def save(self, config: Optional[VibeProxyConfig] = None) -> None:
        """Save configuration to file."""
        if config is None:
            config = self._config or self.load()

        # Save with PascalCase keys for compatibility with PS1
        data = {
            "MacUser": config.mac_user,
            "MacIP": config.mac_ip,
            "LocalPort": config.local_port,
            "RemotePort": config.remote_port,
            "SSHPassword": config.ssh_password,
            "Favorites": config.favorites,
            "DisabledModels": config.disabled_models,
            "MaxTokens": config.max_tokens,
        }

        self.config_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )
        self._config = config

    def get_a0_configs(self) -> list[A0Config]:
        """Get list of available A0 configuration presets."""
        configs = []

        if not self.configs_dir.exists():
            return configs

        for path in sorted(self.configs_dir.glob("a0-*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                # Extract model from settings
                model = ""
                if "chat" in data and "model" in data["chat"]:
                    model = data["chat"]["model"]
                elif "chat_model" in data:
                    model = data["chat_model"]

                # Parse name from filename (a0-gpt-5.2-codex.json -> GPT-5.2 Codex)
                name = path.stem.replace("a0-", "").replace("-", " ").title()

                configs.append(A0Config(
                    name=name,
                    path=str(path),
                    model=model,
                    description=f"Uses {model}" if model else "",
                ))
            except (json.JSONDecodeError, Exception):
                continue

        return configs

    def get_current_a0_config(self) -> Optional[A0Config]:
        """Get the currently active A0 configuration."""
        if not self.a0_settings_path.exists():
            return None

        try:
            data = json.loads(self.a0_settings_path.read_text(encoding="utf-8"))
            model = ""
            if "chat" in data and "model" in data["chat"]:
                model = data["chat"]["model"]
            elif "chat_model" in data:
                model = data["chat_model"]

            return A0Config(
                name="Current",
                path=str(self.a0_settings_path),
                model=model,
            )
        except Exception:
            return None

    def backup_a0_config(self) -> Optional[Path]:
        """Create a backup of current A0 settings before modifying."""
        if not self.a0_settings_path.exists():
            return None
        try:
            from datetime import datetime
            backup_dir = self.base_path / "configs" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"settings_backup_{timestamp}.json"
            content = self.a0_settings_path.read_text(encoding="utf-8")
            backup_path.write_text(content, encoding="utf-8")
            return backup_path
        except Exception:
            return None

    def apply_a0_config(self, config: A0Config) -> bool:
        """Copy a preset config to A0's settings location."""
        try:
            source = Path(config.path)
            if not source.exists():
                return False

            # Ensure parent directory exists
            self.a0_settings_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy config
            content = source.read_text(encoding="utf-8")
            self.a0_settings_path.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False

    def create_config_for_model(self, model_id: str) -> Optional[Path]:
        """Create a new A0 config preset for a specific model."""
        # Template for new config
        template = {
            "chat": {
                "model": model_id,
                "api_base": "http://host.docker.internal:8317/v1",
            },
            "chat_model_kwargs": {
                "temperature": "1" if "gpt-5" in model_id.lower() else "0",
            },
        }

        # Generate filename
        safe_name = re.sub(r"[^a-z0-9-]", "-", model_id.lower())
        filename = f"a0-{safe_name}.json"
        path = self.configs_dir / filename

        # Ensure configs dir exists
        self.configs_dir.mkdir(parents=True, exist_ok=True)

        # Write config
        path.write_text(json.dumps(template, indent=2), encoding="utf-8")
        return path

    # Convenience methods for favorites
    def add_favorite(self, model_id: str) -> None:
        """Add a model to favorites."""
        config = self.load()
        if model_id not in config.favorites:
            config.favorites.append(model_id)
            self.save(config)

    def remove_favorite(self, model_id: str) -> None:
        """Remove a model from favorites."""
        config = self.load()
        if model_id in config.favorites:
            config.favorites.remove(model_id)
            self.save(config)

    def toggle_favorite(self, model_id: str) -> bool:
        """Toggle favorite status. Returns new state."""
        config = self.load()
        if model_id in config.favorites:
            config.favorites.remove(model_id)
            self.save(config)
            return False
        else:
            config.favorites.append(model_id)
            self.save(config)
            return True

    def is_favorite(self, model_id: str) -> bool:
        """Check if a model is favorited."""
        return model_id in self.load().favorites

    # Convenience methods for max_tokens
    def get_max_tokens(self) -> int:
        """Get current max_tokens setting."""
        return self.load().max_tokens

    def set_max_tokens(self, tokens: int) -> None:
        """Set max_tokens setting."""
        config = self.load()
        config.max_tokens = max(1, min(128000, tokens))  # Clamp to valid range
        self.save(config)

    # Factory (droid-cli) config helpers
    def load_factory_config(self) -> dict:
        """Load Factory config.json or return defaults if missing/invalid."""
        if not self.factory_config_path.exists():
            return {"custom_models": []}
        try:
            return json.loads(self.factory_config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return {"custom_models": []}

    def save_factory_config(self, data: dict) -> None:
        """Save Factory config.json, creating parent directories if needed."""
        self.factory_config_path.parent.mkdir(parents=True, exist_ok=True)
        self.factory_config_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

    def set_factory_default_model(self, model_id: str, display_name: str) -> tuple[bool, str]:
        """Upsert a model in Factory config and move it to the top.
        
        Returns:
            tuple[bool, str]: (success, message) where message describes the outcome.
        """
        try:
            # Check if .factory directory exists
            factory_dir = self.factory_config_path.parent
            if not factory_dir.exists():
                factory_dir.mkdir(parents=True, exist_ok=True)
            
            data = self.load_factory_config()
            models = data.get("custom_models")
            if not isinstance(models, list):
                models = []

            base_url = f"http://localhost:{self.load().local_port}/v1"
            entry = {
                "model_display_name": f"{display_name} (VibeProxy)",
                "model": model_id,
                "base_url": base_url,
                "api_key": "dummy-not-used",
                "provider": "openai"
            }

            # Remove any existing entry for this model
            models = [m for m in models if m.get("model") != model_id]
            # Insert chosen model at top
            models.insert(0, entry)
            data["custom_models"] = models

            self.save_factory_config(data)
            return True, f"Factory default set to {display_name}"
        except PermissionError:
            return False, f"Permission denied writing to {self.factory_config_path}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in Factory config: {e}"
        except OSError as e:
            return False, f"Cannot write to Factory config: {e}"
        except Exception as e:
            return False, f"Unexpected error updating Factory config: {e}"
