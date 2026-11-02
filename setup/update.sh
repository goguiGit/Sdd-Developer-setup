#!/usr/bin/env bash
# Actualiza el marketplace y todos los plugins instalados desde él. Es lo que ejecuta la tarea programada; también se puede lanzar a mano.
# Escribe un log en ~/.claude/sdd-update.log y sale con 1 si Claude Code devolvió un fallo.
set -uo pipefail

marketplace="sdd-developer-setup"
log="$HOME/.claude/sdd-update.log"
mkdir -p "$(dirname "$log")"
note() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$log"; }
ok=0

run() {
  local label="$1"; shift
  local output
  output="$(claude "$@" 2>&1 | tr '\n' ' ')"
  note "$label: $output"
  echo "$output" | grep -qE 'Failed|Error' && ok=1
}

note "update: inicio"
run "marketplace" plugin marketplace update "$marketplace"
installed="$(claude plugin list 2>&1 | grep -oE "[A-Za-z0-9_-]+@$marketplace" | sort -u)"
[ -z "$installed" ] && note "plugins: ninguno instalado desde $marketplace"
for plugin in $installed; do
  run "plugin ${plugin%@*}" plugin update "$plugin"
done
if [ "$ok" -eq 0 ]; then note "update: ok"; else note "update: con fallos"; fi
exit "$ok"
