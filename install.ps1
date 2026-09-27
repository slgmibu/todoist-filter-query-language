# Windows PowerShell installer for Todoist Filter Query Language (TFQL)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$scriptDir\tools\install.py"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 "$scriptDir\tools\install.py"
} else {
    Write-Error "Python 3 is required to run the installer."
}
