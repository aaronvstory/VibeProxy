# VibeProxy-Windows

> **Fork of [automazeio/vibeproxy](https://github.com/automazeio/vibeproxy)** focused on Windows integration, Agent Zero (A0), and Droid CLI management.

Use your **Claude Code** and **ChatGPT/Codex** subscriptions on Windows by tunneling to VibeProxy running on your Mac.

## 🎯 What This Does

- **Problem:** AI tools on Windows need API keys → pay-per-token billing
- **Solution:** VibeProxy bridges your subscriptions → use existing Claude Code/ChatGPT Plus/Pro access
- **This repo:** Windows-side management tools, configs, and integration with Agent Zero + Droid CLI

## 🚀 Quick Start

```powershell
# Launch the main manager CLI
.\VibeProxy-Manager.ps1
```

This gives you a menu to: start SSH tunnel, browse models, switch A0 configs, test connectivity, manage Droid models.

**Detailed guides:** See `docs/VIBEPROXY-QUICKSTART.md` and `docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md`

## 📂 Key Files

### Launchers
- **VibeProxy-Manager.ps1** - All-in-one CLI manager (tunnel, models, configs, testing)
- **start-tui.bat** - Launch Python TUI with auto-tunnel (alternative interface)

### Scripts
- **ssh-tunnel-intelligent.py** - Smart tunnel with auto-reconnect and Mac discovery
- **ssh-tunnel-vibeproxy.ps1** - PowerShell tunnel script
- **scripts/** - Additional utilities (sync models, test connection, etc.)

### Configuration
- **vibeproxy-config.json** - Your Mac IP, SSH credentials, favorites (gitignored)
- **configs/a0-*.json** - Agent Zero model presets
- **factory-config-example.json** - Template for `~/.factory/config.json`

### Documentation
- **docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md** - Comprehensive integration guide
- **docs/VIBEPROXY-QUICKSTART.md** - Quick setup reference
- **CLAUDE.md** - AI assistant instructions for this codebase

## 🎯 Supported Clients

- ✅ **Agent Zero (A0)** - See [docs/A0-VIBEPROXY-FIXES.md](docs/A0-VIBEPROXY-FIXES.md)
- ✅ **Factory Droid CLI** - See main setup guide
- ✅ **OpenClaw/Clawdbot** - See [docs/OPENCLAW-VIBEPROXY-INTEGRATION.md](docs/OPENCLAW-VIBEPROXY-INTEGRATION.md)

## 🎬 Setup Overview

### On MacBook (One-Time):
1. Install VibeProxy from [GitHub Releases](https://github.com/automazeio/vibeproxy/releases)
2. Authenticate Claude Code + Codex in menu bar app
3. Enable SSH (System Settings → Sharing → Remote Login)
4. Note your Mac's IP: `ipconfig getifaddr en0`

### On Windows (One-Time):
1. Copy `vibeproxy-config.example.json` to `vibeproxy-config.json` and edit with your Mac's IP and username
2. Configure Factory: Copy `factory-config-example.json` to `~/.factory/config.json`

### Daily Usage:
```powershell
# 1. Start tunnel (keep window open)
.\ssh-tunnel-vibeproxy.ps1

# 2. Use Factory Droid
droid
/model  # Select VibeProxy model
```

## ✨ Features

- ✅ **Auto-reconnecting tunnel** - No manual restarts
- ✅ **Connection testing** - Verify setup works
- ✅ **Multiple models** - Claude Sonnet/Opus/Haiku + GPT-5.1/GPT-4
- ✅ **No API keys needed** - Uses your subscriptions
- ✅ **Windows compatible** - Works via SSH tunnel
- ✅ **Battle-tested** - Based on official VibeProxy docs

## 🎯 Supported Models

### Via Claude Code Subscription:
- Claude Sonnet 4.5
- Claude Opus 4.5
- Claude Haiku 4

### Via ChatGPT/Codex Subscription:
- GPT-5.1 Codex Max
- GPT-4 Turbo
- GPT-4o

### Optional (if authenticated):
- Gemini models
- Qwen models
- Antigravity models

## 🐛 Troubleshooting

**Quick diagnostics:**
```powershell
# On Windows
.\scripts\test-connection.ps1

# On Mac (copy scripts/mac/mac-vibeproxy-status.sh first)
~/vibeproxy-status.sh
```

**Common issues:**
- Connection refused → SSH tunnel not running
- Unauthorized → Check VibeProxy provider status on Mac
- Wrong IP → Verify Mac IP with `ipconfig getifaddr en0`

See [docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md](docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md) for detailed troubleshooting.

## 📚 Requirements

### MacBook
- ✅ Apple Silicon (M1/M2/M3/M4)
- ✅ macOS 13.0+ (Ventura or later)
- ✅ SSH enabled

### Windows PC
- ✅ Windows 10/11 (SSH client built-in)
- ✅ Factory Droid/CLI installed
- ✅ Network access to Mac

### Subscriptions
- ✅ Claude Code Pro/Max OR
- ✅ ChatGPT Plus/Pro OR
- ✅ Both (recommended)

## 🔗 Resources

- **VibeProxy GitHub:** https://github.com/automazeio/vibeproxy
- **Factory CLI Docs:** https://docs.factory.ai/cli
- **Port Used:** 8317 (VibeProxy local server)

## 💡 Pro Tips

1. **Skip password prompts:** Set up SSH key authentication
2. **Auto-start tunnel:** Add script to Windows startup folder
3. **Monitor logs:** `tail -f ~/Library/Logs/VibeProxy/vibeproxy.log` on Mac

## 🎓 How It Works

```
┌─────────────┐         SSH Tunnel          ┌─────────────┐
│   Windows   │←─────────────────────────────│   MacBook   │
│             │  localhost:8317              │             │
│  Factory    │  ← port forward →            │  VibeProxy  │
│  Droid      │                              │   App       │
└─────────────┘                              └─────────────┘
                                                    ↓
                                             OAuth Providers
                                             - Claude Code
                                             - ChatGPT/Codex
```

1. **VibeProxy** on Mac handles OAuth with AI providers
2. **SSH tunnel** forwards `localhost:8317` from Windows to Mac
3. **Factory Droid** on Windows thinks it's talking to localhost
4. **Requests** tunnel to Mac → VibeProxy → Provider APIs
5. **Responses** come back the same way

## ❓ Questions?

1. **First time?** → [docs/VIBEPROXY-QUICKSTART.md](docs/VIBEPROXY-QUICKSTART.md)
2. **Full reference** → [docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md](docs/VIBEPROXY-LLM-INTEGRATION-GUIDE.md)
3. **A0 Issues?** → [docs/A0-VIBEPROXY-FIXES.md](docs/A0-VIBEPROXY-FIXES.md)

---

**Ready to start?** → Run `.\VibeProxy-Manager.ps1`!
