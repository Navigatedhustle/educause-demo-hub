#!/usr/bin/env bash
set -e
ENGINE="$HOME/.local/share/educause-demo-hub"
if [ "${HUB_TRANSITION_MANAGED:-0}" != "1" ]; then
    exec /usr/bin/python3 "$ENGINE/hubctl.py" start btg-player
fi
exec "$ENGINE/start-btg-backend.sh"
