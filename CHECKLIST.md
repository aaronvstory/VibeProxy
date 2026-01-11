# VibeProxy Setup Checklist

Use this checklist to ensure every step is completed correctly.

---

## 📋 Pre-Setup Requirements

- [ ] **MacBook available?** (Apple Silicon M1+ required)
- [ ] **MacBook on macOS 13+?** (Ventura or later)
- [ ] **Windows PC available?**
- [ ] **Both on same network?** (or can reach via VPN)
- [ ] **Factory Droid installed on Windows?**
- [ ] **Active subscriptions?** (Claude Code and/or ChatGPT Plus/Pro)

---

## 🍎 MacBook Setup

### Step 1: Install VibeProxy
- [ ] Download from https://github.com/automazeio/vibeproxy/releases
- [ ] Extract `VibeProxy.zip`
- [ ] Move `VibeProxy.app` to `/Applications/`
- [ ] Launch app (menu bar icon appears)
- [ ] Server auto-starts (check Settings → Running)

### Step 2: Authenticate Providers
- [ ] Click menu bar icon → "Open Settings"
- [ ] Connect **Claude Code** (if you have subscription)
  - [ ] Click "Connect"
  - [ ] Browser opens OAuth flow
  - [ ] Complete authentication
  - [ ] Status shows "Connected ✅"
- [ ] Connect **Codex** (ChatGPT/GPT models)
  - [ ] Click "Connect"
  - [ ] Browser opens OAuth flow
  - [ ] Complete authentication
  - [ ] Status shows "Connected ✅"
- [ ] (Optional) Connect Gemini, Qwen, Antigravity if needed

### Step 3: Enable SSH
- [ ] Method A (GUI):
  - [ ] System Settings → General → Sharing
  - [ ] Enable "Remote Login"
  - [ ] Note connection string (e.g., `ssh yourname@192.168.1.100`)
- [ ] Method B (Terminal):
  - [ ] Run: `sudo systemsetup -setremotelogin on`
  - [ ] Verify: `systemsetup -getremotelogin`

### Step 4: Get IP Address
- [ ] Run: `ipconfig getifaddr en0`
- [ ] Note IP (e.g., `192.168.1.100`)
- [ ] Verify with: `ping <IP>` from Windows

### Step 5: Test VibeProxy Locally
- [ ] Run: `curl http://localhost:8317/health`
- [ ] Should return success (200 OK or similar)
- [ ] (Optional) Copy `mac-vibeproxy-status.sh` to Mac home directory
- [ ] (Optional) Run: `chmod +x ~/mac-vibeproxy-status.sh && ~/mac-vibeproxy-status.sh`

---

## 🪟 Windows Setup

### Step 1: Prepare Scripts
- [ ] Navigate to `F:\claude\VibeProxy\`
- [ ] Verify files exist:
  - [ ] `ssh-tunnel-vibeproxy.ps1`
  - [ ] `test-connection.ps1`
  - [ ] `factory-config-example.json`

### Step 2: Configure SSH Tunnel Script
- [ ] Open `ssh-tunnel-vibeproxy.ps1` in editor
- [ ] Change `$MacUser = "yourname"` to your actual Mac username
- [ ] Change `$MacIP = "192.168.1.100"` to your Mac's actual IP
- [ ] Save file

### Step 3: Test SSH Connection
- [ ] Run: `ssh yourname@<mac-ip>` (use your values)
- [ ] Should connect successfully
- [ ] Type `exit` to disconnect
- [ ] If password required every time → Set up SSH key (see Pro Tips)

### Step 4: Start SSH Tunnel
- [ ] Open PowerShell in `F:\claude\VibeProxy\`
- [ ] Run: `.\ssh-tunnel-vibeproxy.ps1`
- [ ] Should show: "Connecting..." and stay connected
- [ ] Keep this window open in background
- [ ] If it fails immediately → Check Mac IP, username, SSH enabled

### Step 5: Test Tunnel
- [ ] Open NEW PowerShell window
- [ ] Navigate to `F:\claude\VibeProxy\`
- [ ] Run: `.\test-connection.ps1`
- [ ] Should show: `3/3 tests passed`
- [ ] If any fail → Follow error messages to fix

### Step 6: Configure Factory Droid
- [ ] Open `factory-config-example.json`
- [ ] Copy entire contents
- [ ] Paste into: `C:\Users\YourName\.factory\config.json`
  - [ ] Or Git Bash: `~/.factory/config.json`
  - [ ] Create directory if doesn't exist: `mkdir -p ~/.factory`
- [ ] Remove models you don't need (optional)
- [ ] Save file

### Step 7: Test Factory Droid
- [ ] Open PowerShell or Git Bash
- [ ] Run: `droid`
- [ ] Run: `/model`
- [ ] Verify VibeProxy models appear in list
- [ ] Select a model (e.g., "Claude Sonnet 4.5 (VibeProxy)")
- [ ] Send test message: `Hello! Can you confirm you're working?`
- [ ] Should receive response → SUCCESS! 🎉

---

## 🔧 Optional: Improvements

### SSH Key Setup (Skip Password Prompts)
- [ ] On Windows: `ssh-keygen -t ed25519`
- [ ] Press Enter 3 times (accept defaults)
- [ ] Copy key to Mac:
  ```powershell
  type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh yourname@<mac-ip> "cat >> ~/.ssh/authorized_keys"
  ```
- [ ] Enter Mac password one last time
- [ ] Test: `ssh yourname@<mac-ip>` (should NOT ask for password)
- [ ] Now tunnel connects without password!

### Auto-Start Tunnel on Windows Boot
- [ ] Right-click `ssh-tunnel-vibeproxy.ps1`
- [ ] Create shortcut
- [ ] Press `Win+R` → Type `shell:startup` → Enter
- [ ] Move shortcut to startup folder
- [ ] Test: Reboot Windows → Tunnel auto-starts

### Mac Status Script Setup
- [ ] Copy `mac-vibeproxy-status.sh` to Mac (via USB, network, etc.)
- [ ] On Mac: `chmod +x ~/mac-vibeproxy-status.sh`
- [ ] Test: `~/mac-vibeproxy-status.sh`
- [ ] Should show: `5/5 tests passed`
- [ ] Use for debugging when Windows can't connect

---

## 🎯 Daily Usage Checklist

### Every Time You Want to Use Factory Droid:
- [ ] **On Mac:** Ensure VibeProxy is running (check menu bar icon)
- [ ] **On Windows:** Start SSH tunnel
  ```powershell
  cd F:\claude\VibeProxy
  .\ssh-tunnel-vibeproxy.ps1
  ```
- [ ] Keep tunnel window open in background
- [ ] Use Factory Droid normally:
  ```bash
  droid
  /model
  # Select VibeProxy model
  # Chat!
  ```

---

## 🐛 Troubleshooting Checklist

### Windows Can't Connect (Connection Refused)
- [ ] SSH tunnel running? (Check window is still open)
- [ ] Run: `Get-Process ssh | Where-Object {$_.CommandLine -like "*8317*"}`
- [ ] If no process → Restart tunnel: `.\ssh-tunnel-vibeproxy.ps1`
- [ ] Run test: `.\test-connection.ps1`

### Factory Droid Shows "Unauthorized"
- [ ] Mac VibeProxy providers authenticated?
- [ ] Check Mac menu bar → Settings → Providers show "Connected ✅"
- [ ] If "Not Connected" → Disconnect and reconnect provider
- [ ] Restart VibeProxy app on Mac
- [ ] Restart SSH tunnel on Windows

### SSH Tunnel Fails to Connect
- [ ] Mac IP correct in `ssh-tunnel-vibeproxy.ps1`?
- [ ] Test: `ping <mac-ip>` from Windows
- [ ] Mac SSH enabled? On Mac: `systemsetup -getremotelogin`
- [ ] Mac firewall blocking? Try: `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate`
- [ ] Can manually SSH? Test: `ssh yourname@<mac-ip>`

### VibeProxy Not Working on Mac
- [ ] App running? Check menu bar icon
- [ ] If not → Launch: `/Applications/VibeProxy.app`
- [ ] Server running? Menu bar → Settings → Should say "Running"
- [ ] If "Stopped" → Click to start
- [ ] Port listening? `lsof -i :8317`
- [ ] Run Mac status: `~/mac-vibeproxy-status.sh`

---

## ✅ Success Criteria

You've successfully set up VibeProxy when:

- ✅ Mac shows VibeProxy menu bar icon with "Running" status
- ✅ Mac providers show "Connected ✅" in Settings
- ✅ Windows SSH tunnel window stays connected (not failing/reconnecting)
- ✅ `.\test-connection.ps1` shows `3/3 tests passed`
- ✅ Factory Droid `/model` shows VibeProxy models
- ✅ Factory Droid sends messages and receives responses via VibeProxy models
- ✅ No error messages or connection issues

---

## 📊 Verification Commands

Run these to verify setup:

**On Mac:**
```bash
# All should succeed
pgrep -x "VibeProxy"              # App running
lsof -i :8317 | grep LISTEN       # Port listening
curl http://localhost:8317/health # Health check
systemsetup -getremotelogin       # SSH enabled
ipconfig getifaddr en0            # Get IP
```

**On Windows:**
```powershell
# All should succeed
Get-Process ssh | Where-Object {$_.CommandLine -like "*8317*"}  # Tunnel running
Test-NetConnection localhost -Port 8317                          # Port listening
curl http://localhost:8317/health                                # Health check
cat ~/.factory/config.json | grep vibeproxy -i                   # Config exists
```

---

**Everything checked off?** You're ready to use VibeProxy! 🚀

**Still issues?** → See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed troubleshooting.
