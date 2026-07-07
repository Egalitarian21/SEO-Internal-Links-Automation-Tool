param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot
)

$env:ILMVP_ROOT = $ProjectRoot
$ResolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot.Trim('"')).Path
$env:ILMVP_ROOT = $ResolvedRoot
$script = Join-Path $ResolvedRoot "scripts\start-local-hidden.ps1"
$text = [System.IO.File]::ReadAllText($script, [System.Text.Encoding]::UTF8)
& ([scriptblock]::Create($text))
