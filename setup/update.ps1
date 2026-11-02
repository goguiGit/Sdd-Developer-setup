<#
.SYNOPSIS
Actualiza el marketplace y todos los plugins instalados desde él. Es lo que ejecuta la tarea programada; también se puede lanzar a mano.
Escribe un log en ~/.claude/sdd-update.log y sale con 1 si Claude Code devolvió un fallo.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$marketplace = 'sdd-developer-setup'
$log = Join-Path $HOME '.claude\sdd-update.log'
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null

function Log([string] $Text) {
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Text
    Add-Content -Path $log -Value $line
    Write-Host $line
}

function Run([string] $Label, [string[]] $Arguments) {
    $output = (& claude @Arguments 2>&1 | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ }) -join ' | '
    Log "${Label}: $output"
    return ($output -notmatch 'Failed|Error')
}

Log 'update: inicio'
$ok = Run 'marketplace' @('plugin', 'marketplace', 'update', $marketplace)
$installed = (claude plugin list 2>&1 | Out-String) -split "`n" | ForEach-Object { if ($_ -match "([\w-]+)@$marketplace") { $Matches[1] } } | Sort-Object -Unique
if (-not $installed) { Log "plugins: ninguno instalado desde $marketplace" }
foreach ($plugin in $installed) {
    $ok = (Run "plugin $plugin" @('plugin', 'update', "$plugin@$marketplace")) -and $ok
}
Log ('update: ' + $(if ($ok) { 'ok' } else { 'con fallos' }))
exit $(if ($ok) { 0 } else { 1 })
