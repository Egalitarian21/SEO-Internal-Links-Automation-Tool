$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $root "scripts\verify-local-utf8.ps1"
$text = [System.IO.File]::ReadAllText($script, [System.Text.Encoding]::UTF8)
& ([scriptblock]::Create($text))
