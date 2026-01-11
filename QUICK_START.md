# VibeProxy Quick Start - Windows + Mac Setup

## 🚀 5-Minute Setup (TL;DR)

### On MacBook:
```bash
# 1. Download & install
open https://github.com/automazeio/vibeproxy/releases
# Move VibeProxy.app to /Applications/

# 2. Launch & authenticate
open /Applications/VibeProxy.app
# Click menu bar icon → Settings → Connect (Claude Code, Codex)

# 3. Enable SSH
sudo systemsetup -setremotelogin on

# 4. Get your IP
ipconfig getifaddr en0
# Example: 192.168.1.100
```

### On Windows:
```powershell
# 1. Edit config with your Mac's IP (preferred)
notepad F:\claude\VibeProxy\vibeproxy-config.json
# Set: MacUser and MacIP (or edit ssh-tunnel-vibeproxy.ps1)

# 2. Start tunnel (keep window open)
.\ssh-tunnel-vibeproxy.ps1

# 3. Test connection (in new window)
.\test-connection.ps1
# Should show: 3/3 tests passed

# 4. Configure Factory
notepad C:\Users\YourName\.factory\config.json
# Copy from: factory-config-example.json

# 5. Use Factory Droid
droid
/model
# Select "Claude Sonnet 4.5 (VibeProxy)"
# Chat away!
```

---

## 📂 Files in This Directory

| File | Purpose |
|------|---------|
| `SETUP_GUIDE.md` | **Complete setup instructions** (read this first!) |
| `QUICK_START.md` | This file - quick reference |
| `ssh-tunnel-vibeproxy.ps1` | **Windows script** - creates SSH tunnel (auto-reconnect) |
| `test-connection.ps1` | **Windows script** - verifies tunnel is working |
| `factory-config-example.json` | **Factory config** - copy to `~/.factory/config.json` |
| `mac-vibeproxy-status.sh` | **Mac script** - check VibeProxy status |

---

## ⚡ Daily Workflow

```powershell
# 1. Start tunnel (one-time per session)
.\ssh-tunnel-vibeproxy.ps1
# Keep window open in background

# 2. Use Factory Droid normally
droid
/model
# Select VibeProxy model
# Chat!
```

That's it! 🎉

---

## 🐛 Troubleshooting (Quick Fixes)

### "Connection refused" on Windows
```powershell
# Check tunnel is running
Get-Process ssh | Where-Object {$_.CommandLine -like "*8317*"}

# If not running:
.\ssh-tunnel-vibeproxy.ps1
```

### Factory Droid can't connect
```powershell
# Test tunnel
.\test-connection.ps1

# Should show: 3/3 passed
# If not, check errors and fix
```

### SSH tunnel won't start
```bash
# On Mac: Enable SSH
sudo systemsetup -setremotelogin on

# Verify IP
ipconfig getifaddr en0

# Update config with correct IP
notepad vibeproxy-config.json
```

---

## 🔗 Quick Links

- **VibeProxy GitHub:** https://github.com/automazeio/vibeproxy
- **Full Setup Guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Factory CLI Docs:** https://docs.factory.ai/cli

---

## ❓ Need Help?

1. **Read full guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. **Check Mac status:**
   ```bash
   # On Mac
   ~/vibeproxy-status.sh
   ```
3. **Test Windows connection:**
   ```powershell
   # On Windows
   .\test-connection.ps1
   ```
4. **Gather debug info:**
   - Mac status output
   - Windows test output
   - Factory config: `cat ~/.factory/config.json`
   - Error messages

---

## 💡 Pro Tips

**Skip password prompts:**
```powershell
# On Windows: Generate SSH key
ssh-keygen -t ed25519

# Copy to Mac (enter password once)
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh yourname@192.168.1.100 "cat >> ~/.ssh/authorized_keys"

# Now tunnel connects without password!
```

**Auto-start tunnel on Windows boot:**
1. Right-click `ssh-tunnel-vibeproxy.ps1` → Create shortcut
2. Press `Win+R` → Type `shell:startup` → Enter
3. Move shortcut there
4. Tunnel starts when Windows boots!

**Monitor VibeProxy logs on Mac:**
```bash
tail -f ~/Library/Logs/VibeProxy/vibeproxy.log
```

---

## 🎯 What You Get

✅ Use **Claude Code subscription** in Factory Droid
✅ Use **ChatGPT/Codex subscription** in Factory Droid
✅ No separate API keys needed
✅ No pay-per-token billing
✅ Works on Windows via SSH tunnel
✅ Auto-reconnects if connection drops

---

**Questions?** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed troubleshooting!
