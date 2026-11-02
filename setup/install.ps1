<#
.SYNOPSIS
Instala el plugin sdd en Claude Code y deja las plantillas donde hacen falta. Idempotente.

.EXAMPLE
.\setup\install.ps1                      # plugin + CLAUDE.md global si no existe
.\setup\install.ps1 -Repo C:\src\MiRepo  # además copia CLAUDE.md y docs/ al repo si no los tiene
#>
[CmdletBinding()]
param(
    [string] $Repo,
    [string] $Marketplace = 'goguiGit/Sdd-Developer-setup'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

foreach ($tool in 'claude', 'git', 'python') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Falta '$tool' en el PATH." }
}

Write-Host "== Plugin sdd" -ForegroundColor Cyan
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
    Write-Host "== CLAUDE.md global" -ForegroundColor Cyan
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

Write-Host ''
Write-Host 'Listo. En una sesión de Claude Code dentro del repo: /sdd-change <id> <descripción>' -ForegroundColor Green
