<#
.SYNOPSIS
Instala el plugin sdd en Claude Code, prepara un repo si se indica y programa la actualización diaria. Idempotente.

.EXAMPLE
.\setup\install.ps1                        # plugin + actualización diaria a las 08:00
.\setup\install.ps1 -UpdateAt 09:30        # misma instalación, actualización a las 09:30
.\setup\install.ps1 -WithLibraries         # además el plugin libraries (skills de librerías)
.setupinstall.ps1 -Tracker AzureDevOps -Organization miorg   # MCP de Azure DevOps para leer tickets y crear tareas
.setupinstall.ps1 -Tracker Jira        # MCP remoto de Atlassian (OAuth en el navegador la primera vez)
.\setup\install.ps1 -NoSchedule            # sin tarea programada
.\setup\install.ps1 -Repo C:\src\MiRepo    # además AGENTS.md, CLAUDE.md y docs/features en el repo si no los tiene
.\setup\install.ps1 -RemoveSchedule        # quita la tarea programada y termina
#>
[CmdletBinding()]
param(
    [string] $Repo,
    [string] $Marketplace = 'goguiGit/Sdd-Developer-setup',
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')]
    [string] $UpdateAt = '08:00',
    [ValidateSet('None', 'AzureDevOps', 'Jira')]
    [string] $Tracker = 'None',
    [string] $Organization,
    [switch] $WithLibraries,
    [switch] $NoSchedule,
    [switch] $RemoveSchedule
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$marketplaceName = 'sdd-developer-setup'
$taskName = 'Claude sdd plugin update'

if ($RemoveSchedule) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Tarea '$taskName' eliminada." -ForegroundColor Green
    return
}

foreach ($tool in 'claude', 'git', 'python') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Falta '$tool' en el PATH." }
}

function Install-Plugin([string] $Name) {
    $plugins = claude plugin list 2>&1 | Out-String
    if ($plugins -match "$Name@$marketplaceName") { claude plugin update "$Name@$marketplaceName" }
    else { claude plugin install "$Name@$marketplaceName" --scope user }
}

Write-Host '== Marketplace y plugins' -ForegroundColor Cyan
$marketplaces = claude plugin marketplace list 2>&1 | Out-String
if ($marketplaces -notmatch $marketplaceName) { claude plugin marketplace add $Marketplace }
Install-Plugin 'sdd'
if ($WithLibraries) { Install-Plugin 'libraries' }

if ($Tracker -ne 'None') {
    Write-Host "== Gestor de tareas: $Tracker" -ForegroundColor Cyan
    $servers = claude mcp list 2>&1 | Out-String
    if ($Tracker -eq 'AzureDevOps') {
        if (-not $Organization) { throw '-Tracker AzureDevOps necesita -Organization <nombre de la organización>.' }
        if ($servers -notmatch 'azure-devops') { claude mcp add --scope user azure-devops -- npx -y @azure-devops/mcp $Organization }
        else { Write-Host '   azure-devops ya registrado' }
    }
    else {
        if ($servers -notmatch 'atlassian') { claude mcp add --transport sse --scope user atlassian https://mcp.atlassian.com/v1/sse }
        else { Write-Host '   atlassian ya registrado' }
    }
}

if ($Repo) {
    Write-Host "== Repo $Repo" -ForegroundColor Cyan
    foreach ($name in 'AGENTS.md', 'CLAUDE.md') {
        if (-not (Test-Path (Join-Path $Repo $name))) {
            Copy-Item (Join-Path $root "templates\$name") (Join-Path $Repo $name)
            Write-Host "   $name copiado"
        }
    }
    Write-Host '   rellena los <...> de AGENTS.md'
    $features = Join-Path $Repo 'docs\features'
    if (-not (Test-Path $features)) {
        New-Item -ItemType Directory -Force $features | Out-Null
        Write-Host "   creado $features; la primera feature la crea /sdd"
    }
}

if (-not $NoSchedule) {
    Write-Host "== Actualización diaria a las $UpdateAt" -ForegroundColor Cyan
    $updateScript = Join-Path $PSScriptRoot 'update.ps1'
    $shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { 'pwsh' } else { 'powershell' }
    $action = New-ScheduledTaskAction -Execute $shell -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$updateScript`""
    $trigger = New-ScheduledTaskTrigger -Daily -At $UpdateAt
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Actualiza los plugins de Claude Code del marketplace sdd-developer-setup.' -Force | Out-Null
    Write-Host "   tarea '$taskName' registrada; si el equipo está apagado a esa hora, se ejecuta al encenderlo. Log en ~\.claude\sdd-update.log"
}

Write-Host ''
Write-Host 'Listo. En una sesión de Claude Code dentro del repo: /sdd <id> <descripción>' -ForegroundColor Green
