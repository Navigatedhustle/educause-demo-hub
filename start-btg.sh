#!/usr/bin/env bash
set -e

ENGINE="$HOME/.local/share/educause-demo-hub"

if [ "${HUB_TRANSITION_MANAGED:-0}" != "1" ]; then "$ENGINE/stop-all.sh" || exit $?; fi

notify-send "Beat The Guard" "Starting local AI security demo..."

LAUNCHER="$HOME/Desktop/btg-launch.desktop"

if [ ! -f "$LAUNCHER" ]; then
    notify-send -u critical "Beat The Guard" \
    "Beat The Guard launcher could not be found."
    exit 1
fi

gio launch "$LAUNCHER"
