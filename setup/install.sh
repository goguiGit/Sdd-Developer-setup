#!/usr/bin/env bash
# Instala el plugin sdd en Claude Code y deja las plantillas donde hacen falta. Idempotente.
#   ./setup/install.sh                 # plugin + CLAUDE.md global si no existe
#   ./setup/install.sh ~/src/mi-repo   # además copia CLAUDE.md y docs/ al repo si no los tiene
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
repo="${1:-}"
marketplace="${MARKETPLACE:-goguiGit/Sdd-Developer-setup}"

for tool in claude git python3; do
  command -v "$tool" >/dev/null || { echo "Falta '$tool' en el PATH."; exit 1; }
done

echo "== Plugin sdd"
if ! claude plugin marketplace list 2>&1 | grep -q sdd-developer-setup; then
  claude plugin marketplace add "$marketplace"
fi
if claude plugin list 2>&1 | grep -q 'sdd@sdd-developer-setup'; then
  claude plugin update sdd@sdd-developer-setup
else
  claude plugin install sdd@sdd-developer-setup --scope user
fi

global_claude="$HOME/.claude/CLAUDE.md"
if [ ! -f "$global_claude" ]; then
  echo "== CLAUDE.md global"
  mkdir -p "$(dirname "$global_claude")"
  cp "$root/templates/CLAUDE.md" "$global_claude"
  echo "   creado $global_claude; edítalo con lo tuyo"
fi

if [ -n "$repo" ]; then
  echo "== Repo $repo"
  [ -f "$repo/CLAUDE.md" ] || { cp "$root/templates/CLAUDE.md" "$repo/CLAUDE.md"; echo '   CLAUDE.md copiado: rellena los <...>'; }
  [ -d "$repo/docs/features" ] || { mkdir -p "$repo/docs/features"; echo "   creado $repo/docs/features; la primera feature la crea /sdd-change"; }
fi

echo
echo "Listo. En una sesión de Claude Code dentro del repo: /sdd-change <id> <descripción>"
