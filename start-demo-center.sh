#!/usr/bin/env bash
set -e

if [ "${HUB_TRANSITION_MANAGED:-0}" != "1" ]; then "$HOME/.local/share/educause-demo-hub/stop-all.sh" || exit $?; fi

notify-send "HP ZGX Demo Center" "Opening demo center..."

if [ "${HUB_NO_BROWSER:-0}" = "1" ]; then
    exec "$HOME/zgx-demo-center-bundle/demos/start_demo_center.sh" --check
fi
gio launch "$HOME/Desktop/hp-zgx-demo-center.desktop"
