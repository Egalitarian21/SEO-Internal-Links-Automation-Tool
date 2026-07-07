$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "install-wsl.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log {
    param([string]$Message)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Encoding UTF8 -Value $line
}

function Enable-Feature {
    param([string]$FeatureName)

    Write-Log "Enable Windows feature: $FeatureName"
    & dism.exe /online /enable-feature /featurename:$FeatureName /all /norestart
    $code = $LASTEXITCODE
    Write-Log "DISM exit code for $FeatureName`: $code"

    if ($code -ne 0 -and $code -ne 3010) {
        throw "DISM failed for $FeatureName with exit code $code"
    }
}

Write-Log "Start WSL prerequisite setup."
Enable-Feature "Microsoft-Windows-Subsystem-Linux"
Enable-Feature "VirtualMachinePlatform"

Write-Log "Run: wsl --install --no-distribution"
& wsl.exe --install --no-distribution
Write-Log "wsl install exit code: $LASTEXITCODE"

Write-Log "Run: wsl --set-default-version 2"
& wsl.exe --set-default-version 2
Write-Log "wsl set default version exit code: $LASTEXITCODE"

Write-Log "WSL prerequisite setup finished. Restart Windows before opening Docker Desktop."
