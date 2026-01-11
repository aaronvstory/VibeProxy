"""Data models for VibeProxy Manager."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Model(BaseModel):
    """Represents an AI model from VibeProxy."""

    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "vibeproxy"

    @property
    def provider(self) -> str:
        """Determine the provider from model ID."""
        id_lower = self.id.lower()
        if "claude" in id_lower:
            return "Anthropic"
        elif "gpt" in id_lower:
            return "OpenAI"
        elif "gemini" in id_lower:
            return "Google"
        elif "grok" in id_lower:
            return "xAI"
        elif "raptor" in id_lower:
            return "Raptor"
        else:
            return "Other"

    @property
    def display_name(self) -> str:
        """Human-friendly display name."""
        return MODEL_DISPLAY_NAMES.get(self.id, self.id)


class ChatMessage(BaseModel):
    """A message in a chat conversation."""

    role: str  # "user", "assistant", "system"
    content: str


class ChatResponse(BaseModel):
    """Response from a chat completion."""

    content: str
    tokens: int = 0
    elapsed: float = 0.0
    model: str = ""
    finish_reason: str = "stop"


class A0Config(BaseModel):
    """Agent Zero configuration preset."""

    name: str
    path: str
    model: str = ""
    description: str = ""


# Display names for known models
MODEL_DISPLAY_NAMES = {
    # Claude (Anthropic direct)
    "claude-opus-4-5-20251101": "Claude Opus 4.5 (Latest)",
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
    "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
    "claude-opus-4-1-20250805": "Claude Opus 4.1",
    "claude-sonnet-4-20250514": "Claude Sonnet 4",
    "claude-3-7-sonnet-20250219": "Claude 3.7 Sonnet",
    "claude-3-5-haiku-20241022": "Claude 3.5 Haiku",
    # Claude (via Copilot)
    "claude-opus-4.5": "Claude Opus 4.5 (Copilot)",
    "claude-sonnet-4.5": "Claude Sonnet 4.5 (Copilot)",
    "claude-haiku-4.5": "Claude Haiku 4.5 (Copilot)",
    # GPT
    "gpt-5.2-codex": "GPT-5.2 Codex",
    "gpt-5.2": "GPT-5.2",
    "gpt-5.1-codex-max": "GPT-5.1 Codex Max (Best)",
    "gpt-5.1-codex": "GPT-5.1 Codex",
    "gpt-5.1-codex-mini": "GPT-5.1 Codex Mini",
    "gpt-5.1": "GPT-5.1",
    "gpt-5-codex": "GPT-5 Codex",
    "gpt-5-codex-mini": "GPT-5 Codex Mini",
    "gpt-5": "GPT-5",
    "gpt-5-mini": "GPT-5 Mini",
    "gpt-4.1": "GPT-4.1",
    # Gemini
    "gemini-3-pro-preview": "Gemini 3 Pro Preview",
    "gemini-3-flash-preview": "Gemini 3 Flash Preview",
    "gemini-3-pro": "Gemini 3 Pro",
    "gemini-2.5-pro": "Gemini 2.5 Pro (1M ctx)",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite",
    # Other
    "grok-code-fast-1": "Grok Code Fast",
    "raptor-mini": "Raptor Mini",
}


# Provider order for grouping
PROVIDER_ORDER = ["Anthropic", "OpenAI", "Google", "xAI", "Raptor", "Other"]
