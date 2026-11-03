<#
.SYNOPSIS
Instala el plugin sdd en Claude Code, prepara un repo si se indica y programa la actualización diaria. Idempotente.

.EXAMPLE
.\setup\install.ps1                        # plugin + actualización diaria a las 08:00
.\setup\install.ps1 -UpdateAt 09:30        # misma instalación, actualización a las 09:30
.\setup\install.ps1 -WithLibraries         # además el plugin libraries (skills de librerías)
.\setup\install.ps1 -Tracker AzureDevOps -Organization miorg   # MCP de Azure DevOps para leer tickets y crear tareas
.\setup\install.ps1 -Tracker Jira        # MCP remoto de Atlassian (OAuth en el navegador la primera vez)
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

function Invoke-Claude([string[]] $Arguments) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & claude @Arguments 2>&1 | Out-String } finally { $ErrorActionPreference = $previous }
}

function Install-Plugin([string] $Name) {
    $plugins = Invoke-Claude plugin, list
    if ($plugins -match "$Name@$marketplaceName") { claude plugin update "$Name@$marketplaceName" }
    else { claude plugin install "$Name@$marketplaceName" --scope user }
}

Write-Host '== Marketplace y plugins' -ForegroundColor Cyan
$marketplaces = Invoke-Claude plugin, marketplace, list
if ($marketplaces -notmatch $marketplaceName) { claude plugin marketplace add $Marketplace }
Install-Plugin 'sdd'
if ($WithLibraries) { Install-Plugin 'libraries' }

if ($Tracker -ne 'None') {
    Write-Host "== Gestor de tareas: $Tracker" -ForegroundColor Cyan
    $servers = Invoke-Claude mcp, list
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
    $templates = @{
        'AGENTS.md' = Join-Path $root 'templates\AGENTS.md'
        'CLAUDE.md' = Join-Path $root 'templates\CLAUDE.md'
        'sdd.json'  = Join-Path $root 'plugins\sdd\templates\sdd.json'
    }
    foreach ($name in $templates.Keys) {
        if (-not (Test-Path (Join-Path $Repo $name))) {
            Copy-Item $templates[$name] (Join-Path $Repo $name)
            Write-Host "   $name copiado"
        }
    }
    Write-Host '   rellena los <...> de AGENTS.md y activa los lenguajes con /sdd-languages use <lang>'
    $features = Join-Path $Repo 'docs\features'
    if (-not (Test-Path $features)) {
        New-Item -ItemType Directory -Force $features | Out-Null
        Write-Host "   creado $features; la primera feature la crea /sdd"
    }
    python -I (Join-Path $root 'plugins\sdd\scripts\sdd.py') index (Join-Path $Repo 'docs') | Out-Null
    Write-Host '   índices generados en docs/features (INDEX.md, REQ-INDEX.md)'
}

if (-not $NoSchedule) {
    Write-Host "== Actualización diaria a las $UpdateAt" -ForegroundColor Cyan
    $updateScript = Join-Path $PSScriptRoot 'update.ps1'
    $shellCommand = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not $shellCommand) { $shellCommand = Get-Command powershell }
    $shell = $shellCommand.Source
    $action = New-ScheduledTaskAction -Execute $shell -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$updateScript`""
    $trigger = New-ScheduledTaskTrigger -Daily -At $UpdateAt
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Actualiza los plugins de Claude Code del marketplace sdd-developer-setup.' -Force | Out-Null
    Write-Host "   tarea '$taskName' registrada; si el equipo está apagado a esa hora, se ejecuta al encenderlo. Log en ~\.claude\sdd-update.log"
}

Write-Host ''
Write-Host 'Listo. Reinicia Claude Code si estaba abierto; después, dentro del repo: /sdd <id> <descripción>' -ForegroundColor Green
