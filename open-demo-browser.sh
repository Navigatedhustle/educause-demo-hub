#!/usr/bin/env bash
set -e

URL="$1"
PROFILE="$HOME/snap/chromium/common/hp-zgx-nano-hub"
if [ "$URL" = "http://127.0.0.1:8000" ]; then
    PROFILE="$HOME/snap/chromium/common/hp-zgx-nano-campuscompass"
fi

mkdir -p "$PROFILE"
for hub_browser_pid in $(pgrep -f -- "--user-data-dir=$PROFILE" || true); do
    hub_browser_window=$(wmctrl -lp | awk -v hub_pid="$hub_browser_pid" '$3 == hub_pid { print $1; exit }')
    if [ -n "$hub_browser_window" ]; then
        wmctrl -i -a "$hub_browser_window"
        exit 0
    fi
done

chromium \
    --user-data-dir="$PROFILE" \
    --no-first-run \
    --no-default-browser-check \
    --autoplay-policy=no-user-gesture-required \
    --app="$URL" \
    >/dev/null 2>&1 &
