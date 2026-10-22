#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('status','disk','processes','git-status')]
    [string]$Operation,
    [string]$Workspace
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-RelayResult {
    param([string]$Name, [object]$Data)
    [pscustomobject]@{
        service = 'HeavenzFireControlRelay'
        version = '0.1.0'
        operation = $Name
        timestamp_utc = [DateTime]::UtcNow.ToString('o')
        execution_mode = 'read_only_allowlist'
        result = $Data
    } | ConvertTo-Json -Depth 5
}

switch ($Operation) {
    'status' {
        $python = Get-Command python -ErrorAction SilentlyContinue
        $git = Get-Command git -ErrorAction SilentlyContinue
        Write-RelayResult -Name 'status' -Data @{
            computer_name = $env:COMPUTERNAME
            user_name = $env:USERNAME
            powershell_version = $PSVersionTable.PSVersion.ToString()
            python_available = [bool]$python
            git_available = [bool]$git
            inbound_listener = $false
            remote_transport = 'not_configured'
            execution_enabled = $false
        }
    }
    'disk' {
        $items = @(Get-CimInstance -ClassName Win32_LogicalDisk -Filter 'DriveType=3' |
            Select-Object DeviceID, Size, FreeSpace)
        Write-RelayResult -Name 'disk' -Data $items
    }
    'processes' {
        $items = @(Get-Process |
            Sort-Object ProcessName |
            Select-Object -First 40 ProcessName, Id, CPU)
        Write-RelayResult -Name 'processes' -Data $items
    }
    'git-status' {
        if ([string]::IsNullOrWhiteSpace($Workspace)) {
            throw 'git-status requires -Workspace with an explicit directory.'
        }
        $resolved = Resolve-Path -LiteralPath $Workspace -ErrorAction Stop
        if (-not (Test-Path -LiteralPath (Join-Path $resolved.Path '.git'))) {
            throw 'Workspace must be a Git repository root containing .git.'
        }
        $git = Get-Command git -ErrorAction Stop
        $output = & $git.Source -C $resolved.Path status --short --branch 2>&1
        if ($LASTEXITCODE -ne 0) { throw 'git status failed.' }
        Write-RelayResult -Name 'git-status' -Data @{
            workspace = $resolved.Path
            status = @($output | ForEach-Object { [string]$_ })
        }
    }
}
