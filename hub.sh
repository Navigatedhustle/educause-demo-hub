#!/usr/bin/env bash
set -e
ENGINE="$HOME/.local/share/educause-demo-hub"
if ! curl --max-time 2 -fsS http://127.0.0.1:8790/api/status >/dev/null 2>&1; then
  if ! systemctl --user is-active --quiet hp-zgx-demo-hub.service; then
    systemd-run --user --unit=hp-zgx-demo-hub --collect --quiet \
        /usr/bin/python3 "$ENGINE/hub_server.py"
  fi
    for i in $(seq 1 30); do
        curl --max-time 1 -fsS http://127.0.0.1:8790/api/status >/dev/null 2>&1 && break
        sleep .1
    done
fi
curl --max-time 2 -fsS http://127.0.0.1:8790/api/status >/dev/null
exec /usr/bin/python3 "$ENGINE/hub.py"
