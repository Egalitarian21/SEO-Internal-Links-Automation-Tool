$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    $Root = $env:ILMVP_ROOT.TrimEnd("\")
}
else {
    $Root = Split-Path -Parent $PSScriptRoot
}
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "start-local.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log {
    param([string]$Message)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -LiteralPath $LogFile -Encoding UTF8 -Value "[$timestamp] $Message"
}

function Find-CommandPath {
    param([string]$CommandName)

    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        return $null
    }

    return $command.Source
}

function Start-HiddenProcess {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.Arguments = Join-ProcessArguments $Arguments

    return [System.Diagnostics.Process]::Start($startInfo)
}

function Join-ProcessArguments {
    param([string[]]$Arguments)

    $parts = foreach ($argument in $Arguments) {
        if ($null -eq $argument) {
            '""'
        }
        elseif ($argument -match '[\s"]') {
            '"' + ($argument -replace '"', '\"') + '"'
        }
        else {
            $argument
        }
    }

    return ($parts -join " ")
}

try {
    Write-Log "开始启动 SEO 内链 MVP。"

    $dockerPath = Find-CommandPath "docker"
    if ([string]::IsNullOrWhiteSpace($dockerPath)) {
        Write-Log "未检测到 Docker。请先安装并启动 Docker Desktop：https://www.docker.com/products/docker-desktop/"
        exit 1
    }
    Write-Log "Docker 路径：$dockerPath"

    $npmPath = Find-CommandPath "npm.cmd"
    if ([string]::IsNullOrWhiteSpace($npmPath)) {
        Write-Log "未检测到 npm.cmd。请先安装 Node.js。"
        exit 1
    }

    $pythonPath = Find-CommandPath "python"
    if ([string]::IsNullOrWhiteSpace($pythonPath)) {
        Write-Log "未检测到 python。请先安装 Python 3.11 或更新版本。"
        exit 1
    }

    $backendDir = Join-Path $Root "backend"
    $frontendDir = Join-Path $Root "frontend"
    $backendPython = Join-Path $backendDir ".venv\Scripts\python.exe"
    $frontendNodeModules = Join-Path $frontendDir "node_modules"

    if (-not (Test-Path -LiteralPath $backendPython)) {
        Write-Log "后端虚拟环境不存在。请先按 README.md 中的后端安装命令完成设置。"
        exit 1
    }

    if (-not (Test-Path -LiteralPath $frontendNodeModules)) {
        Write-Log "前端依赖不存在。请先在 frontend 目录中运行 npm.cmd install。"
        exit 1
    }

    Write-Log "正在启动 PostgreSQL。"
    $dockerProcess = Start-HiddenProcess -FilePath $dockerPath -WorkingDirectory $Root -Arguments @("compose", "up", "-d")
    if ($null -eq $dockerProcess) {
        Write-Log "PostgreSQL 启动失败：Docker 进程没有创建成功。"
        exit 1
    }
    $dockerProcess.WaitForExit()
    if ($dockerProcess.ExitCode -ne 0) {
        Write-Log "PostgreSQL 启动失败。请确认 Docker Desktop 正在运行。退出码：$($dockerProcess.ExitCode)"
        exit 1
    }

    Write-Log "正在启动后端服务：http://localhost:8000"
    [void](Start-HiddenProcess `
        -FilePath $backendPython `
        -WorkingDirectory $backendDir `
        -Arguments @("-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"))

    Write-Log "正在启动前端服务：http://localhost:5173"
    [void](Start-HiddenProcess `
        -FilePath "cmd.exe" `
        -WorkingDirectory $frontendDir `
        -Arguments @("/c", "call", $npmPath, "run", "dev", "--", "--host", "127.0.0.1"))

    Start-Sleep -Seconds 3

    Write-Log "正在打开浏览器。"
    Start-Process "http://localhost:5173"

    Write-Log "启动命令已执行完成。"
}
catch {
    Write-Log "启动失败：$($_.Exception.Message)"
    exit 1
}
