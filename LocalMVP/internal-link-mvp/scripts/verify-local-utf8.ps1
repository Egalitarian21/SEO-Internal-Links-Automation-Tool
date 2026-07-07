$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    $Root = (Resolve-Path -LiteralPath ".").Path
}
else {
    $Root = Split-Path -Parent $PSScriptRoot
}
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"

Write-Host "== SEO 内链 MVP 本机验收 =="

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "未找到后端虚拟环境：$PythonExe"
}

Write-Host "`n[1/4] 运行后端测试"
Push-Location $BackendDir
try {
    & $PythonExe -m pytest
    if ($LASTEXITCODE -ne 0) {
        throw "后端测试失败。"
    }
}
finally {
    Pop-Location
}

Write-Host "`n[2/4] 运行前端构建"
Push-Location $FrontendDir
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) {
        throw "前端构建失败。"
    }
}
finally {
    Pop-Location
}

Write-Host "`n[3/4] 检查 Docker"
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $docker) {
    Write-Host "未检测到 Docker。真实 PostgreSQL 验收需先安装并启动 Docker Desktop。"
    exit 0
}

Write-Host "`n[4/4] 验证 PostgreSQL 与 Alembic 迁移"
Push-Location $Root
try {
    & docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up -d 失败。"
    }
}
finally {
    Pop-Location
}

Push-Location $BackendDir
try {
    & $PythonExe -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Alembic 迁移失败。"
    }
}
finally {
    Pop-Location
}

Write-Host "`n验收脚本执行完成。"
