"""VibeProxy API client."""

import httpx
import time
from typing import Optional, Any

from .models import Model, ChatMessage, ChatResponse


class VibeProxyClient:
    """Async HTTP client for VibeProxy API."""

    # Class-level cache for model list (shared across instances)
    _model_cache: dict[str, Any] = {
        "models": [],
        "last_refresh": 0.0,
        "cache_seconds": 30,  # Cache TTL in seconds
    }

    def __init__(self, base_url: str = "http://localhost:8317"):
        """Initialize with VibeProxy base URL."""
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            # Use reasonable timeouts: 30s for requests, 5s for connect
            # This prevents UI blocking on slow/hung connections
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=5.0),
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check if VibeProxy is reachable."""
        try:
            client = await self._get_client()
            response = await client.get("/v1/models", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self, force_refresh: bool = False) -> list[Model]:
        """Get list of available models from VibeProxy.

        Uses a 30-second cache to prevent UI blocking on repeated calls.
        Pass force_refresh=True to bypass cache (e.g., for explicit refresh action).
        """
        cache = VibeProxyClient._model_cache
        now = time.time()
        cache_age = now - cache["last_refresh"]

        # Return cached data if still valid
        if not force_refresh and cache_age < cache["cache_seconds"] and cache["models"]:
            return cache["models"]

        try:
            client = await self._get_client()
            # Use shorter timeout for model list (2s) to avoid blocking UI
            response = await client.get("/v1/models", timeout=5.0)
            response.raise_for_status()
            data = response.json()

            models = []
            for item in data.get("data", []):
                models.append(Model(
                    id=item.get("id", ""),
                    object=item.get("object", "model"),
                    created=item.get("created", 0),
                    owned_by=item.get("owned_by", "vibeproxy"),
                ))

            # Update cache
            cache["models"] = models
            cache["last_refresh"] = now
            return models
        except Exception as e:
            # On error, return cached data if available (stale is better than nothing)
            if cache["models"]:
                return cache["models"]
            raise ConnectionError(f"Failed to list models: {e}")

    async def chat(
        self,
        model: str,
        messages: list[ChatMessage] | list[dict],
        max_tokens: int = 500,
        temperature: Optional[float] = None,
    ) -> ChatResponse:
        """Send a chat completion request."""
        start_time = time.time()

        # Convert ChatMessage objects to dicts if needed
        msg_dicts = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                msg_dicts.append({"role": msg.role, "content": msg.content})
            else:
                msg_dicts.append(msg)

        # GPT-5 models require temperature=1
        if temperature is None:
            temperature = 1.0 if "gpt-5" in model.lower() else 0.0

        payload = {
            "model": model,
            "messages": msg_dicts,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            client = await self._get_client()
            response = await client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = ""
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                message = choice.get("message", {})
                content = message.get("content", "")
                finish_reason = choice.get("finish_reason", "stop")
            else:
                finish_reason = "error"

            # Extract token usage
            usage = data.get("usage", {})
            tokens = usage.get("total_tokens", 0)

            elapsed = time.time() - start_time

            return ChatResponse(
                content=content,
                tokens=tokens,
                elapsed=elapsed,
                model=model,
                finish_reason=finish_reason,
            )
        except httpx.HTTPStatusError as e:
            elapsed = time.time() - start_time
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            return ChatResponse(
                content=f"Error: {error_msg}",
                tokens=0,
                elapsed=elapsed,
                model=model,
                finish_reason="error",
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return ChatResponse(
                content=f"Error: {str(e)}",
                tokens=0,
                elapsed=elapsed,
                model=model,
                finish_reason="error",
            )

    async def preflight(self, model: str) -> tuple[bool, str]:
        """Test if a model is working with a simple request."""
        try:
            response = await self.chat(
                model=model,
                messages=[{"role": "user", "content": "Reply with just 'OK'"}],
                max_tokens=10,
            )
            if response.finish_reason == "error":
                return False, response.content
            return True, f"OK ({response.elapsed:.1f}s, {response.tokens} tokens)"
        except Exception as e:
            return False, str(e)

    async def test_connection(self) -> tuple[bool, str]:
        """Test VibeProxy connection and return status message."""
        try:
            client = await self._get_client()
            response = await client.get("/v1/models", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("data", []))
                return True, f"Connected ({count} models available)"
            return False, f"HTTP {response.status_code}"
        except httpx.ConnectError:
            return False, "Connection refused - is SSH tunnel running?"
        except httpx.TimeoutException:
            return False, "Connection timeout"
        except Exception as e:
            return False, str(e)
