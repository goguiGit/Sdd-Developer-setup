#!/usr/bin/env bash
# Instala el plugin sdd en Claude Code, prepara un repo si se indica y programa la actualización diaria. Idempotente.
#   ./setup/install.sh                      # plugin + actualización diaria a las 08:00
#   UPDATE_AT=09:30 ./setup/install.sh      # actualización a las 09:30
#   WITH_LIBRARIES=1 ./setup/install.sh     # además el plugin libraries (skills de librerías)
#   TRACKER=AzureDevOps ADO_ORG=miorg ./setup/install.sh   # MCP de Azure DevOps para leer tickets y crear tareas
#   TRACKER=Jira ./setup/install.sh         # MCP remoto de Atlassian (OAuth en el navegador la primera vez)
#   NO_SCHEDULE=1 ./setup/install.sh        # sin tarea programada
#   ./setup/install.sh ~/src/mi-repo        # además AGENTS.md, CLAUDE.md y docs/features en el repo si no los tiene
#   ./setup/install.sh --remove-schedule    # quita la tarea programada y termina
# macOS: LaunchAgent (~/Library/LaunchAgents/com.sdd.plugin-update.plist); si el Mac dormía a esa hora, corre al despertar.
# Linux: línea de crontab marcada con "# claude-sdd-plugin-update".
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
marketplace="${MARKETPLACE:-goguiGit/Sdd-Developer-setup}"
marketplace_name="sdd-developer-setup"
update_at="${UPDATE_AT:-08:00}"
marker="# claude-sdd-plugin-update"
label="com.sdd.plugin-update"
plist="$HOME/Library/LaunchAgents/$label.plist"
is_mac() { [ "$(uname -s)" = "Darwin" ]; }

remove_schedule() {
  if is_mac; then
    launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || true
    rm -f "$plist"
    echo "LaunchAgent $label eliminado."
  else
    (crontab -l 2>/dev/null | grep -v "$marker" || true) | crontab -
    echo "Cron de actualización eliminado."
  fi
}

install_plugin() {
  if claude plugin list 2>&1 | grep -q "$1@$marketplace_name"; then claude plugin update "$1@$marketplace_name"
  else claude plugin install "$1@$marketplace_name" --scope user; fi
}

schedule() {
  [[ "$update_at" =~ ^([01][0-9]|2[0-3]):([0-5][0-9])$ ]] || { echo "UPDATE_AT debe ser HH:MM"; exit 1; }
  local hour="${BASH_REMATCH[1]#0}" minute="${BASH_REMATCH[2]#0}"
  hour="${hour:-0}"; minute="${minute:-0}"
  if is_mac; then
    mkdir -p "$(dirname "$plist")"
    cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$root/setup/update.sh</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$PATH</string></dict>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>$hour</integer><key>Minute</key><integer>$minute</integer></dict>
  <key>StandardOutPath</key><string>$HOME/.claude/sdd-update.launchd.log</string>
  <key>StandardErrorPath</key><string>$HOME/.claude/sdd-update.launchd.log</string>
</dict>
</plist>
EOF
    launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$plist"
    echo "   LaunchAgent $label registrado ($update_at); si el Mac estaba dormido, corre al despertar. Log en ~/.claude/sdd-update.log"
  else
    local entry="$minute $hour * * * PATH=\"$PATH\" \"$root/setup/update.sh\" >/dev/null 2>&1 $marker"
    (crontab -l 2>/dev/null | grep -v "$marker" || true; echo "$entry") | crontab -
    echo "   cron registrado ($update_at); log en ~/.claude/sdd-update.log"
  fi
}

if [ "${1:-}" = "--remove-schedule" ]; then remove_schedule; exit 0; fi
repo="${1:-}"

for tool in claude git python3; do
  command -v "$tool" >/dev/null || { echo "Falta '$tool' en el PATH."; exit 1; }
done

echo "== Marketplace y plugins"
claude plugin marketplace list 2>&1 | grep -q "$marketplace_name" || claude plugin marketplace add "$marketplace"
install_plugin sdd
[ -n "${WITH_LIBRARIES:-}" ] && install_plugin libraries

case "${TRACKER:-None}" in
  AzureDevOps)
    echo "== Gestor de tareas: Azure DevOps"
    [ -n "${ADO_ORG:-}" ] || { echo "TRACKER=AzureDevOps necesita ADO_ORG=<nombre de la organización>"; exit 1; }
    if claude mcp list 2>&1 | grep -q azure-devops; then echo "   azure-devops ya registrado"
    else claude mcp add --scope user azure-devops -- npx -y @azure-devops/mcp "$ADO_ORG"; fi ;;
  Jira)
    echo "== Gestor de tareas: Jira"
    if claude mcp list 2>&1 | grep -q atlassian; then echo "   atlassian ya registrado"
    else claude mcp add --transport sse --scope user atlassian https://mcp.atlassian.com/v1/sse; fi ;;
  None) ;;
  *) echo "TRACKER debe ser AzureDevOps o Jira"; exit 1 ;;
esac

if [ -n "$repo" ]; then
  echo "== Repo $repo"
  for name in AGENTS.md CLAUDE.md sdd.json; do
    [ -f "$repo/$name" ] || { cp "$root/templates/$name" "$repo/$name"; echo "   $name copiado"; }
  done
  echo "   rellena los <...> de AGENTS.md"
  [ -d "$repo/docs/features" ] || { mkdir -p "$repo/docs/features"; echo "   creado $repo/docs/features; la primera feature la crea /sdd"; }
fi

if [ -z "${NO_SCHEDULE:-}" ]; then
  echo "== Actualización diaria a las $update_at"
  schedule
fi

echo
echo "Listo. En una sesión de Claude Code dentro del repo: /sdd <id> <descripción>"
