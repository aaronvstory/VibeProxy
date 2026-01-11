# VibeProxy Setup for Windows + Mac

Use your **Claude Code** and **ChatGPT/Codex** subscriptions in Factory Droid on Windows by running VibeProxy on your MacBook with an SSH tunnel.

## 🎯 What This Does

- **Problem:** Factory Droid requires API keys → pay-per-token billing
- **Solution:** VibeProxy bridges your subscriptions → use existing Claude Code/ChatGPT Plus/Pro access
- **Catch:** VibeProxy is macOS-only (M1+ required)
- **Fix:** Run on Mac, tunnel to Windows via SSH (this guide!)

## 🚀 Quick Start

**New to this?** → Read [QUICK_START.md](QUICK_START.md) for 5-minute setup
**Want details?** → Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete instructions

## 📂 What's Included

This directory contains everything you need:

### Documentation
- **QUICK_START.md** - 5-minute setup guide
- **SETUP_GUIDE.md** - Complete installation & troubleshooting
- **README.md** - This file

### Windows Scripts
- **ssh-tunnel-vibeproxy.ps1** - Auto-reconnecting SSH tunnel
- **test-connection.ps1** - Verify tunnel is working

### Configuration
- **vibeproxy-config.example.json** - Example config (copy to `vibeproxy-config.json` and edit)
- **factory-config-example.json** - Copy to `~/.factory/config.json`

### Mac Scripts
- **mac-vibeproxy-status.sh** - Check VibeProxy status (copy to Mac)

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
.\test-connection.ps1

# On Mac (copy mac-vibeproxy-status.sh first)
~/vibeproxy-status.sh
```

**Common issues:**
- Connection refused → SSH tunnel not running
- Unauthorized → Check VibeProxy provider status on Mac
- Wrong IP → Verify Mac IP with `ipconfig getifaddr en0`

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed troubleshooting.

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

1. **Skip password prompts:** Set up SSH key authentication (see SETUP_GUIDE.md)
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

1. **First time?** → [QUICK_START.md](QUICK_START.md)
2. **Need details?** → [SETUP_GUIDE.md](SETUP_GUIDE.md)
3. **Still stuck?** → Run diagnostics and check guide's troubleshooting section

---

**Ready to start?** → Open [QUICK_START.md](QUICK_START.md)!
