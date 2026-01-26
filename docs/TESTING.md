# VibeProxy Tunnel Fixes - Testing Guide

## What Was Fixed

### Critical Bug Found

The initial fix using `-hostkey acceptnew` was **INVALID** - PuTTY does not support this OpenSSH syntax!

### Correct Fix Applied

Changed to use EXACT host key fingerprint:

```
-hostkey "SHA256:5XgC3h/+waae885A5/IORHon1HPf3QLQXbF84V+mj0Y"
```

This is your Mac's specific SSH host key at `192.168.50.71`.

### Files Modified

1. `vibeproxy_manager/tunnel.py` (lines 274, 293)
2. `ssh-tunnel-vibeproxy.ps1` (line 203)

## Quick Test

```powershell
# Run the comprehensive test suite
powershell -ExecutionPolicy Bypass -File test-tunnel-fixes.ps1
```

This will test:

- ✅ PuTTY installation
- ✅ Config file validity
- ✅ Host key syntax
- ✅ Actual tunnel connection
- ✅ Python code syntax
- ✅ PowerShell script syntax

## Manual Testing

### Test 1: Standalone Tunnel Script

```powershell
python ssh-tunnel-intelligent.py
```

**Expected Output:**

```
✅ SUCCESS! Tunnel started on port 8317
🔗 Testing connection to VibeProxy...
✅ Connection successful! Found X models
```

**If it fails:**

- Check Mac IP: `ssh danielba@192.168.50.71` (should connect)
- Verify VibeProxy running on Mac: `curl http://localhost:8317/v1/models`
- Check firewall settings

### Test 2: Python TUI

```powershell
python -m vibeproxy_manager
# Or:
python run.py
```

**Steps:**

1. Select `[1] Start SSH Tunnel`
2. New PowerShell window should open
3. Tunnel should connect without errors
4. Select `[3] Test VibeProxy`
5. Should show: "Connected (X models available)"

### Test 3: PowerShell CLI (Legacy)

```powershell
powershell -ExecutionPolicy Bypass -File "VibeProxy-Manager.ps1"
```

**Steps:**

1. Select `[1] Start SSH Tunnel`
2. Should show: "✅ Tunnel started successfully"
3. Select `[3] Test VibeProxy`
4. Should show: "✅ Connected (X models available)"

### Test 4: Zombie State Detection

```powershell
# 1. Start tunnel via TUI
python -m vibeproxy_manager
# Select: [1] Start SSH Tunnel

# 2. Kill the PowerShell window manually (X button)

# 3. Wait 15 seconds for status bar refresh

# 4. Try starting tunnel again
# Select: [1] Start SSH Tunnel

# Expected: Auto-detects zombie state and force restarts
```

### Test 5: Health Check Caching

```powershell
# Start TUI with tunnel running
python -m vibeproxy_manager

# Watch status bar (should update every 5 seconds)
# Every 10 seconds should run HTTP health check
# Status should show:
#   SSH: ✅ Connected (port 8317)
#   A0: 🟢 Running
#   Config: <model-name>
```

## Troubleshooting

### Error: "host key is not cached"

**Cause:** Fingerprint doesn't match your Mac
**Fix:** Get correct fingerprint from first connection attempt and update code

### Error: "Authentication failed"

**Cause:** Password incorrect or missing from config
**Fix:**

```powershell
# Delete password from config to re-enter
$config = Get-Content vibeproxy-config.json | ConvertFrom-Json
$config.SSHPassword = ""
$config | ConvertTo-Json | Set-Content vibeproxy-config.json

# Run tunnel again - it will prompt for password
```

### Error: "Connection refused"

**Possible causes:**

1. Mac IP changed (use `ipconfig getifaddr en0` on Mac to verify)
2. VibeProxy not running on Mac
3. Mac firewall blocking port 22
4. Network connectivity issue

**Fix:** Verify each item above

### Port 8317 already in use

**Cause:** Previous tunnel didn't shut down
**Fix:**

```powershell
# Find and kill process on port 8317
$conn = Get-NetTCPConnection -LocalPort 8317 -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force
}
```

## Expected Test Results

### All Tests Passing:

```
═══════════════════════════════════════════════════════════════
   TEST SUMMARY
═══════════════════════════════════════════════════════════════

PuTTY Installation                PASS
Config File                       PASS
Host Key Syntax                   PASS
Tunnel Connection                 PASS
Python Syntax                     PASS
PowerShell Syntax                 PASS

Total: 6 | PASS: 6 | FAIL: 0 | SKIP: 0

✅ All tests passed!
```

## Next Steps After Testing

### Immediate Actions

1. Run test suite: `test-tunnel-fixes.ps1`
2. Verify tunnel connects successfully
3. Test all three entry points (TUI, CLI, script)

### Future Improvements (Optional)

1. **Add SSHHostKey to config file** for portability
   - Store fingerprint in `vibeproxy-config.json`
   - Allow updating if Mac IP/key changes

2. **Consider SSH key-based auth** (more secure)
   - No password needed
   - No host key prompt issues
   - See: `ssh-keygen` and `ssh-copy-id`

3. **Add config validation on startup**
   - Check Mac reachable before starting tunnel
   - Validate fingerprint matches current Mac

## Success Criteria

✅ Tunnel connects without errors
✅ API health check passes
✅ Status bar shows "Connected"
✅ No zombie states after manual kills
✅ Feature parity between TUI and CLI
✅ All syntax tests pass

## Reporting Issues

If tests fail, collect this information:

1. Full error output from test script
2. Output from `plink -V` (PuTTY version)
3. Output from `ssh danielba@192.168.50.71 "echo test"` (SSH connectivity)
4. Contents of `vibeproxy-config.json` (redact password)
5. Mac IP from `ipconfig getifaddr en0`
