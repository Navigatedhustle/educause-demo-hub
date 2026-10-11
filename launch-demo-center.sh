#!/usr/bin/env bash
set -e

if [ "${HUB_TRANSITION_MANAGED:-0}" != "1" ]; then "$HOME/.local/share/educause-demo-hub/stop-all.sh" || exit $?; fi

notify-send "HP ZGX Demo Center" "Opening demo center..."

LAUNCHER="$HOME/Desktop/hp-zgx-demo-center.desktop"

if [ ! -f "$LAUNCHER" ]; then
    notify-send -u critical "HP ZGX Demo Center" \
    "Demo Center launcher could not be found."
    exit 1
fi

gio launch "$LAUNCHER"
