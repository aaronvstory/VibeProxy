# VibeProxy Setup Guide: Mac + Windows Configuration

## 🎯 Goal
Use your Claude Code and ChatGPT/Codex subscriptions in Factory Droid/CLI on **Windows** by running VibeProxy on your **MacBook** with an SSH tunnel.

## 📋 Requirements

### MacBook
- Apple Silicon (M1/M2/M3/M4)
- macOS 13.0 (Ventura) or later
- SSH enabled (for remote access from Windows)

### Windows PC
- SSH client (built into Windows 10/11)
- Factory Droid/CLI installed
- Network access to MacBook (same network or VPN)

---

## 🚀 Part 1: MacBook Setup

### Step 1: Install VibeProxy

1. **Download:**
   - Visit: https://github.com/automazeio/vibeproxy/releases
   - Download latest `VibeProxy.zip`

2. **Install:**
   ```bash
   # Extract and move to Applications
   unzip ~/Downloads/VibeProxy.zip
   mv VibeProxy.app /Applications/
   ```

3. **Launch:**
   - Open `/Applications/VibeProxy.app`
   - Menu bar icon appears
   - Server auto-starts on port **8317**

### Step 2: Authenticate Providers

1. Click VibeProxy menu bar icon → **"Open Settings"**
2. Click **"Connect"** for each provider you want:
   - ☑ **Claude Code** (for Claude models)
   - ☑ **Codex** (for ChatGPT/GPT models)
   - ☐ Gemini (optional)
   - ☐ Qwen (optional)
   - ☐ Antigravity (optional)

3. Browser opens OAuth flow for each → Complete authentication
4. VibeProxy detects credentials automatically
5. Status shows **"Connected ✅"**

### Step 3: Enable SSH on MacBook

```bash
# Enable Remote Login
sudo systemsetup -setremotelogin on

# Get your Mac's local IP address
ipconfig getifaddr en0

# Note this IP (e.g., 192.168.1.100)
```

**Alternative GUI method:**
1. System Settings → General → Sharing
2. Enable **"Remote Login"**
3. Note the connection string (e.g., `ssh yourname@192.168.1.100`)

### Step 4: Test VibeProxy Locally

```bash
# Verify server is running
curl http://localhost:8317/health

# Should return: {"status": "ok"} or similar
```

---

## 🪟 Part 2: Windows Setup

### Step 1: Set Up SSH Tunnel

**Manual method:**
```powershell
# Replace with your Mac's IP and username
ssh -L 8317:localhost:8317 yourname@192.168.1.100 -N
```

**Automated method** (see `ssh-tunnel-vibeproxy.ps1` script below):
- Creates persistent tunnel
- Auto-reconnects on failure
- Runs in background

### Step 2: Configure Factory Droid

Edit `C:\Users\YourName\.factory\config.json` (or `~/.factory/config.json` in Git Bash):

```json
{
  "custom_models": [
    {
      "model_display_name": "Claude Sonnet 4.5 (via VibeProxy)",
      "model": "claude-sonnet-4-5",
      "base_url": "http://localhost:8317",
      "api_key": "dummy-not-used",
      "provider": "anthropic"
    },
    {
      "model_display_name": "GPT-4 Turbo (via VibeProxy)",
      "model": "gpt-4-turbo",
      "base_url": "http://localhost:8317/v1",
      "api_key": "dummy-not-used",
      "provider": "openai"
    },
    {
      "model_display_name": "GPT-5.1 Codex Max (via VibeProxy)",
      "model": "gpt-5.1-codex-max",
      "base_url": "http://localhost:8317/v1",
      "api_key": "dummy-not-used",
      "provider": "openai"
    }
  ]
}
```

**Key Points:**
- **Claude models:** `base_url: "http://localhost:8317"`, `provider: "anthropic"`
- **OpenAI/GPT models:** `base_url: "http://localhost:8317/v1"`, `provider: "openai"`
- **API key:** Always use `"dummy-not-used"` (VibeProxy handles auth)

### Step 3: Test Connection

```powershell
# Test tunnel is working
curl http://localhost:8317/health

# Should return: {"status": "ok"}
```

### Step 4: Use in Factory Droid

```bash
# Start Droid
droid

# Select model
/model

# Choose your VibeProxy model (e.g., "Claude Sonnet 4.5 (via VibeProxy)")

# Send a test message
Hello! Can you confirm you're working via VibeProxy?
```

---

## 🔧 Helper Scripts

### Windows: SSH Tunnel Auto-Connect

Save as `F:\claude\VibeProxy\ssh-tunnel-vibeproxy.ps1`:

```powershell
# SSH Tunnel for VibeProxy (Auto-reconnect)
param(
    [string]$MacUser = "yourname",
    [string]$MacIP = "192.168.1.100"
)

Write-Host "🔌 Starting VibeProxy SSH Tunnel..." -ForegroundColor Cyan
Write-Host "   Mac: $MacUser@$MacIP" -ForegroundColor Gray
Write-Host "   Local Port: 8317 → Mac Port: 8317" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Keep this window open while using Factory Droid" -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to disconnect" -ForegroundColor Yellow
Write-Host ""

while ($true) {
    try {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Connecting..." -ForegroundColor Green
        ssh -o "ServerAliveInterval=60" -o "ServerAliveCountMax=3" `
            -L 8317:localhost:8317 `
            "$MacUser@$MacIP" -N
    }
    catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ Connection lost!" -ForegroundColor Red
    }

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🔄 Reconnecting in 5 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
```

**Usage:**
```powershell
# Edit the script with your Mac's IP and username, then run:
.\ssh-tunnel-vibeproxy.ps1
```

### MacBook: Quick Status Check

Save as `~/vibeproxy-status.sh`:

```bash
#!/bin/bash
echo "🔍 VibeProxy Status Check"
echo ""

# Check if app is running
if pgrep -x "VibeProxy" > /dev/null; then
    echo "✅ VibeProxy app is running"
else
    echo "❌ VibeProxy app is NOT running"
    echo "   → Launch /Applications/VibeProxy.app"
fi

# Check port 8317
if lsof -Pi :8317 -sTCP:LISTEN -t >/dev/null; then
    echo "✅ Port 8317 is listening"
else
    echo "❌ Port 8317 is NOT listening"
fi

# Test endpoint
if curl -s http://localhost:8317/health >/dev/null 2>&1; then
    echo "✅ Health endpoint responding"
else
    echo "⚠️  Health endpoint not responding (may be normal)"
fi

echo ""
echo "📊 Current connections to port 8317:"
lsof -i :8317 | grep LISTEN || echo "   None"
```

**Usage:**
```bash
chmod +x ~/vibeproxy-status.sh
~/vibeproxy-status.sh
```

---

## 🐛 Troubleshooting

### Windows Can't Connect to localhost:8317

**Check:**
1. Is SSH tunnel running?
   ```powershell
   # Should show ssh process with -L 8317
   Get-Process ssh
   ```

2. Is the tunnel actually forwarding?
   ```powershell
   netstat -ano | findstr :8317
   # Should show LISTENING on 127.0.0.1:8317
   ```

**Fix:**
```powershell
# Kill existing tunnels
Get-Process ssh | Stop-Process -Force

# Restart tunnel
.\ssh-tunnel-vibeproxy.ps1
```

### Factory Droid Can't Connect

**Error:** `Connection refused` or `Unauthorized`

**Check:**
1. **Tunnel active?** `curl http://localhost:8317/health`
2. **Config correct?** Check `~/.factory/config.json` for typos
3. **VibeProxy authenticated?** Check Mac menu bar → Settings → Provider status

**Fix:**
```bash
# Test tunnel manually
curl -v http://localhost:8317/health

# Should show HTTP 200 or similar (not connection refused)
```

### SSH Connection Fails

**Error:** `Connection refused` or `Permission denied`

**Check on Mac:**
```bash
# Is SSH enabled?
sudo systemsetup -getremotelogin
# Should show: Remote Login: On

# Is firewall blocking?
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

**Fix:**
```bash
# Enable SSH
sudo systemsetup -setremotelogin on

# Allow SSH through firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/sbin/sshd
```

### VibeProxy Not Starting on Mac

**Error:** "App is damaged" or won't launch

**Fix:**
```bash
# Remove quarantine attribute
xattr -cr /Applications/VibeProxy.app

# Re-launch
open /Applications/VibeProxy.app
```

### Providers Not Authenticating

**Issue:** OAuth flow completes but VibeProxy shows "Not Connected"

**Fix:**
1. Click "Disconnect" in VibeProxy settings
2. Close all browser tabs for that provider
3. Click "Connect" again
4. Complete OAuth flow in *new* browser window
5. Don't close browser until VibeProxy shows "Connected ✅"

---

## 🎯 Complete Workflow Example

### Initial Setup (One-time)
```powershell
# 1. On Mac: Install VibeProxy, authenticate providers, enable SSH

# 2. On Windows: Edit this with your Mac's info
notepad F:\claude\VibeProxy\ssh-tunnel-vibeproxy.ps1
# Change: $MacUser and $MacIP

# 3. Create Factory config
notepad C:\Users\YourName\.factory\config.json
# Add custom_models from examples above

# 4. Test connection
.\ssh-tunnel-vibeproxy.ps1
# (Keep window open)

# In new window:
curl http://localhost:8317/health
```

### Daily Usage
```powershell
# 1. Start SSH tunnel (one-time per session)
.\ssh-tunnel-vibeproxy.ps1
# Keep window open in background

# 2. Use Factory Droid normally
droid
/model
# Select VibeProxy model
# Chat as normal!
```

---

## 💡 Pro Tips

1. **SSH Key Authentication** (avoid password prompts):
   ```powershell
   # On Windows: Generate SSH key if you don't have one
   ssh-keygen -t ed25519

   # Copy to Mac (enter Mac password once)
   type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh yourname@192.168.1.100 "cat >> ~/.ssh/authorized_keys"

   # Now tunnel connects without password!
   ```

2. **Auto-start Tunnel** (Windows startup):
   - Create shortcut to `ssh-tunnel-vibeproxy.ps1`
   - Place in `shell:startup` folder
   - Tunnel starts when Windows boots

3. **Monitor VibeProxy Usage** (on Mac):
   ```bash
   # Watch logs in real-time
   tail -f ~/Library/Logs/VibeProxy/vibeproxy.log
   ```

4. **Multiple Models**:
   Add all models you need to Factory config:
   - Claude Sonnet/Opus/Haiku
   - GPT-4/GPT-5.1
   - Gemini (if authenticated)

   Factory Droid shows all in `/model` menu!

---

## 📚 Reference

- **VibeProxy GitHub:** https://github.com/automazeio/vibeproxy
- **Factory CLI Docs:** https://docs.factory.ai/cli
- **Port:** 8317 (VibeProxy local server)
- **Endpoints:**
  - Anthropic: `http://localhost:8317`
  - OpenAI: `http://localhost:8317/v1`

## ❓ Questions?

If setup fails, gather this info:
1. Mac: `~/vibeproxy-status.sh` output
2. Windows: `netstat -ano | findstr :8317` output
3. Factory config: `cat ~/.factory/config.json`
4. Error messages from Factory Droid

Then troubleshoot using the checklist above!
