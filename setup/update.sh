#!/usr/bin/env bash
# Actualiza el marketplace y el plugin sdd. Es lo que ejecuta el cron; también se puede lanzar a mano.
# Escribe un log en ~/.claude/sdd-update.log.
set -uo pipefail

log="$HOME/.claude/sdd-update.log"
mkdir -p "$(dirname "$log")"
note() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$log"; }

note "update: inicio"
note "marketplace: $(claude plugin marketplace update sdd-developer-setup 2>&1 | tr '\n' ' ')"
note "plugin: $(claude plugin update sdd@sdd-developer-setup 2>&1 | tr '\n' ' ')"
note "update: fin"
