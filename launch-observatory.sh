#!/usr/bin/env bash
set -e

if [ "${HUB_TRANSITION_MANAGED:-0}" != "1" ]; then "$HOME/.local/share/educause-demo-hub/stop-all.sh" || exit $?; fi

notify-send "ZGX Research Observatory" "Starting demo..."

LAUNCHER="$HOME/Desktop/hp-zgx-research-observatory-v04.desktop"

if [ ! -f "$LAUNCHER" ]; then
    notify-send -u critical "ZGX Research Observatory" \
    "v04 desktop launcher could not be found."
    exit 1
fi

gio launch "$LAUNCHER"
