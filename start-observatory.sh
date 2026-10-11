#!/usr/bin/env bash
set -e

ENGINE="$HOME/.local/share/educause-demo-hub"

if [ "${HUB_TRANSITION_MANAGED:-0}" != "1" ]; then "$ENGINE/stop-all.sh" || exit $?; fi

notify-send "ZGX Research Observatory" "Starting demo..."

if [ "${HUB_NO_BROWSER:-0}" = "1" ]; then
    cd "$HOME/HP_ZGX_Research_Observatory_V4/zgx-research-observatory-v04"
    exec "$HOME/miniforge3/envs/zgx/bin/python" -m uvicorn app:app --host 127.0.0.1 --port 8120 --no-access-log
fi
gio launch "$HOME/Desktop/hp-zgx-research-observatory-v04.desktop"
