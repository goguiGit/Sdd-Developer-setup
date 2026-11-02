<#
.SYNOPSIS
Instala el plugin sdd en Claude Code, deja las plantillas donde hacen falta y programa la actualización diaria. Idempotente.

.EXAMPLE
.\setup\install.ps1                        # plugin + CLAUDE.md global + tarea diaria a las 08:00
.\setup\install.ps1 -UpdateAt 09:30        # misma instalación, actualización a las 09:30
.\setup\install.ps1 -NoSchedule            # sin tarea programada
.\setup\install.ps1 -Repo C:\src\MiRepo    # además copia CLAUDE.md y docs/features al repo si no los tiene
.\setup\install.ps1 -RemoveSchedule        # quita la tarea programada y termina
#>
[CmdletBinding()]
param(
    [string] $Repo,
    [string] $Marketplace = 'goguiGit/Sdd-Developer-setup',
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')]
    [string] $UpdateAt = '08:00',
    [switch] $NoSchedule,
    [switch] $RemoveSchedule
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$taskName = 'Claude sdd plugin update'

if ($RemoveSchedule) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Tarea '$taskName' eliminada." -ForegroundColor Green
    return
}

foreach ($tool in 'claude', 'git', 'python') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Falta '$tool' en el PATH." }
}

Write-Host '== Plugin sdd' -ForegroundColor Cyan
$marketplaces = claude plugin marketplace list 2>&1 | Out-String
if ($marketplaces -notmatch 'sdd-developer-setup') {
    claude plugin marketplace add $Marketplace
}
$plugins = claude plugin list 2>&1 | Out-String
if ($plugins -match 'sdd@sdd-developer-setup') {
    claude plugin update sdd@sdd-developer-setup
}
else {
    claude plugin install sdd@sdd-developer-setup --scope user
}

$globalClaude = Join-Path $HOME '.claude\CLAUDE.md'
if (-not (Test-Path $globalClaude)) {
    Write-Host '== CLAUDE.md global' -ForegroundColor Cyan
    New-Item -ItemType Directory -Force (Split-Path $globalClaude) | Out-Null
    Copy-Item (Join-Path $root 'templates\CLAUDE.md') $globalClaude
    Write-Host "   creado $globalClaude; edítalo con lo tuyo"
}

if ($Repo) {
    Write-Host "== Repo $Repo" -ForegroundColor Cyan
    if (-not (Test-Path (Join-Path $Repo 'CLAUDE.md'))) {
        Copy-Item (Join-Path $root 'templates\CLAUDE.md') (Join-Path $Repo 'CLAUDE.md')
        Write-Host '   CLAUDE.md copiado: rellena los <...>'
    }
    $features = Join-Path $Repo 'docs\features'
    if (-not (Test-Path $features)) {
        New-Item -ItemType Directory -Force $features | Out-Null
        Write-Host "   creado $features; la primera feature la crea /sdd-change"
    }
}

if (-not $NoSchedule) {
    Write-Host "== Actualización diaria a las $UpdateAt" -ForegroundColor Cyan
    $updateScript = Join-Path $PSScriptRoot 'update.ps1'
    $shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { 'pwsh' } else { 'powershell' }
    $action = New-ScheduledTaskAction -Execute $shell -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$updateScript`""
    $trigger = New-ScheduledTaskTrigger -Daily -At $UpdateAt
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Actualiza el plugin sdd de Claude Code desde su marketplace.' -Force | Out-Null
    Write-Host "   tarea '$taskName' registrada; si el equipo está apagado a esa hora, se ejecuta al encenderlo. Log en ~\.claude\sdd-update.log"
}

Write-Host ''
Write-Host 'Listo. En una sesión de Claude Code dentro del repo: /sdd-change <id> <descripción>' -ForegroundColor Green
