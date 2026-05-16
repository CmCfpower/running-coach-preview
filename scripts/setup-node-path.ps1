$ErrorActionPreference = "Stop"

$Root = Resolve-Path "$PSScriptRoot\.."
$NodeRoot = Join-Path $Root ".tools\node-v24.15.0-win-x64"
$NpmBin = Join-Path $NodeRoot "node_modules\npm\bin"

if (-not (Test-Path (Join-Path $NodeRoot "node.exe"))) {
  throw "Local Node was not found at $NodeRoot"
}

$env:PATH = "$NodeRoot;$NpmBin;$env:PATH"

Write-Host "Local Node is ready:"
& (Join-Path $NodeRoot "node.exe") --version
Write-Host "npm:"
& (Join-Path $NodeRoot "npm.cmd") --version
Write-Host "npx:"
& (Join-Path $NodeRoot "npx.cmd") --version

Write-Host ""
Write-Host "Use npm.cmd and npx.cmd in this PowerShell session."
