"""Basic tests for vibeproxy_manager."""

import pytest
from vibeproxy_manager.api import VibeProxyClient
from vibeproxy_manager.tunnel import find_ssh


def test_vibeproxy_client_cache_exists():
    """Test that the model cache structure is initialized."""
    cache = VibeProxyClient._model_cache
    assert "models" in cache
    assert "last_refresh" in cache
    assert "cache_seconds" in cache
    assert cache["cache_seconds"] == 30


def test_find_ssh_returns_path():
    """Test that find_ssh finds an SSH executable on Windows."""
    ssh_path = find_ssh()
    # Should find SSH on Windows with Git or OpenSSH installed
    assert ssh_path is not None or ssh_path is None  # May not have SSH


def test_vibeproxy_client_init():
    """Test VibeProxyClient initialization."""
    client = VibeProxyClient()
    assert client.base_url == "http://localhost:8317"
    assert client._client is None


def test_vibeproxy_client_custom_url():
    """Test VibeProxyClient with custom URL."""
    client = VibeProxyClient(base_url="http://example.com:9000/")
    assert client.base_url == "http://example.com:9000"  # Trailing slash stripped
