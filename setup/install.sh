#!/usr/bin/env bash
# Instala el plugin sdd en Claude Code, deja las plantillas donde hacen falta y programa la actualización diaria. Idempotente.
#   ./setup/install.sh                      # plugin + CLAUDE.md global + cron diario a las 08:00
#   UPDATE_AT=09:30 ./setup/install.sh      # actualización a las 09:30
#   NO_SCHEDULE=1 ./setup/install.sh        # sin cron
#   ./setup/install.sh ~/src/mi-repo        # además copia CLAUDE.md y docs/features al repo si no los tiene
#   ./setup/install.sh --remove-schedule    # quita el cron y termina
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
marketplace="${MARKETPLACE:-goguiGit/Sdd-Developer-setup}"
update_at="${UPDATE_AT:-08:00}"
marker="# claude-sdd-plugin-update"

remove_schedule() {
  (crontab -l 2>/dev/null | grep -v "$marker" || true) | crontab -
  echo "Cron de actualización eliminado."
}

if [ "${1:-}" = "--remove-schedule" ]; then remove_schedule; exit 0; fi
repo="${1:-}"

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

if [ -z "${NO_SCHEDULE:-}" ]; then
  echo "== Actualización diaria a las $update_at"
  [[ "$update_at" =~ ^([01][0-9]|2[0-3]):([0-5][0-9])$ ]] || { echo "UPDATE_AT debe ser HH:MM"; exit 1; }
  hour="${BASH_REMATCH[1]#0}"; minute="${BASH_REMATCH[2]#0}"
  entry="${minute:-0} ${hour:-0} * * * PATH=\"$PATH\" \"$root/setup/update.sh\" >/dev/null 2>&1 $marker"
  (crontab -l 2>/dev/null | grep -v "$marker" || true; echo "$entry") | crontab -
  echo "   cron registrado; log en ~/.claude/sdd-update.log. En macOS, si el cron no corre, dale a cron 'Full Disk Access' o usa el plugin update a mano."
fi

echo
echo "Listo. En una sesión de Claude Code dentro del repo: /sdd-change <id> <descripción>"
