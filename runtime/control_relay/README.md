# HeavenzFire Control Relay — PowerShell 5.1 bootstrap

This first slice is a **local read-only CLI**, not the completed remote relay. It intentionally creates no service, scheduled task, firewall rule, or inbound listener.

## Install on the Windows workstation

Run in a normal (non-administrator) Windows PowerShell 5.1 window. This downloads the installer as a file, then runs that file; it does not pipe downloaded code directly into a shell.

```powershell
$ErrorActionPreference = 'Stop'
$installScript = Join-Path $env:TEMP 'Install-HeavenzFireControlRelay.ps1'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/HeavenzFire/HeavenzFire-Sovereign-Node/main/runtime/control_relay/Install-HeavenzFireControlRelay.ps1' -OutFile $installScript
Get-FileHash -LiteralPath $installScript -Algorithm SHA256
notepad.exe $installScript
```

Review the downloaded file, then run it in that same PowerShell session:

```powershell
& $installScript
```

The installer writes the agent to `$env:LOCALAPPDATA\HeavenzFire\ControlRelay`, prints the installed agent's SHA-256, and runs a local status self-test. No administrator elevation is needed.

## Allowed operations

```powershell
$relay = Join-Path $env:LOCALAPPDATA 'HeavenzFire\ControlRelay\Invoke-HeavenzFireControlRelay.ps1'
& $relay -Operation status
& $relay -Operation disk
& $relay -Operation processes
& $relay -Operation git-status -Workspace 'C:\path\to\an\existing\repo'
```

The allowlist is fixed: `status`, `disk`, `processes`, and `git-status`. It does not accept arbitrary command strings. Process output is capped to the first 40 processes; disk output includes drive size/free space. Do not post raw machine results publicly if they contain private details.

## What is not installed yet

- No outbound task polling or ChatGPT transport.
- No background service or scheduled task.
- No command execution, write operations, or admin operations.
- No private control repository or credential has been configured.

The repository is public. Do not use public GitHub issues or commits to exchange live tasks, command output, tokens, or machine diagnostics. Completing the remote connection requires a private control plane and an authenticated Windows-side outbound client. The current GitHub integration does not itself install files on the user's workstation, and this CLI must not be described as connected until a real end-to-end test passes.
