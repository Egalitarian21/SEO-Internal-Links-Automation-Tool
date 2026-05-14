$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $rootDir "Backend"
$frontendDir = Join-Path $rootDir "Frontend"
$backendLog = Join-Path $backendDir "backend-run.log"
$backendErr = Join-Path $backendDir "backend-run.err"
$frontendLog = Join-Path $frontendDir "frontend-server.log"
$frontendErr = Join-Path $frontendDir "frontend-server.err"
$frontendCacheDir = Join-Path $frontendDir ".next"

$backendUrl = "http://127.0.0.1:8000/healthz"
$frontendUrl = "http://127.0.0.1:3000"

function Start-HiddenPowerShell {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [string]$StdOutPath,
        [Parameter(Mandatory = $true)]
        [string]$StdErrPath
    )

    Set-Content -Path $StdOutPath -Value $null -Encoding UTF8
    Set-Content -Path $StdErrPath -Value $null -Encoding UTF8

    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-WindowStyle",
        "Hidden",
        "-Command",
        $Command
    ) -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -RedirectStandardOutput $StdOutPath -RedirectStandardError $StdErrPath | Out-Null
}

function Get-PortProcessId {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $lines = & cmd.exe /c "netstat -ano -p tcp | findstr LISTENING | findstr :$Port"

    foreach ($line in $lines) {
        if ($line -match "^\s*TCP\s+\S+:$Port\s+\S+\s+LISTENING\s+(\d+)\s*$") {
            return [int]$matches[1]
        }
    }

    return $null
}

function Stop-PortProcess {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string[]]$AllowedProcessNames,
        [Parameter(Mandatory = $true)]
        [string]$DisplayName
    )

    $portProcessId = Get-PortProcessId -Port $Port

    if (-not $portProcessId) {
        return $false
    }

    $process = Get-Process -Id $portProcessId -ErrorAction Stop
    $allowedNames = $AllowedProcessNames | ForEach-Object { $_.ToLowerInvariant() }
    $actualName = $process.ProcessName.ToLowerInvariant()

    if ($allowedNames -notcontains $actualName) {
        throw "Port $Port is occupied by '$($process.ProcessName)' (PID $portProcessId). Please close it manually and try again."
    }

    Stop-Process -Id $portProcessId -Force -ErrorAction Stop
    Start-Sleep -Seconds 2
    return $true
}

function Test-HttpReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Wait-HttpReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        if (Test-HttpReady -Url $Url) {
            return $true
        }

        Start-Sleep -Seconds 2
    }

    return $false
}

function Show-LauncherError {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($Message, "Internal Link Tool Demo", "OK", "Error") | Out-Null
}

try {
    if (-not (Test-Path (Join-Path $backendDir "app\main.py"))) {
        throw "Backend entry file not found: $backendDir\app\main.py"
    }

    if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
        throw "Frontend package.json not found: $frontendDir\package.json"
    }

    $pythonExe = (Get-Command python.exe -ErrorAction Stop).Source
    $npmCmd = Join-Path $env:ProgramFiles "nodejs\npm.cmd"

    if (-not (Test-Path $npmCmd)) {
        throw "npm.cmd not found. Please confirm Node.js is installed correctly."
    }

    if (-not (Test-HttpReady -Url $backendUrl)) {
        $backendCommand = "& '$pythonExe' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
        Stop-PortProcess -Port 8000 -AllowedProcessNames @("python") -DisplayName "backend" | Out-Null
        Start-HiddenPowerShell -WorkingDirectory $backendDir -Command $backendCommand -StdOutPath $backendLog -StdErrPath $backendErr
    }

    if (-not (Wait-HttpReady -Url $backendUrl -TimeoutSeconds 25)) {
        throw "Backend startup timed out. Please check Backend\\backend-run.log and Backend\\backend-run.err."
    }

    if (-not (Test-HttpReady -Url $frontendUrl)) {
        $stoppedFrontend = Stop-PortProcess -Port 3000 -AllowedProcessNames @("node") -DisplayName "frontend"

        if ($stoppedFrontend -and (Test-Path $frontendCacheDir)) {
            # A stale Next.js dev cache can leave broken chunk references behind.
            Remove-Item -LiteralPath $frontendCacheDir -Recurse -Force
        }

        $frontendCommand = "& '$npmCmd' run dev -- --hostname 127.0.0.1 --port 3000"
        Start-HiddenPowerShell -WorkingDirectory $frontendDir -Command $frontendCommand -StdOutPath $frontendLog -StdErrPath $frontendErr
    }

    if (-not (Wait-HttpReady -Url $frontendUrl -TimeoutSeconds 90)) {
        throw "Frontend startup timed out. Please check Frontend\\frontend-server.log and Frontend\\frontend-server.err."
    }

    Start-Process $frontendUrl | Out-Null
}
catch {
    Show-LauncherError -Message $_.Exception.Message
    exit 1
}
