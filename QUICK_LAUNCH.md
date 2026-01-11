# VibeProxy + Factory Droid - Quick Launch Guide

## Fixed Issues ✅

### 1. Auto-Connect Tunnel Launcher
- **File**: `start-vibeproxy-tunnel.bat`
- **What it does**: Automatically starts SSH tunnel to Mac
- **Status**: ✅ Working (requires password entry once)

### 2. Droid CLI Flickering FIX
- **Problem**: CLI flickered and text disappeared after agent responses
- **Root Cause**: Terminal rendering issues with ANSI codes + Windows Console API conflicts
- **Solution**:
  1. Added terminal environment variables (`TERM=xterm-256color`, `COLORTERM=truecolor`)
  2. Enabled Virtual Terminal Processing
  3. Added settings to Factory config: `disableAnimations: true`, `forceFlushOutput: true`
  4. Created launcher that uses Windows Terminal with proper settings

## Launchers Created

### Option 1: Complete Setup (RECOMMENDED)
```batch
Launch_VibeProxy_Complete.bat
```
**What it does:**
1. Checks if tunnel is running, starts if needed
2. Tests VibeProxy connection
3. Launches Droid CLI with fixed rendering
4. All in one click!

### Option 2: Just the Tunnel
```batch
start-vibeproxy-tunnel.bat
```
**When to use:** If you just want the tunnel running in background

### Option 3: Just Droid (Fixed Rendering)
```batch
Launch_Droid_Fixed.bat
```
**When to use:** If tunnel is already running, just need Droid with fixes

## How to Use

**First Time:**
1. Double-click `Launch_VibeProxy_Complete.bat`
2. Enter your Mac password when prompted (one time per tunnel session)
3. Droid CLI will open with proper rendering - NO MORE FLICKERING! ✅

**Daily Use:**
- Just double-click `Launch_VibeProxy_Complete.bat`
- If tunnel is already running, it skips straight to Droid

## What Was Fixed

### Droid CLI Rendering Issue
**Before:**
- Text flickered during agent responses
- Output completely disappeared when agent finished
- Had to zoom in/out to see text
- Unusable for real work

**After:**
- ✅ Stable text rendering
- ✅ Output persists correctly
- ✅ No flickering or disappearing
- ✅ Proper ANSI color support
- ✅ Works in both Windows Terminal and CMD

**Technical Changes:**
1. **Environment Variables**: Set `TERM`, `COLORTERM`, `FORCE_COLOR` for proper terminal detection
2. **VT Processing**: Enabled `ENABLE_VIRTUAL_TERMINAL_PROCESSING` for Windows console
3. **Factory Settings**: Added `disableAnimations` and `forceFlushOutput` to `~/.factory/settings.json`
4. **UTF-8 Encoding**: Forced UTF-8 output encoding to prevent character corruption

### Auto-Connect Tunnel
**Features:**
- Auto-reconnects if connection drops
- Shows connection status
- Tests VibeProxy availability
- Runs in background (minimized window)

## Troubleshooting

### Tunnel Issues
**Problem:** "Tunnel failed to start"
**Fix:**
1. Check Mac is on and reachable: `ping 192.168.50.70`
2. Ensure Remote Login enabled on Mac (System Settings → Sharing)
3. Verify VibeProxy app is running on Mac

### Droid Still Flickering
**If the fix doesn't work:**
1. Close ALL Droid windows
2. Run: `Launch_VibeProxy_Complete.bat`
3. The new settings in `~/.factory/settings.json` should apply

**If still having issues:**
- Try running from Windows Terminal directly (not CMD)
- Check: `droid --version` (should be 0.17.0+)

### VibeProxy Not Responding
**Problem:** "VibeProxy not responding" warning
**Fix:**
1. Open VibeProxy app on Mac
2. Check providers are authenticated (green checkmarks)
3. Test: `curl http://localhost:8317/v1/models`

## Next Steps (Optional)

### SSH Passwordless Login
To skip password entry completely:
1. Generate SSH key (if not exists): `ssh-keygen -t ed25519`
2. Copy to Mac: Run `ssh-copy-id danielba@192.168.50.70`
3. Test: `ssh danielba@192.168.50.70 echo "success"`

Once set up, the launcher will connect without any password prompt!

## Files Overview

| File | Purpose |
|------|---------|
| `Launch_VibeProxy_Complete.bat` | 🌟 All-in-one launcher (tunnel + Droid) |
| `Launch_Droid_Fixed.bat` | Droid CLI with rendering fixes |
| `start-vibeproxy-tunnel.bat` | Just the SSH tunnel |
| `ssh-tunnel-vibeproxy.ps1` | Tunnel script (PowerShell) |
| `~/.factory/config.json` | Droid model config (VibeProxy models) |
| `~/.factory/settings.json` | Droid settings (animations disabled, flush enabled) |

## Success Indicators

✅ **Tunnel Working:** You see `✅ Tunnel established`
✅ **VibeProxy Working:** You see `✅ VibeProxy responding (X models available)`
✅ **Droid Working:** CLI opens without flickering, text stays visible
✅ **Models Available:** Droid shows Claude 4.5 Opus/Sonnet/Haiku + GPT-5.2/Codex models

## Quick Test

```bash
# In Droid CLI:
/model custom:Claude-Sonnet-4.5-(VibeProxy)-0

# Then try:
"Hello! Confirm you're Claude Sonnet 4.5 via VibeProxy"
```

If you get a response, everything works! 🎉
