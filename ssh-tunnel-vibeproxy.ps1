<#
.SYNOPSIS
    Auto-reconnecting SSH tunnel for VibeProxy with key-based authentication

.DESCRIPTION
    Creates an SSH tunnel from Windows to MacBook running VibeProxy.
    Automatically reconnects if connection drops. Uses SSH key authentication.

.PARAMETER MacUser
    Your username on the MacBook (default: from config or danielba)

.PARAMETER MacIP
    Your MacBook's local IP address (default: from config or 192.168.50.70)

.PARAMETER KeyPath
    Path to SSH private key (default: ~/.ssh/id_ed25519 or ~/.ssh/id_rsa)

.NOTES
    Port: Windows localhost:8317 → Mac localhost:8317
    Keep this window open while using Factory Droid!

    SSH Key Setup (one-time):
      1. Generate key: ssh-keygen -t ed25519 -f ~/.ssh/vibeproxy_key
      2. Copy to Mac:  ssh-copy-id -i ~/.ssh/vibeproxy_key.pub user@mac-ip
      3. Set KeyPath in vibeproxy-config.json or pass -KeyPath parameter
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$MacUser,

    [Parameter(Mandatory=$false)]
    [string]$MacIP,

    [Parameter(Mandatory=$false)]
    [int]$LocalPort,

    [Parameter(Mandatory=$false)]
    [int]$RemotePort,

    [Parameter(Mandatory=$false)]
    [string]$KeyPath,

    [Parameter(Mandatory=$false)]
    [switch]$NoAutoReconnect,

    [Parameter(Mandatory=$false)]
    [switch]$Monitor,

    [Parameter(Mandatory=$false)]
    [switch]$KillPort
)

# Configuration
$ConfigPath = Join-Path $PSScriptRoot "vibeproxy-config.json"
$DefaultConfig = [pscustomobject]@{
    MacUser = "danielba"
    MacIP = "192.168.50.70"
    LocalPort = 8317
    RemotePort = 8317
    SSHKeyPath = ""
}

# Load or create config
function Get-Config {
    $config = [pscustomobject]@{
        MacUser = $DefaultConfig.MacUser
        MacIP = $DefaultConfig.MacIP
        LocalPort = $DefaultConfig.LocalPort
        RemotePort = $DefaultConfig.RemotePort
        SSHKeyPath = $DefaultConfig.SSHKeyPath
    }
    if (Test-Path $ConfigPath) {
        try {
            $fileConfig = Get-Content $ConfigPath -Raw | ConvertFrom-Json
            if ($fileConfig) {
                foreach ($prop in $fileConfig.PSObject.Properties) {
                    # Skip legacy password field
                    if ($prop.Name -eq "SSHPassword") { continue }
                    $config | Add-Member -NotePropertyName $prop.Name -NotePropertyValue $prop.Value -Force
                }
            }
        } catch {
            # Ignore parse errors and use defaults.
        }
    }
    return $config
}

function Save-Config {
    param($Config)
    # Remove any legacy password field before saving
    $cleanConfig = $Config | Select-Object -Property MacUser, MacIP, LocalPort, RemotePort, SSHKeyPath
    $cleanConfig | ConvertTo-Json | Set-Content $ConfigPath -Encoding UTF8
}

# Find SSH key
function Find-SSHKey {
    param([string]$ExplicitPath)

    # 1. Use explicit path if provided
    if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
        if (Test-Path $ExplicitPath) {
            return $ExplicitPath
        }
        Write-Host "⚠️  Specified key not found: $ExplicitPath" -ForegroundColor Yellow
    }

    # 2. Check common key locations
    $sshDir = Join-Path $env:USERPROFILE ".ssh"
    $keyNames = @(
        "vibeproxy_key",     # Project-specific key (preferred)
        "id_ed25519",        # Modern default
        "id_rsa"             # Legacy default
    )

    foreach ($keyName in $keyNames) {
        $keyPath = Join-Path $sshDir $keyName
        if (Test-Path $keyPath) {
            return $keyPath
        }
    }

    return $null
}

# Load config and apply defaults
$config = Get-Config
if ([string]::IsNullOrWhiteSpace($MacUser)) { $MacUser = $config.MacUser }
if ([string]::IsNullOrWhiteSpace($MacIP)) { $MacIP = $config.MacIP }
if (-not $LocalPort -or $LocalPort -le 0) { $LocalPort = [int]$config.LocalPort }
if (-not $RemotePort -or $RemotePort -le 0) { $RemotePort = [int]$config.RemotePort }

# Find SSH key
$resolvedKeyPath = Find-SSHKey -ExplicitPath $(if ([string]::IsNullOrWhiteSpace($KeyPath)) { $config.SSHKeyPath } else { $KeyPath })

if ([string]::IsNullOrWhiteSpace($resolvedKeyPath)) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "                   SSH KEY REQUIRED - Setup Instructions                        " -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host ""
    Write-Host "  No SSH key found. Key-based authentication is required for security." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Quick Setup (run in PowerShell):" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "    # 1. Generate a new key (press Enter for defaults):" -ForegroundColor White
    Write-Host '    ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\vibeproxy_key"' -ForegroundColor Gray
    Write-Host ""
    Write-Host "    # 2. Copy public key to your Mac:" -ForegroundColor White
    Write-Host "    type `$env:USERPROFILE\.ssh\vibeproxy_key.pub | ssh $MacUser@$MacIP `"cat >> ~/.ssh/authorized_keys`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "    # 3. Re-run this script" -ForegroundColor White
    Write-Host ""
    Write-Host "  Or specify an existing key:" -ForegroundColor Cyan
    Write-Host "    .\ssh-tunnel-vibeproxy.ps1 -KeyPath `"C:\path\to\your\key`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Red
    exit 1
}

# Persist config updates if needed
$updated = $false
if ($config.MacUser -ne $MacUser) { $config.MacUser = $MacUser; $updated = $true }
if ($config.MacIP -ne $MacIP) { $config.MacIP = $MacIP; $updated = $true }
if ($config.LocalPort -ne $LocalPort) { $config.LocalPort = $LocalPort; $updated = $true }
if ($config.RemotePort -ne $RemotePort) { $config.RemotePort = $RemotePort; $updated = $true }
if ($config.SSHKeyPath -ne $resolvedKeyPath) { $config.SSHKeyPath = $resolvedKeyPath; $updated = $true }

if ($updated -or -not (Test-Path $ConfigPath)) {
    Save-Config $config
}

# Banner
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                   VibeProxy SSH Tunnel - Auto-Reconnect                       " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  🔌 Configuration:" -ForegroundColor White
Write-Host "     Mac Target      : $MacUser@$MacIP" -ForegroundColor Gray
Write-Host "     Local Port      : $LocalPort" -ForegroundColor Gray
Write-Host "     Remote Port     : $RemotePort" -ForegroundColor Gray
Write-Host "     Auto-Reconnect  : $(-not $NoAutoReconnect)" -ForegroundColor Gray
Write-Host "     SSH Key         : $resolvedKeyPath" -ForegroundColor Gray
Write-Host ""
Write-Host "  💡 Usage Tips:" -ForegroundColor Yellow
Write-Host "     • Keep this window OPEN while using VibeProxy, Factory Droid, or Agent Zero" -ForegroundColor Gray
Write-Host "     • Press Ctrl+C to disconnect" -ForegroundColor Gray
Write-Host "     • Test connection: curl http://localhost:8317/health" -ForegroundColor Gray
Write-Host ""

# Check if SSH is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ERROR: SSH not found!" -ForegroundColor Red
    Write-Host "   Install OpenSSH client (Windows 10/11 includes it)" -ForegroundColor Yellow
    exit 1
}

# Check if port is already in use
$PortInUse = Get-NetTCPConnection -LocalPort $LocalPort -ErrorAction SilentlyContinue
if ($PortInUse) {
    $processIds = $PortInUse.OwningProcess | Sort-Object -Unique | Where-Object { $_ -ne 0 }
    Write-Host "⚠️  WARNING: Port $LocalPort is already in use!" -ForegroundColor Yellow
    Write-Host "   Process IDs: $($processIds -join ', ')" -ForegroundColor Gray
    Write-Host ""

    if ($KillPort) {
        # Auto-kill without prompting
        foreach ($procId in $processIds) {
            try {
                Stop-Process -Id $procId -Force -ErrorAction Stop
                Write-Host "✅ Killed process $procId" -ForegroundColor Green
            } catch {
                Write-Host "⚠️  Could not kill process $procId (may require admin): $_" -ForegroundColor Yellow
            }
        }
        Start-Sleep -Seconds 2
    } else {
        $Response = Read-Host "Kill existing process and continue? (y/n)"
        if ($Response -eq 'y') {
            foreach ($procId in $processIds) {
                try {
                    Stop-Process -Id $procId -Force -ErrorAction Stop
                    Write-Host "✅ Killed process $procId" -ForegroundColor Green
                } catch {
                    Write-Host "⚠️  Could not kill process $procId (may require admin): $_" -ForegroundColor Yellow
                }
            }
            Start-Sleep -Seconds 2
        } else {
            Write-Host "❌ Exiting..." -ForegroundColor Red
            exit 1
        }
    }
}

# Function to test if port is accessible
function Test-TunnelPort {
    param([int]$Port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("localhost", $Port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

# Connection attempt counter
$AttemptCount = 0
$LastConnectTime = Get-Date

# Main connection loop
while ($true) {
    $AttemptCount++
    $Timestamp = Get-Date -Format 'HH:mm:ss'

    try {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "Attempt #$AttemptCount - Connecting..." -ForegroundColor Green

        # Build SSH arguments (key-based auth only)
        $sshArgs = @(
            "-i", $resolvedKeyPath,
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "BatchMode=yes",
            "-L", "${LocalPort}:localhost:${RemotePort}",
            "${MacUser}@${MacIP}", "-N"
        )

        if ($Monitor) {
            # Monitor mode: Run SSH as background process and show status updates
            $sshProcess = $null

            try {
                $sshProcess = Start-Process -FilePath "ssh" -ArgumentList $sshArgs -PassThru -WindowStyle Hidden

                # Wait for connection to establish
                Start-Sleep -Seconds 2

                if ($sshProcess.HasExited) {
                    throw "SSH process exited immediately. Check your SSH key and Mac settings."
                }

                Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
                Write-Host "✅ Connected! Starting live monitor..." -ForegroundColor Green
                Write-Host ""
                Write-Host "  ════════════════════════════════════════════════════════════════" -ForegroundColor DarkCyan
                Write-Host "    LIVE ACTIVITY MONITOR" -ForegroundColor Cyan
                Write-Host "    Latency checks every 5s | Press Ctrl+C to stop" -ForegroundColor DarkGray
                Write-Host "  ════════════════════════════════════════════════════════════════" -ForegroundColor DarkCyan
                Write-Host ""

                # Monitor loop - check latency every 5 seconds
                $checkCount = 0
                $totalLatency = 0

                # Do initial check immediately
                $Timestamp = Get-Date -Format 'HH:mm:ss'
                Write-Host ""
                try {
                    $sw = [System.Diagnostics.Stopwatch]::StartNew()
                    $response = Invoke-RestMethod -Uri "http://localhost:$LocalPort/v1/models" -Method GET -TimeoutSec 10
                    $sw.Stop()
                    $latencyMs = $sw.ElapsedMilliseconds
                    $checkCount++
                    $totalLatency += $latencyMs
                    $modelCount = $response.data.Count
                    Write-Host "  🟢 [$Timestamp] Connected! $modelCount models available (${latencyMs}ms)" -ForegroundColor Green
                } catch {
                    Write-Host "  🔴 [$Timestamp] Initial check failed - tunnel may still be connecting..." -ForegroundColor Yellow
                }
                Write-Host ""

                while (-not $sshProcess.HasExited) {
                    Start-Sleep -Seconds 5

                    # Show latency check
                    $Timestamp = Get-Date -Format 'HH:mm:ss'
                    $checkCount++

                    try {
                        $sw = [System.Diagnostics.Stopwatch]::StartNew()
                        $response = Invoke-RestMethod -Uri "http://localhost:$LocalPort/v1/models" -Method GET -TimeoutSec 10
                        $sw.Stop()
                        $latencyMs = $sw.ElapsedMilliseconds
                        $totalLatency += $latencyMs
                        $avgLatency = [math]::Round($totalLatency / $checkCount)
                        $modelCount = $response.data.Count

                        $latencyColor = if ($latencyMs -lt 100) { "Green" } elseif ($latencyMs -lt 300) { "Yellow" } else { "Red" }
                        $statusIcon = if ($latencyMs -lt 100) { "🟢" } elseif ($latencyMs -lt 300) { "🟡" } else { "🔴" }

                        Write-Host "  $statusIcon " -NoNewline -ForegroundColor $latencyColor
                        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
                        Write-Host "Latency: " -NoNewline -ForegroundColor White
                        Write-Host "${latencyMs}ms" -NoNewline -ForegroundColor $latencyColor
                        Write-Host " (avg: ${avgLatency}ms) | " -NoNewline -ForegroundColor DarkGray
                        Write-Host "$modelCount models" -ForegroundColor Cyan
                    } catch {
                        Write-Host "  🔴 [$Timestamp] Request failed: $($_.Exception.Message)" -ForegroundColor Red
                    }
                }

                # Process exited
                Write-Host ""

            } finally {
                # Cleanup: ensure SSH process is terminated on script exit or Ctrl+C
                if ($null -ne $sshProcess -and -not $sshProcess.HasExited) {
                    Write-Host "  🧹 Cleaning up SSH process (PID: $($sshProcess.Id))..." -ForegroundColor Yellow
                    try {
                        $sshProcess.Kill()
                        $sshProcess.WaitForExit(3000)
                    } catch {
                        # Process may have already exited
                    }
                }
            }

        } else {
            # Non-monitor mode: Run SSH in foreground (blocking)
            & ssh @sshArgs
        }

    } catch {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "❌ Connection error: $_" -ForegroundColor Red
    }

    # Connection ended (either error or user killed it)
    $CurrentTime = Get-Date
    $Duration = ($CurrentTime - $LastConnectTime).TotalSeconds

    if ($Duration -lt 5) {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "⚠️  Connection failed immediately!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  ───────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
        Write-Host "  Possible issues:" -ForegroundColor Yellow
        Write-Host "    1. Mac IP wrong or unreachable: $MacIP" -ForegroundColor Gray
        Write-Host "    2. SSH not enabled on Mac (System Settings → Sharing → Remote Login)" -ForegroundColor Gray
        Write-Host "    3. SSH key not authorized on Mac (~/.ssh/authorized_keys)" -ForegroundColor Gray
        Write-Host "    4. Wrong username: $MacUser" -ForegroundColor Gray
        Write-Host "    5. SSH key passphrase required (use ssh-agent)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Test manually:" -ForegroundColor Cyan
        Write-Host "    ssh -i `"$resolvedKeyPath`" $MacUser@$MacIP" -ForegroundColor Gray
        Write-Host "  ───────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
        Write-Host ""
    } else {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "🔌 Connection lost after $([math]::Round($Duration))s" -ForegroundColor Yellow
    }

    # Exit if auto-reconnect disabled
    if ($NoAutoReconnect) {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "Auto-reconnect disabled. Exiting." -ForegroundColor Red
        exit 0
    }

    # Wait before reconnecting
    Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
    Write-Host "🔄 Reconnecting in 5 seconds... (Ctrl+C to cancel)" -ForegroundColor Cyan
    Start-Sleep -Seconds 5

    $LastConnectTime = Get-Date
}
