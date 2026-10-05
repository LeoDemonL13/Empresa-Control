#!/usr/bin/env bash
set -uo pipefail

. /opt/nexus/scripts/lib.sh

url=$(leer_env HEARTBEAT_URL)
[ -n "$url" ] || exit 0

sano=1
salud_ok || sano=0
tunel_ok || sano=0

uso_disco=$(df --output=pcent / | tail -n 1 | tr -dc '0-9')
if [ "${uso_disco:-0}" -ge 90 ]; then
    sano=0
fi

if [ "$sano" -eq 1 ]; then
    curl -fsS -m 10 --retry 2 "$url" >/dev/null 2>&1 || true
else
    curl -fsS -m 10 --retry 2 "${url%/}/fail" >/dev/null 2>&1 || true
fi
