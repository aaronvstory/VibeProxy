<#
.SYNOPSIS
    VibeProxy Manager - Switch A0 configs and manage SSH tunnel

.DESCRIPTION
    All-in-one manager for:
    - Switching Agent Zero between OpenRouter and VibeProxy modes
    - Starting/stopping SSH tunnel to Mac
    - Testing VibeProxy connectivity
    - Auto-restart A0 after config changes

.NOTES
    Requires: SSH tunnel to Mac for VibeProxy mode
    A0 Settings: C:\claude\agent-zero-data\tmp\settings.json
#>

# ═══════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════

$Script:ConfigDir = Join-Path $PSScriptRoot "configs"
$Script:A0SettingsPath = "C:\claude\agent-zero-data\tmp\settings.json"
$Script:ConfigPath = Join-Path $PSScriptRoot "vibeproxy-config.json"
$Script:Config = $null
$Script:MacUser = ""
$Script:MacIP = ""
$Script:TunnelPort = 8317

# Neon theme palette
$Script:Theme = @{
    Border = "Cyan"
    Title = "Magenta"
    Section = "Blue"
    Accent = "Magenta"
    Text = "White"
    Muted = "DarkGray"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Glow = "Cyan"
}

function Write-Rail {
    param(
        [string]$Label = ""
    )

    $line = "───────────────────────────────────────────────────────────────────────"
    if ([string]::IsNullOrWhiteSpace($Label)) {
        Write-Host $line -ForegroundColor $Script:Theme.Border
    } else {
        Write-Host $line -ForegroundColor $Script:Theme.Border
        Write-Host $Label -ForegroundColor $Script:Theme.Title
    }
}

# All available VibeProxy models (from /v1/models endpoint)
$Script:AvailableModels = @{
    # Claude (Anthropic direct)
    "claude-opus-4-5-20251101" = "Claude Opus 4.5 (Latest)"
    "claude-sonnet-4-5-20250929" = "Claude Sonnet 4.5"
    "claude-haiku-4-5-20251001" = "Claude Haiku 4.5"
    "claude-opus-4-1-20250805" = "Claude Opus 4.1"
    "claude-sonnet-4-20250514" = "Claude Sonnet 4"
    "claude-3-7-sonnet-20250219" = "Claude 3.7 Sonnet"
    "claude-3-5-haiku-20241022" = "Claude 3.5 Haiku"
    # Claude (via Copilot)
    "claude-opus-4.5" = "Claude Opus 4.5 (Copilot)"
    "claude-sonnet-4.5" = "Claude Sonnet 4.5 (Copilot)"
    "claude-haiku-4.5" = "Claude Haiku 4.5 (Copilot)"
    # GPT
    "gpt-5.2-codex" = "GPT-5.2 Codex"
    "gpt-5.2" = "GPT-5.2"
    "gpt-5.1-codex-max" = "GPT-5.1 Codex Max (Best)"
    "gpt-5.1-codex" = "GPT-5.1 Codex"
    "gpt-5.1-codex-mini" = "GPT-5.1 Codex Mini"
    "gpt-5.1" = "GPT-5.1"
    "gpt-5-codex" = "GPT-5 Codex"
    "gpt-5-codex-mini" = "GPT-5 Codex Mini"
    "gpt-5" = "GPT-5"
    "gpt-5-mini" = "GPT-5 Mini"
    "gpt-4.1" = "GPT-4.1"
    # Gemini
    "gemini-3-pro-preview" = "Gemini 3 Pro Preview"
    "gemini-3-flash-preview" = "Gemini 3 Flash Preview"
    "gemini-3-pro" = "Gemini 3 Pro"
    "gemini-2.5-pro" = "Gemini 2.5 Pro (1M ctx)"
    "gemini-2.5-flash" = "Gemini 2.5 Flash"
    "gemini-2.5-flash-lite" = "Gemini 2.5 Flash Lite"
    # Other
    "grok-code-fast-1" = "Grok Code Fast"
    "raptor-mini" = "Raptor Mini"
}

# ═══════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════

function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Rail
    Write-Host "VibeProxy Manager for Agent Zero" -ForegroundColor $Script:Theme.Title
    Write-Host "All Models via SSH Tunnel" -ForegroundColor $Script:Theme.Glow
    Write-Rail
    Write-Host ""
}

function Get-VibeProxyConfig {
    $config = [pscustomobject]@{
        MacUser = "danielba"
        MacIP = "192.168.50.70"
        LocalPort = 8317
        RemotePort = 8317
        SSHPassword = ""
    }

    if (Test-Path $Script:ConfigPath) {
        try {
            $fileConfig = Get-Content $Script:ConfigPath -Raw | ConvertFrom-Json
            if ($fileConfig) {
                foreach ($prop in $fileConfig.PSObject.Properties) {
                    $config | Add-Member -NotePropertyName $prop.Name -NotePropertyValue $prop.Value -Force
                }
            }
        } catch {
            # Ignore parse errors and use defaults.
        }
    }

    return [pscustomobject]$config
}

function Get-ConfigValue {
    param(
        $Config,
        [string]$Name,
        $Default
    )

    if ($null -eq $Config) { return $Default }

    if ($Config -is [hashtable] -or $Config -is [System.Collections.Specialized.OrderedDictionary]) {
        if ($Config.Contains($Name) -and -not [string]::IsNullOrWhiteSpace([string]$Config[$Name])) {
            return $Config[$Name]
        }
    } else {
        $prop = $Config.PSObject.Properties[$Name]
        if ($prop -and -not [string]::IsNullOrWhiteSpace([string]$prop.Value)) {
            return $prop.Value
        }
    }

    return $Default
}

function Refresh-VibeProxyConfig {
    $Script:Config = Get-VibeProxyConfig
    $Script:MacUser = Get-ConfigValue $Script:Config "MacUser" "danielba"
    $Script:MacIP = Get-ConfigValue $Script:Config "MacIP" "192.168.50.70"
    $localPort = Get-ConfigValue $Script:Config "LocalPort" 8317
    if (-not $localPort -or [int]$localPort -le 0) { $localPort = 8317 }
    $Script:TunnelPort = [int]$localPort
}

function Get-VibeProxyModels {
    try {
        return Invoke-RestMethod -Uri "http://localhost:$Script:TunnelPort/v1/models" -TimeoutSec 5
    } catch {
        return $null
    }
}

function Get-ConfigOptions {
    $options = @()
    $files = Get-ChildItem $Script:ConfigDir -Filter "a0-*.json" -ErrorAction SilentlyContinue | Sort-Object Name
    foreach ($file in $files) {
        $name = $file.BaseName -replace "^a0-", ""
        $provider = ""
        $model = ""
        $apiBase = ""
        try {
            $cfg = Get-Content $file.FullName -Raw | ConvertFrom-Json
            $provider = $cfg.chat_model_provider
            $model = $cfg.chat_model_name
            $apiBase = $cfg.chat_model_api_base
        } catch {
            # Ignore config parse errors.
        }

        $mode = "Unknown"
        if ($apiBase -like "*host.docker.internal*" -or $apiBase -like "*localhost:8317*") {
            $mode = "VibeProxy"
        } elseif ($provider) {
            $mode = $provider
        }

        $modelLabel = $model
        if ($Script:AvailableModels[$model]) {
            $modelLabel = $Script:AvailableModels[$model]
        }

        $description = if ($modelLabel) { "$($mode): $modelLabel" } else { $mode }

        $options += [pscustomobject]@{
            Name = $name
            Path = $file.FullName
            Provider = $provider
            Model = $model
            Description = $description
        }
    }

    return $options
}

function Get-Favorites {
    $cfg = Get-VibeProxyConfig
    if ($cfg -and $cfg.PSObject.Properties["Favorites"]) {
        $fav = $cfg.Favorites
        if ($null -eq $fav) { return @() }
        if ($fav -is [string]) { return @($fav) }
        return @($fav)
    }
    return @()
}

function Get-DisabledModels {
    $cfg = Get-VibeProxyConfig
    if ($cfg -and $cfg.PSObject.Properties["DisabledModels"]) {
        $list = $cfg.DisabledModels
        if ($null -eq $list) { return @() }
        if ($list -is [string]) { return @($list) }
        return @($list)
    }
    return @()
}

function Save-DisabledModels {
    param([string[]]$DisabledModels)

    $cfg = $null
    if (Test-Path $Script:ConfigPath) {
        try {
            $cfg = Get-Content $Script:ConfigPath -Raw | ConvertFrom-Json
        } catch {
            $cfg = $null
        }
    }

    if (-not $cfg) { $cfg = [pscustomobject]@{} }
    $cfg | Add-Member -NotePropertyName "DisabledModels" -NotePropertyValue $DisabledModels -Force
    $cfg | ConvertTo-Json -Depth 8 | Set-Content $Script:ConfigPath
}

function Get-FactoryConfigPath {
    return (Join-Path $env:USERPROFILE ".factory\\config.json")
}

function Format-ModelDisplayName {
    param([string]$ModelId)

    if ($Script:AvailableModels[$ModelId]) {
        return "$($Script:AvailableModels[$ModelId]) (VibeProxy)"
    }

    $provider = Resolve-ModelProvider ([pscustomobject]@{ id = $ModelId; owned_by = "" })
    if ($provider -and $provider -ne "Other") {
        return "$provider - $ModelId (VibeProxy)"
    }

    return "$ModelId (VibeProxy)"
}

function Update-FactoryConfigModel {
    param([string]$ModelId)

    $configPath = Get-FactoryConfigPath
    $config = $null
    if (Test-Path $configPath) {
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
        } catch {
            $config = $null
        }
    }
    if (-not $config) {
        $config = [pscustomobject]@{
            custom_models = @()
        }
    }
    if (-not $config.PSObject.Properties["custom_models"]) {
        $config | Add-Member -NotePropertyName "custom_models" -NotePropertyValue @() -Force
    }

    $baseUrl = "http://localhost:$Script:TunnelPort/v1"
    $provider = "openai"
    $displayName = Format-ModelDisplayName $ModelId

    $updatedList = @()
    $existing = $null

    foreach ($item in $config.custom_models) {
        if ($item.model -eq $ModelId) {
            $existing = $item
        } else {
            $updatedList += $item
        }
    }

    if (-not $existing) {
        $existing = [pscustomobject]@{
            model_display_name = $displayName
            model = $ModelId
            base_url = $baseUrl
            api_key = "dummy-not-used"
            provider = $provider
        }
    } else {
        $existing.model_display_name = $displayName
        $existing.base_url = $baseUrl
        $existing.provider = $provider
    }

    # Put selected model first for quick access in other CLIs (e.g., droid-cli)
    $config.custom_models = @($existing) + $updatedList
    $config | ConvertTo-Json -Depth 8 | Set-Content $configPath
}

function Save-Favorites {
    param([string[]]$Favorites)

    $cfg = $null
    if (Test-Path $Script:ConfigPath) {
        try {
            $cfg = Get-Content $Script:ConfigPath -Raw | ConvertFrom-Json
        } catch {
            $cfg = $null
        }
    }

    if (-not $cfg) {
        $cfg = [pscustomobject]@{}
    }

    $cfg | Add-Member -NotePropertyName "Favorites" -NotePropertyValue $Favorites -Force
    $cfg | ConvertTo-Json -Depth 8 | Set-Content $Script:ConfigPath
    Refresh-VibeProxyConfig
}

function Get-MaxTokens {
    $cfg = Get-VibeProxyConfig
    if ($cfg -and $cfg.PSObject.Properties["MaxTokens"]) {
        return [int]$cfg.MaxTokens
    }
    return 500  # Default
}

function Set-MaxTokens {
    param([int]$Tokens)

    $cfg = $null
    if (Test-Path $Script:ConfigPath) {
        try {
            $cfg = Get-Content $Script:ConfigPath -Raw | ConvertFrom-Json
        } catch {
            $cfg = $null
        }
    }

    if (-not $cfg) { $cfg = [pscustomobject]@{} }
    $cfg | Add-Member -NotePropertyName "MaxTokens" -NotePropertyValue $Tokens -Force
    $cfg | ConvertTo-Json -Depth 8 | Set-Content $Script:ConfigPath
    Refresh-VibeProxyConfig
}

function Get-BaseVibeProxyConfigPath {
    $preferred = @(
        "a0-vibeproxy-claude.json",
        "a0-vibeproxy-gpt52.json",
        "a0-vibeproxy-gpt51max.json",
        "a0-vibeproxy-opus.json"
    )

    foreach ($name in $preferred) {
        $path = Join-Path $Script:ConfigDir $name
        if (Test-Path $path) { return $path }
    }

    $fallback = Get-ChildItem $Script:ConfigDir -Filter "a0-vibeproxy-*.json" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($fallback) { return $fallback.FullName }

    return $null
}

function Normalize-ConfigName {
    param([string]$ModelId)
    if ([string]::IsNullOrWhiteSpace($ModelId)) { return "vibeproxy-custom" }
    $safe = $ModelId -replace "[^A-Za-z0-9._-]", "-"
    return "vibeproxy-$safe"
}

function Apply-ModelTempRules {
    param($Cfg)

    $map = @(
        @{ Name = "chat_model_name"; Kw = "chat_model_kwargs" },
        @{ Name = "util_model_name"; Kw = "util_model_kwargs" },
        @{ Name = "browser_model_name"; Kw = "browser_model_kwargs" }
    )

    foreach ($m in $map) {
        $model = $Cfg.$($m.Name)
        if ($model -and $model -like "gpt-5*") {
            if (-not $Cfg.$($m.Kw)) { $Cfg | Add-Member -NotePropertyName $m.Kw -NotePropertyValue @{} -Force }
            $Cfg.$($m.Kw).temperature = "1"
        }
    }
}

function Get-ModelOwner {
    param([string]$ModelId)

    if ([string]::IsNullOrWhiteSpace($ModelId)) { return "" }
    $models = Get-VibeProxyModels
    if (-not $models) { return "" }
    $match = $models.data | Where-Object { $_.id -eq $ModelId } | Select-Object -First 1
    if ($match -and $match.owned_by) { return $match.owned_by }
    return ""
}

function Apply-ModelOwnerRules {
    param(
        $Cfg,
        [string]$Owner
    )

    if (-not $Owner) { return }
    if ($Owner -match "github") {
        # For Copilot models, keep util/browser aligned to chat model to avoid unsupported model errors.
        $Cfg.util_model_name = $Cfg.chat_model_name
        $Cfg.util_model_api_base = $Cfg.chat_model_api_base
        $Cfg.util_model_provider = $Cfg.chat_model_provider

        $Cfg.browser_model_name = $Cfg.chat_model_name
        $Cfg.browser_model_api_base = $Cfg.chat_model_api_base
        $Cfg.browser_model_provider = $Cfg.chat_model_provider
    }
}

function Invoke-ModelPreflight {
    param([string]$ModelId)

    if ([string]::IsNullOrWhiteSpace($ModelId)) {
        return [pscustomobject]@{ Ok = $false; Message = "No model selected" }
    }

    $body = @{
        model = $ModelId
        messages = @(@{ role = "user"; content = "ping" })
        max_tokens = 5
        temperature = 1
    } | ConvertTo-Json -Depth 4

    try {
        $null = Invoke-RestMethod -Uri "http://localhost:$Script:TunnelPort/v1/chat/completions" `
            -Method POST `
            -Headers @{ "Content-Type" = "application/json"; "Authorization" = "Bearer dummy" } `
            -Body $body `
            -TimeoutSec 30
        return [pscustomobject]@{ Ok = $true; Message = "OK" }
    } catch {
        $msg = $_.Exception.Message
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $msg = $_.ErrorDetails.Message }
        return [pscustomobject]@{ Ok = $false; Message = $msg }
    }
}

function Invoke-ModelConversationalTest {
    param([string]$ModelId)

    if ([string]::IsNullOrWhiteSpace($ModelId)) {
        return [pscustomobject]@{ Ok = $false; Response = ""; Message = "No model selected" }
    }

    $maxTokens = Get-MaxTokens

    $body = @{
        model = $ModelId
        messages = @(@{ role = "user"; content = "Hi, what day is it today and who are you?" })
        max_tokens = $maxTokens
        temperature = 1
    } | ConvertTo-Json -Depth 4

    try {
        $result = Invoke-RestMethod -Uri "http://localhost:$Script:TunnelPort/v1/chat/completions" `
            -Method POST `
            -Headers @{ "Content-Type" = "application/json"; "Authorization" = "Bearer dummy" } `
            -Body $body `
            -TimeoutSec 60

        $responseText = $result.choices[0].message.content
        return [pscustomobject]@{ Ok = $true; Response = $responseText; Message = "OK" }
    } catch {
        $msg = $_.Exception.Message
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $msg = $_.ErrorDetails.Message }
        return [pscustomobject]@{ Ok = $false; Response = ""; Message = $msg }
    }
}

function Start-ModelChat {
    param([string]$ModelId)

    $maxTokens = Get-MaxTokens
    $messages = @()

    Clear-Host
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host ("║ 💬 Chat: {0,-54} [/exit to quit] ║" -f $ModelId.Substring(0, [Math]::Min($ModelId.Length, 54))) -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Commands: /exit /quit /q = leave  |  /clear = new conversation  |  /tokens N = set max" -ForegroundColor Gray
    Write-Host "            /model = show model     |  /help = show commands" -ForegroundColor Gray
    Write-Host ""

    while ($true) {
        Write-Host "You: " -ForegroundColor Green -NoNewline
        $userInput = Read-Host

        if ([string]::IsNullOrWhiteSpace($userInput)) { continue }

        # Handle chat commands
        if ($userInput -match "^/(exit|quit|q)$") {
            Write-Host ""
            Write-Host "Leaving chat mode..." -ForegroundColor Yellow
            Start-Sleep -Milliseconds 500
            break
        }

        if ($userInput -eq "/clear") {
            $messages = @()
            Clear-Host
            Write-Host ""
            Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
            Write-Host ("║ 💬 Chat: {0,-54} [/exit to quit] ║" -f $ModelId.Substring(0, [Math]::Min($ModelId.Length, 54))) -ForegroundColor Cyan
            Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  ✓ Conversation cleared" -ForegroundColor Green
            Write-Host ""
            continue
        }

        if ($userInput -match "^/tokens\s+(\d+)$") {
            $newTokens = [int]$Matches[1]
            Set-MaxTokens $newTokens
            $maxTokens = $newTokens
            Write-Host ""
            Write-Host "  ✓ Max tokens set to $maxTokens" -ForegroundColor Green
            Write-Host ""
            continue
        }

        if ($userInput -eq "/model") {
            Write-Host ""
            Write-Host "  Model: $ModelId" -ForegroundColor Cyan
            Write-Host "  Max tokens: $maxTokens" -ForegroundColor Cyan
            Write-Host "  Messages in history: $($messages.Count)" -ForegroundColor Cyan
            Write-Host ""
            continue
        }

        if ($userInput -eq "/help") {
            Write-Host ""
            Write-Host "  Chat Commands:" -ForegroundColor Cyan
            Write-Host "    /exit, /quit, /q  - Leave chat mode" -ForegroundColor Gray
            Write-Host "    /clear            - Clear conversation, start fresh" -ForegroundColor Gray
            Write-Host "    /tokens N         - Set max response tokens (e.g., /tokens 1000)" -ForegroundColor Gray
            Write-Host "    /model            - Show current model and settings" -ForegroundColor Gray
            Write-Host "    /help             - Show this help" -ForegroundColor Gray
            Write-Host ""
            continue
        }

        # Add user message to history
        $messages += @{ role = "user"; content = $userInput }

        # Call API
        $body = @{
            model = $ModelId
            messages = $messages
            max_tokens = $maxTokens
            temperature = 1
        } | ConvertTo-Json -Depth 10

        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

        try {
            $result = Invoke-RestMethod -Uri "http://localhost:$Script:TunnelPort/v1/chat/completions" `
                -Method POST `
                -Headers @{ "Content-Type" = "application/json"; "Authorization" = "Bearer dummy" } `
                -Body $body `
                -TimeoutSec 120

            $stopwatch.Stop()
            $elapsed = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1)

            $responseText = $result.choices[0].message.content
            $tokenCount = if ($result.usage -and $result.usage.completion_tokens) { $result.usage.completion_tokens } else { "?" }

            # Add assistant response to history
            $messages += @{ role = "assistant"; content = $responseText }

            Write-Host ""
            Write-Host "AI: " -ForegroundColor Magenta -NoNewline
            Write-Host $responseText -ForegroundColor White
            Write-Host ""
            Write-Host "    [$tokenCount tokens · ${elapsed}s]" -ForegroundColor DarkGray
            Write-Host ""

        } catch {
            $stopwatch.Stop()
            $msg = $_.Exception.Message
            if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $msg = $_.ErrorDetails.Message }

            # Remove the failed user message from history
            $messages = $messages[0..($messages.Count - 2)]

            Write-Host ""
            Write-Host "  ❌ Error: $msg" -ForegroundColor Red
            Write-Host ""
        }
    }
}

function Ensure-ConfigForModel {
    param([string]$ModelId)

    $configs = Get-ConfigOptions
    $match = $configs | Where-Object { $_.Model -eq $ModelId } | Select-Object -First 1
    if ($match) { return $match.Name }

    $basePath = Get-BaseVibeProxyConfigPath
    if (-not $basePath) {
        Write-Host "❌ No base VibeProxy config found in $Script:ConfigDir" -ForegroundColor Red
        return $null
    }

    try {
        $cfg = Get-Content $basePath -Raw | ConvertFrom-Json
    } catch {
        Write-Host "❌ Failed to read base config: $basePath" -ForegroundColor Red
        return $null
    }

    $cfg.chat_model_name = $ModelId
    $cfg._config_name = "VibeProxy ($ModelId)"
    $cfg._description = "Auto-generated VibeProxy config for $ModelId"

    $owner = Get-ModelOwner $ModelId
    Apply-ModelOwnerRules $cfg $owner
    Apply-ModelTempRules $cfg

    $name = Normalize-ConfigName $ModelId
    $fileName = "a0-$name.json"
    $targetPath = Join-Path $Script:ConfigDir $fileName
    $cfg | ConvertTo-Json -Depth 10 | Set-Content $targetPath

    return $name
}

function Resolve-ModelProvider {
    param($Model)

    $owner = $Model.owned_by
    $id = $Model.id

    if (-not [string]::IsNullOrWhiteSpace($owner)) {
        switch -Regex ($owner) {
            "anthropic" { return "Claude (Anthropic)" }
            "github" { return "GitHub Copilot" }
            "openai" { return "OpenAI" }
            "google|gemini" { return "Google (Gemini)" }
            "antigravity" { return "Antigravity" }
            "xai|grok" { return "xAI (Grok)" }
            default { return $owner }
        }
    }

    if ($id -like "claude*") { return "Claude (Anthropic)" }
    if ($id -like "gpt*") { return "OpenAI" }
    if ($id -like "gemini*") { return "Google (Gemini)" }
    if ($id -like "grok*") { return "xAI (Grok)" }
    if ($id -like "antigravity*") { return "Antigravity" }
    return "Other"
}

function Get-ModelGroups {
    param($Models)

    $groups = @{}
    foreach ($model in $Models.data) {
        $provider = Resolve-ModelProvider $model
        if (-not $groups.ContainsKey($provider)) {
            $groups[$provider] = New-Object System.Collections.Generic.List[string]
        }
        $groups[$provider].Add($model.id)
    }

    return $groups
}

function Write-CheckLine {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Details = "",
        [string]$Hint = ""
    )

    if ($Ok) {
        Write-Host "  ✅ $Name" -ForegroundColor Green
        if ($Details) { Write-Host "     $Details" -ForegroundColor DarkGray }
    } else {
        Write-Host "  ❌ $Name" -ForegroundColor Red
        if ($Details) { Write-Host "     $Details" -ForegroundColor DarkGray }
        if ($Hint) { Write-Host "     Fix: $Hint" -ForegroundColor Yellow }
    }
}

function Get-TunnelStatus {
    $tunnel = Get-NetTCPConnection -LocalPort $Script:TunnelPort -ErrorAction SilentlyContinue
    return ($null -ne $tunnel)
}

function Get-A0Status {
    $container = docker ps --filter "name=agent-zero" --format "{{.Status}}" 2>$null
    if ($container) {
        return $container
    }
    return "Not running"
}

function Get-CurrentA0Config {
    if (Test-Path $Script:A0SettingsPath) {
        $settings = Get-Content $Script:A0SettingsPath | ConvertFrom-Json
        $provider = $settings.chat_model_provider
        $model = $settings.chat_model_name
        $apiBase = $settings.chat_model_api_base

        if ($apiBase -like "*host.docker.internal*" -or $apiBase -like "*localhost:8317*") {
            $displayName = if ($Script:AvailableModels[$model]) { $Script:AvailableModels[$model] } else { $model }
            return "VibeProxy: $displayName"
        } elseif ($provider -eq "openrouter") {
            return "OpenRouter: $model"
        } else {
            return "$provider`: $model"
        }
    }
    return "Unknown"
}

function Show-Status {
    Refresh-VibeProxyConfig
    Write-Host "Status" -ForegroundColor $Script:Theme.Title
    Write-Rail

    # SSH Tunnel
    $tunnelRunning = Get-TunnelStatus
    Write-Host "  SSH Tunnel: " -NoNewline -ForegroundColor $Script:Theme.Text
    if ($tunnelRunning) {
        Write-Host "✅ Connected (port $Script:TunnelPort)" -ForegroundColor $Script:Theme.Success
    } else {
        Write-Host "❌ Not running" -ForegroundColor $Script:Theme.Error
    }

    # A0 Status
    $a0Status = Get-A0Status
    Write-Host "  Agent Zero: " -NoNewline -ForegroundColor $Script:Theme.Text
    if ($a0Status -like "*Up*") {
        $shortStatus = if ($a0Status.Length -gt 40) { $a0Status.Substring(0, 40) + "..." } else { $a0Status }
        Write-Host "✅ $shortStatus" -ForegroundColor $Script:Theme.Success
    } else {
        Write-Host "⚪ $a0Status" -ForegroundColor $Script:Theme.Warning
    }

    # Current Config
    $currentConfig = Get-CurrentA0Config
    Write-Host "  A0 Config:  " -NoNewline -ForegroundColor $Script:Theme.Text
    if ($currentConfig -like "*VibeProxy*") {
        Write-Host "🔵 $currentConfig" -ForegroundColor $Script:Theme.Glow
    } else {
        Write-Host "🟢 $currentConfig" -ForegroundColor $Script:Theme.Success
    }
    Write-Host ""
}

function Verify-Setup {
    Refresh-VibeProxyConfig
    Write-Host "🔎 Verifying local setup..." -ForegroundColor Cyan
    Write-Host ""

    $checks = @()

    $sshOk = $null -ne (Get-Command ssh -ErrorAction SilentlyContinue)
    $checks += [pscustomobject]@{ Name = "SSH client"; Ok = $sshOk }
    Write-CheckLine "SSH client" $sshOk "" "Install OpenSSH client (Windows Features)"

    $dockerOk = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
    $checks += [pscustomobject]@{ Name = "Docker CLI"; Ok = $dockerOk }
    Write-CheckLine "Docker CLI" $dockerOk "" "Install Docker Desktop"

    $a0PathOk = Test-Path $Script:A0SettingsPath
    $checks += [pscustomobject]@{ Name = "A0 settings file"; Ok = $a0PathOk }
    Write-CheckLine "A0 settings file" $a0PathOk $Script:A0SettingsPath "Verify Agent Zero data path"

    $factoryConfig = Join-Path $env:USERPROFILE ".factory\config.json"
    $factoryOk = Test-Path $factoryConfig
    $checks += [pscustomobject]@{ Name = "Factory config"; Ok = $factoryOk }
    Write-CheckLine "Factory config" $factoryOk $factoryConfig "Copy factory-config-example.json to this path"

    $configOk = Test-Path $Script:ConfigPath
    $checks += [pscustomobject]@{ Name = "VibeProxy config"; Ok = $configOk }
    Write-CheckLine "VibeProxy config" $configOk $Script:ConfigPath "Create vibeproxy-config.json (see defaults in scripts)"

    $a0Status = Get-A0Status
    $a0Ok = $a0Status -like "*Up*"
    $checks += [pscustomobject]@{ Name = "Agent Zero container"; Ok = $a0Ok }
    Write-CheckLine "Agent Zero container" $a0Ok $a0Status "Start Agent Zero / Docker Desktop"

    $tunnelOk = Get-TunnelStatus
    $checks += [pscustomobject]@{ Name = "SSH tunnel"; Ok = $tunnelOk }
    Write-CheckLine "SSH tunnel (port $Script:TunnelPort)" $tunnelOk "" "Run .\\ssh-tunnel-vibeproxy.ps1"

    Write-Host ""
    Write-Host "Config:" -ForegroundColor White
    Write-Host "  MacUser    : $($Script:MacUser)" -ForegroundColor Gray
    Write-Host "  MacIP      : $($Script:MacIP)" -ForegroundColor Gray
    Write-Host "  LocalPort  : $($Script:TunnelPort)" -ForegroundColor Gray
    Write-Host ""

    $passed = ($checks | Where-Object { $_.Ok }).Count
    $total = $checks.Count
    $color = if ($passed -eq $total) { "Green" } else { "Yellow" }
    Write-Host "Summary: $passed/$total checks passed" -ForegroundColor $color
    Write-Host ""
}

function Start-Tunnel {
    Refresh-VibeProxyConfig
    $tunnelRunning = Get-TunnelStatus
    if ($tunnelRunning) {
        Write-Host "⚠️  Tunnel already running on port $Script:TunnelPort" -ForegroundColor Yellow
        return $true
    }

    Write-Host "🚀 Starting SSH tunnel to $Script:MacUser@$Script:MacIP..." -ForegroundColor Cyan

    $tunnelScript = Join-Path $PSScriptRoot "ssh-tunnel-vibeproxy.ps1"
    if (Test-Path $tunnelScript) {
        Start-Process powershell -ArgumentList "-NoExit", "-File", $tunnelScript
        Write-Host "✅ Tunnel started in new window" -ForegroundColor Green
        Write-Host "   Keep that window open while using VibeProxy!" -ForegroundColor Gray
        Start-Sleep -Seconds 3
        return $true
    } else {
        Write-Host "❌ Tunnel script not found: $tunnelScript" -ForegroundColor Red
        return $false
    }
}

function Restart-A0 {
    Write-Host "🔄 Restarting Agent Zero container..." -ForegroundColor Cyan
    docker restart agent-zero-instance 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container restarted successfully" -ForegroundColor Green
        Write-Host "   Wait ~10 seconds for A0 to fully start" -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed to restart container" -ForegroundColor Red
    }
}

function Switch-A0Config {
    param(
        [string]$ConfigName,
        [switch]$AutoRestart
    )

    Refresh-VibeProxyConfig
    $configFile = Join-Path $Script:ConfigDir "a0-$ConfigName.json"

    if (-not (Test-Path $configFile)) {
        Write-Host "❌ Config not found: $configFile" -ForegroundColor Red
        return $false
    }

    # Check if VibeProxy config needs tunnel
    if ($ConfigName -like "*vibeproxy*") {
        $tunnelRunning = Get-TunnelStatus
        if (-not $tunnelRunning) {
            Write-Host "⚠️  VibeProxy mode requires SSH tunnel!" -ForegroundColor Yellow
            $response = Read-Host "Start tunnel now? (Y/n)"
            if ($response -ne 'n') {
                $started = Start-Tunnel
                if (-not $started) { return $false }
            }
        }
    }

    Write-Host "📝 Switching A0 to: $ConfigName" -ForegroundColor Cyan

    # Read new config (partial - only model settings)
    $newConfig = Get-Content $configFile | ConvertFrom-Json
    $owner = Get-ModelOwner $newConfig.chat_model_name
    Apply-ModelOwnerRules $newConfig $owner
    Apply-ModelTempRules $newConfig

    # Read current full settings
    if (-not (Test-Path $Script:A0SettingsPath)) {
        Write-Host "❌ A0 settings file not found!" -ForegroundColor Red
        return $false
    }
    $currentSettings = Get-Content $Script:A0SettingsPath | ConvertFrom-Json

    # Backup current settings
    $backupPath = Join-Path $Script:ConfigDir "backups"
    if (-not (Test-Path $backupPath)) { New-Item -ItemType Directory -Path $backupPath | Out-Null }
    $backupFile = Join-Path $backupPath "a0-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    $currentSettings | ConvertTo-Json -Depth 10 | Set-Content $backupFile
    Write-Host "   Backup: $backupFile" -ForegroundColor DarkGray

    # Update only model-related settings
    $modelSettings = @(
        "chat_model_provider", "chat_model_name", "chat_model_api_base", "chat_model_kwargs",
        "chat_model_ctx_length", "chat_model_ctx_history", "chat_model_vision",
        "chat_model_rl_requests", "chat_model_rl_input", "chat_model_rl_output",
        "util_model_provider", "util_model_name", "util_model_api_base", "util_model_kwargs",
        "util_model_ctx_length", "util_model_ctx_input",
        "util_model_rl_requests", "util_model_rl_input", "util_model_rl_output",
        "browser_model_provider", "browser_model_name", "browser_model_api_base", "browser_model_kwargs",
        "browser_model_vision", "browser_model_rl_requests", "browser_model_rl_input", "browser_model_rl_output"
    )

    foreach ($setting in $modelSettings) {
        if ($null -ne $newConfig.$setting) {
            $currentSettings.$setting = $newConfig.$setting
        }
    }

    # Update API keys if present in new config
    if ($newConfig.api_keys) {
        if (-not $currentSettings.api_keys) {
            $currentSettings | Add-Member -NotePropertyName "api_keys" -NotePropertyValue @{} -Force
        }
        foreach ($key in $newConfig.api_keys.PSObject.Properties) {
            $currentSettings.api_keys | Add-Member -NotePropertyName $key.Name -NotePropertyValue $key.Value -Force
        }
    }

    # Save updated settings
    $currentSettings | ConvertTo-Json -Depth 10 | Set-Content $Script:A0SettingsPath

    Write-Host "✅ Config switched to: $ConfigName" -ForegroundColor Green

    if ($AutoRestart) {
        Write-Host ""
        Restart-A0
    } else {
        Write-Host ""
        $response = Read-Host "Restart A0 now to apply changes? (Y/n)"
        if ($response -ne 'n') {
            Restart-A0
        }
    }

    return $true
}

function Test-VibeProxy {
    Refresh-VibeProxyConfig
    Write-Host "🔍 Testing VibeProxy connectivity..." -ForegroundColor Cyan
    Write-Host ""

    # Test from host
    Write-Host "1. Host → VibeProxy (localhost:$Script:TunnelPort)..." -ForegroundColor White
    $healthOk = $false
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Script:TunnelPort/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) { $healthOk = $true }
    } catch {
        $healthOk = $false
    }

    if ($healthOk) {
        Write-Host "   ✅ Health endpoint OK" -ForegroundColor Green
    } else {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Script:TunnelPort" -Method GET -TimeoutSec 5 -ErrorAction Stop
            Write-Host "   ✅ Connected (root endpoint)" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ FAILED - Is SSH tunnel running?" -ForegroundColor Red
            return
        }
    }

    # List models
    Write-Host ""
    Write-Host "2. Available models:" -ForegroundColor White
    $models = Get-VibeProxyModels
    if ($models) {
        $modelCount = $models.data.Count
        Write-Host "   ✅ $modelCount models available" -ForegroundColor Green

        # Group by provider
        $claude = ($models.data | Where-Object { $_.id -like "claude*" }).Count
        $gpt = ($models.data | Where-Object { $_.id -like "gpt*" }).Count
        $gemini = ($models.data | Where-Object { $_.id -like "gemini*" }).Count
        $other = $modelCount - $claude - $gpt - $gemini

        Write-Host "      Claude: $claude | GPT: $gpt | Gemini: $gemini | Other: $other" -ForegroundColor DarkGray
    } else {
        Write-Host "   ⚠️  Could not list models" -ForegroundColor Yellow
    }

    # Test API call
    Write-Host ""
    Write-Host "3. Testing API call..." -ForegroundColor White
    try {
        $selectedModel = $null
        if ($models) {
            $availableIds = $models.data | Select-Object -ExpandProperty id
            $preferred = @(
                "claude-sonnet-4-5-20250929",
                "claude-sonnet-4-5",
                "claude-opus-4-5-20251101",
                "gpt-5.2-codex",
                "gpt-5.1-codex-max",
                "gpt-4.1",
                "gemini-3-pro",
                "gemini-2.5-pro"
            )

            $selectedModel = $preferred | Where-Object { $availableIds -contains $_ } | Select-Object -First 1
            if (-not $selectedModel) {
                $selectedModel = $availableIds | Select-Object -First 1
            }
        }

        if (-not $selectedModel) {
            Write-Host "   ⚠️  No models available to test" -ForegroundColor Yellow
            Write-Host ""
            return
        }

        Write-Host "   Using model: $selectedModel" -ForegroundColor DarkGray
        $body = @{
            model = $selectedModel
            messages = @(@{role = "user"; content = "Say 'OK' only"})
            max_tokens = 5
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "http://localhost:$Script:TunnelPort/v1/chat/completions" `
            -Method POST `
            -Headers @{"Content-Type" = "application/json"; "Authorization" = "Bearer dummy"} `
            -Body $body `
            -TimeoutSec 30

        $reply = $response.choices[0].message.content
        Write-Host "   ✅ Response: $reply" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ API call failed" -ForegroundColor Red
        Write-Host "      $($_.Exception.Message)" -ForegroundColor DarkGray
    }

    Write-Host ""
}

function Show-ConfigMenu {
    Refresh-VibeProxyConfig
    $configs = Get-ConfigOptions
    if (-not $configs -or $configs.Count -eq 0) {
        Write-Host "No configs found in $Script:ConfigDir" -ForegroundColor $Script:Theme.Warning
        return
    }

    Write-Host ""
    Write-Host "Select A0 Configuration" -ForegroundColor $Script:Theme.Title
    Write-Rail
    Write-Host ""
    $currentConfig = Get-CurrentA0Config
    Write-Host ("  Current: {0}" -f $currentConfig) -ForegroundColor $Script:Theme.Muted
    Write-Host ""

    $index = 1
    foreach ($cfg in $configs) {
        $label = "{0,2}. {1,-22} {2}" -f $index, $cfg.Name, $cfg.Description
        $color = $Script:Theme.Text
        if ($cfg.Description -like "VibeProxy*") { $color = "Cyan" }
        elseif ($cfg.Description -like "openrouter*") { $color = $Script:Theme.Success }
        Write-Host "  $label" -ForegroundColor $color
        $index++
    }
    Write-Host ""
    Write-Host "  [B] Back" -ForegroundColor $Script:Theme.Muted
    Write-Host ""

    $choice = Read-Host "Select config"
    if ([string]::IsNullOrWhiteSpace($choice)) { return }
    if ($choice.ToLower() -eq "b") { return }

    if ($choice -match "^\d+$") {
        $idx = [int]$choice
        if ($idx -ge 1 -and $idx -le $configs.Count) {
            $selected = $configs[$idx - 1]
            Switch-A0Config $selected.Name
        } else {
            Write-Host "Invalid selection" -ForegroundColor Red
        }
    } else {
        Write-Host "Invalid selection" -ForegroundColor Red
    }
}

function Show-Menu {
    while ($true) {
        Write-Banner
        Show-Status

        Write-Host "✨ Main Menu" -ForegroundColor $Script:Theme.Title
        Write-Rail
        Write-Host ""
        Write-Host "  🔌 Connectivity" -ForegroundColor $Script:Theme.Section
        Write-Host "    [1] Start SSH Tunnel        [3] Test VibeProxy" -ForegroundColor $Script:Theme.Text
        Write-Host "    [6] Verify Setup" -ForegroundColor $Script:Theme.Text
        Write-Host ""
        Write-Host "───────────────────────────────────────────────────────────────────────" -ForegroundColor $Script:Theme.Border
        Write-Host "  🧠 Models & Configs" -ForegroundColor $Script:Theme.Section
        Write-Host "    [2] Switch A0 Config        [4] Browse Models" -ForegroundColor $Script:Theme.Text
        Write-Host ""
        Write-Host "───────────────────────────────────────────────────────────────────────" -ForegroundColor $Script:Theme.Border
        Write-Host "  ⚙️  System" -ForegroundColor $Script:Theme.Section
        Write-Host "    [5] Restart Agent Zero      [S] Show Status      [Q] Quit" -ForegroundColor $Script:Theme.Text
        Write-Host ""

        $choice = Read-Host "Select option"
        switch ($choice.ToLower()) {
            "1" { Start-Tunnel; Pause }
            "2" { Show-ConfigMenu; Pause }
            "3" { Test-VibeProxy; Pause }
            "4" { Show-AllModels; Pause }
            "5" { Restart-A0; Pause }
            "6" { Verify-Setup; Pause }
            "s" { Show-Status; Pause }
            "q" { return }
            default { Write-Host "Invalid option" -ForegroundColor Red; Start-Sleep -Seconds 1 }
        }
    }
}

function Show-AllModels {
    Refresh-VibeProxyConfig
    $models = Get-VibeProxyModels
    if (-not $models) {
        Write-Host ""
        Write-Host "  ❌ Could not fetch models - is tunnel running?" -ForegroundColor $Script:Theme.Error
        Write-Host ""
        return
    }

    $disabled = Get-DisabledModels
    $visible = $models.data
    if ($disabled -and $disabled.Count -gt 0) {
        $visible = $models.data | Where-Object { $disabled -notcontains $_.id }
    }
    $groups = Get-ModelGroups ([pscustomobject]@{ data = $visible })
    $providers = $groups.Keys | Sort-Object
    $selected = @{}
    foreach ($provider in $providers) { $selected[$provider] = $true }

    $viewMode = "grouped"  # grouped | flat
    $filter = ""
    $favoritesOnly = $false
    $favorites = Get-Favorites
    $preflightOnPick = $true
    $pollOn = $false
    $pollIntervalSec = 5
    $showModelList = $false  # Compact mode by default
    $maxTokens = Get-MaxTokens

    while ($true) {
        $indexMap = @{}
        Write-Host ""
        Write-Host "Browse Models (Live Providers + Search)" -ForegroundColor $Script:Theme.Title
        Write-Rail
        Write-Host ""

        Write-Host "  Providers (toggle):" -ForegroundColor $Script:Theme.Text
        for ($i = 0; $i -lt $providers.Count; $i++) {
            $provider = $providers[$i]
            $mark = if ($selected[$provider]) { "[x]" } else { "[ ]" }
            $count = $groups[$provider].Count
            Write-Host ("    {0} {1,2}. {2} ({3})" -f $mark, ($i + 1), $provider, $count) -ForegroundColor $Script:Theme.Muted
        }

        Write-Host ""
        $filterLabel = if ([string]::IsNullOrWhiteSpace($filter)) { "(none)" } else { $filter }
        Write-Host ("  Search filter: {0}" -f $filterLabel) -ForegroundColor $Script:Theme.Text
        Write-Host ("  View: {0}" -f $(if ($viewMode -eq "flat") { "Flat" } else { "Grouped" })) -ForegroundColor $Script:Theme.Text
        Write-Host ("  Favorites only: {0}" -f $(if ($favoritesOnly) { "On" } else { "Off" })) -ForegroundColor $Script:Theme.Text
        Write-Host ("  Preflight on pick: {0}" -f $(if ($preflightOnPick) { "On" } else { "Off" })) -ForegroundColor $Script:Theme.Text
        Write-Host ("  Poll live list: {0} ({1}s)" -f $(if ($pollOn) { "On" } else { "Off" }), $pollIntervalSec) -ForegroundColor $Script:Theme.Text
        Write-Host ""
        Write-Host ("  Max tokens: {0}" -f $maxTokens) -ForegroundColor $Script:Theme.Text
        Write-Host ""
        Write-Host "  [L]=list models  [C]=chat (#)  [P]=pick (#)  [X]=test (#)  [S]=search  [F]=fav (#)" -ForegroundColor $Script:Theme.Muted
        Write-Host "  [number]=toggle provider  [A]=all  [N]=none  [V]=view  [O]=fav-only  [T]=preflight  [R]=refresh  [Q]=back" -ForegroundColor $Script:Theme.Muted
        Write-Host ""

        $activeProviders = $providers | Where-Object { $selected[$_] }
        if (-not $activeProviders -or $activeProviders.Count -eq 0) {
            Write-Host "  ⚠️  No providers selected" -ForegroundColor $Script:Theme.Warning
        } elseif (-not $showModelList) {
            # Compact mode - just show summary
            $totalModels = 0
            $providerSummary = @()
            foreach ($provider in $activeProviders) {
                $list = $groups[$provider]
                if (-not [string]::IsNullOrWhiteSpace($filter)) {
                    $list = $list | Where-Object { $_ -match [regex]::Escape($filter) }
                }
                if ($favoritesOnly) {
                    $list = $list | Where-Object { $favorites -contains $_ }
                }
                $count = @($list).Count
                $totalModels += $count
                $providerSummary += "$provider ($count)"
            }
            Write-Host ""
            Write-Host "  📋 Providers: $($providerSummary -join ' | ')" -ForegroundColor $Script:Theme.Text
            Write-Host "  📊 Total: $totalModels models | ⭐ Favorites: $($favorites.Count) starred" -ForegroundColor $Script:Theme.Muted
            Write-Host ""
            Write-Host "  💡 Press [L] to list all models, [C #] to chat with model #" -ForegroundColor Yellow

            # Still build indexMap for command handlers
            $index = 1
            foreach ($provider in $activeProviders) {
                foreach ($id in $groups[$provider]) {
                    if ([string]::IsNullOrWhiteSpace($filter) -or ($id -match [regex]::Escape($filter))) {
                        if (-not $favoritesOnly -or ($favorites -contains $id)) {
                            $indexMap[$index] = [pscustomobject]@{ Provider = $provider; Id = $id }
                            $index++
                        }
                    }
                }
            }
        } else {
            # Show full model list
            $showModelList = $false  # Reset after showing
            $index = 1
            if ($viewMode -eq "flat") {
                $flat = @()
                foreach ($provider in $activeProviders) {
                    foreach ($id in $groups[$provider]) {
                        if ([string]::IsNullOrWhiteSpace($filter) -or ($id -match [regex]::Escape($filter))) {
                            if (-not $favoritesOnly -or ($favorites -contains $id)) {
                                $flat += [pscustomobject]@{ Provider = $provider; Id = $id }
                            }
                        }
                    }
                }

                $flat = $flat | Sort-Object @{ Expression = { if ($favorites -contains $_.Id) { 0 } else { 1 } } }, Provider, Id
                Write-Host "  Models (flat):" -ForegroundColor $Script:Theme.Text
                foreach ($item in $flat) {
                    $indexMap[$index] = $item
                    $favMark = if ($favorites -contains $item.Id) { "[*]" } else { "[ ]" }
                    $color = if ($favorites -contains $item.Id) { "Yellow" } else { "Gray" }
                    Write-Host ("    {0,3}. {1} {2} :: {3}" -f $index, $favMark, $item.Provider, $item.Id) -ForegroundColor $color
                    $index++
                }
            } else {
                foreach ($provider in $activeProviders) {
                    $list = $groups[$provider] | Sort-Object
                    if (-not [string]::IsNullOrWhiteSpace($filter)) {
                        $list = $list | Where-Object { $_ -match [regex]::Escape($filter) }
                    }
                    if ($favoritesOnly) {
                        $list = $list | Where-Object { $favorites -contains $_ }
                    }

                $list = $list | Sort-Object @{ Expression = { if ($favorites -contains $_) { 0 } else { 1 } } }, { $_ }
                    Write-Host ""
                    Write-Host "  $provider ($($list.Count)):" -ForegroundColor $Script:Theme.Text
                    Write-Host "  ─────────────────────────────────────────────────────────────" -ForegroundColor $Script:Theme.Muted
                    foreach ($id in $list) {
                    $indexMap[$index] = [pscustomobject]@{ Provider = $provider; Id = $id }
                    $favMark = if ($favorites -contains $id) { "[*]" } else { "[ ]" }
                    $color = if ($favorites -contains $id) { "Yellow" } else { "Gray" }
                    Write-Host ("    {0,3}. {1} {2}" -f $index, $favMark, $id) -ForegroundColor $color
                    $index++
                }
            }
        }
        }

        Write-Host ""
        $choice = Read-Host "Select"
        if ([string]::IsNullOrWhiteSpace($choice)) { continue }
        $choice = $choice.ToLower()

        if ($choice -eq "q") { break }
        if ($choice -eq "a") { foreach ($provider in $providers) { $selected[$provider] = $true }; continue }
        if ($choice -eq "n") { foreach ($provider in $providers) { $selected[$provider] = $false }; continue }
        if ($choice -eq "o") { $favoritesOnly = -not $favoritesOnly; continue }
        if ($choice -eq "t") { $preflightOnPick = -not $preflightOnPick; continue }
        if ($choice -eq "y") { $pollOn = -not $pollOn; continue }
        if ($choice -eq "s") {
            $filter = Read-Host "Search text (empty clears)"
            if ($null -eq $filter) { $filter = "" }
            continue
        }
        if ($choice -eq "v") {
            $viewMode = if ($viewMode -eq "flat") { "grouped" } else { "flat" }
            continue
        }
        if ($choice -eq "l") {
            $showModelList = $true
            continue
        }
        if ($choice -match "^c\s*(\d+)?$") {
            $chatNum = $Matches[1]
            if ([string]::IsNullOrWhiteSpace($chatNum)) {
                $chatNum = Read-Host "Chat with model - enter number"
            }
            if ($chatNum -match "^\d+$") {
                $chatIndex = [int]$chatNum
                if ($indexMap.ContainsKey($chatIndex)) {
                    $modelId = $indexMap[$chatIndex].Id
                    Start-ModelChat $modelId
                } else {
                    Write-Host "Invalid model number" -ForegroundColor $Script:Theme.Error
                }
            } else {
                Write-Host "Invalid model number" -ForegroundColor $Script:Theme.Error
            }
            continue
        }
        if ($choice -eq "f") {
            $favInput = Read-Host "Favorite toggle - model number"
            if ($favInput -match "^\d+$") {
                $favIndex = [int]$favInput
                if ($indexMap.ContainsKey($favIndex)) {
                    $modelId = $indexMap[$favIndex].Id
                    if ($favorites -contains $modelId) {
                        $favorites = $favorites | Where-Object { $_ -ne $modelId }
                    } else {
                        $favorites += $modelId
                    }
                    Save-Favorites $favorites
                } else {
                    Write-Host "Invalid model number" -ForegroundColor $Script:Theme.Error
                }
            } else {
                Write-Host "Invalid model number" -ForegroundColor $Script:Theme.Error
            }
            continue
        }
        if ($choice -eq "p") {
            $pickInput = Read-Host "Pick model - model number"
            if ($pickInput -match "^\d+$") {
                $pickIndex = [int]$pickInput
                if ($indexMap.ContainsKey($pickIndex)) {
                    $modelId = $indexMap[$pickIndex].Id
                    if ($preflightOnPick) {
                        $pf = Invoke-ModelPreflight $modelId
                        if (-not $pf.Ok) {
                            Write-Host "❌ Preflight failed: $($pf.Message)" -ForegroundColor $Script:Theme.Error
                            $cont = Read-Host "Continue anyway? (y/N)"
                            if ($cont.ToLower() -ne "y") { continue }
                        } else {
                            Write-Host "✅ Preflight OK" -ForegroundColor $Script:Theme.Success
                        }
                    }
                    $configName = Ensure-ConfigForModel $modelId
                    if ($configName) {
                        Update-FactoryConfigModel $modelId
                        Switch-A0Config $configName
                    }
                } else {
                    Write-Host "Invalid model number" -ForegroundColor $Script:Theme.Error
                }
            } else {
                Write-Host "Invalid model number" -ForegroundColor $Script:Theme.Error
            }
            continue
        }
        if ($choice -eq "x") {
            $testInput = Read-Host "Test model - model number"
            if ($testInput -match "^\d+$") {
                $testIndex = [int]$testInput
                if ($indexMap.ContainsKey($testIndex)) {
                    $modelId = $indexMap[$testIndex].Id
                    $currentMaxTokens = Get-MaxTokens
                    Write-Host ""
                    Write-Host "🧪 Testing model: $modelId" -ForegroundColor Cyan
                    Write-Host "   Sending: 'Hi, what day is it today and who are you?'" -ForegroundColor Gray
                    Write-Host "   Max tokens: $currentMaxTokens" -ForegroundColor Gray
                    Write-Host ""

                    $test = Invoke-ModelConversationalTest $modelId
                    if ($test.Ok) {
                        Write-Host "✅ Model responded successfully!" -ForegroundColor $Script:Theme.Success
                        Write-Host ""
                        Write-Host "📝 Response:" -ForegroundColor $Script:Theme.Text
                        Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor $Script:Theme.Muted
                        Write-Host $test.Response -ForegroundColor White
                        Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor $Script:Theme.Muted
                    } else {
                        Write-Host "❌ Test failed: $modelId" -ForegroundColor $Script:Theme.Error
                        Write-Host ""
                        Write-Host $test.Message -ForegroundColor $Script:Theme.Muted
                    }
                    Write-Host ""
                } else {
                    Write-Host "Invalid model number" -ForegroundColor $Script:Theme.Error
                }
            } else {
                Write-Host "Invalid model number" -ForegroundColor $Script:Theme.Error
            }
            continue
        }
        if ($choice -eq "r") {
            $models = Get-VibeProxyModels
            if (-not $models) {
                Write-Host "  ❌ Could not fetch models - is tunnel running?" -ForegroundColor $Script:Theme.Error
                continue
            }
            $disabled = Get-DisabledModels
            $visible = $models.data
            if ($disabled -and $disabled.Count -gt 0) {
                $visible = $models.data | Where-Object { $disabled -notcontains $_.id }
            }
            $groups = Get-ModelGroups ([pscustomobject]@{ data = $visible })
            $providers = $groups.Keys | Sort-Object
            foreach ($provider in $providers) {
                if (-not $selected.ContainsKey($provider)) { $selected[$provider] = $true }
            }
            foreach ($key in @($selected.Keys)) {
                if (-not ($providers -contains $key)) { $selected.Remove($key) | Out-Null }
            }
            $favorites = Get-Favorites
            continue
        }

        if ($pollOn) {
            Write-Host "Polling... press any key to stop" -ForegroundColor $Script:Theme.Muted
            $elapsed = 0
            while ($elapsed -lt $pollIntervalSec) {
                Start-Sleep -Milliseconds 200
                $elapsed += 0.2
                if ($Host.UI.RawUI.KeyAvailable) {
                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                    $pollOn = $false
                    break
                }
            }
            if ($pollOn) {
                $models = Get-VibeProxyModels
                if ($models) {
                    $disabled = Get-DisabledModels
                    $visible = $models.data
                    if ($disabled -and $disabled.Count -gt 0) {
                        $visible = $models.data | Where-Object { $disabled -notcontains $_.id }
                    }
                    $groups = Get-ModelGroups ([pscustomobject]@{ data = $visible })
                    $providers = $groups.Keys | Sort-Object
                    foreach ($provider in $providers) {
                        if (-not $selected.ContainsKey($provider)) { $selected[$provider] = $true }
                    }
                    foreach ($key in @($selected.Keys)) {
                        if (-not ($providers -contains $key)) { $selected.Remove($key) | Out-Null }
                    }
                }
                continue
            }
        }

        if ($choice -match "^\d+$") {
            $idx = [int]$choice
            if ($idx -ge 1 -and $idx -le $providers.Count) {
                $provider = $providers[$idx - 1]
                $selected[$provider] = -not $selected[$provider]
            } else {
                Write-Host "Invalid selection" -ForegroundColor Red
            }
        } else {
            Write-Host "Invalid selection" -ForegroundColor Red
        }
    }
}

function Pause {
    Write-Host ""
    Write-Host "Press any key to continue..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# ═══════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════

Show-Menu
