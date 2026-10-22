#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'HeavenzFire\ControlRelay')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$sourceUri = 'https://raw.githubusercontent.com/HeavenzFire/HeavenzFire-Sovereign-Node/main/runtime/control_relay/Invoke-HeavenzFireControlRelay.ps1'
$target = Join-Path $InstallRoot 'Invoke-HeavenzFireControlRelay.ps1'
$null = New-Item -ItemType Directory -Path $InstallRoot -Force

# TLS 1.2 is needed on some Windows PowerShell 5.1 installations.
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch {}

Write-Host 'Downloading the read-only relay CLI from the HeavenzFire repository...'
Invoke-WebRequest -Uri $sourceUri -OutFile $target -UseBasicParsing
if (-not (Test-Path -LiteralPath $target)) { throw 'Download failed: relay script not found.' }

$hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
Write-Host ('Installed: ' + $target)
Write-Host ('SHA256:    ' + $hash)
Write-Host ''
Write-Host 'Running local status self-test...'
& $target -Operation status
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw 'Local status self-test failed.' }
Write-Host ''
Write-Host 'Installation complete. No service, scheduled task, firewall rule, or inbound listener was created.'
Write-Host 'Remote transport is intentionally not configured; this CLI cannot receive ChatGPT tasks yet.'
Write-Host 'To run an allowed read-only operation:'
Write-Host ('  & "' + $target + '" -Operation disk')
Write-Host ('  & "' + $target + '" -Operation processes')
