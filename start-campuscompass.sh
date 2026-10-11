#!/usr/bin/env bash

set -u

ENGINE="$HOME/.local/share/educause-demo-hub"
CC="$HOME/Projects/CampusCompass"
LOG="$HOME/.cache/educause-demo-hub/campuscompass-start.log"

mkdir -p "$(dirname "$LOG")"

if [ "${HUB_TRANSITION_MANAGED:-0}" != "1" ]; then "$ENGINE/stop-all.sh" || exit $?; fi

exec >"$LOG" 2>&1

echo "======================================"
echo "CampusCompass startup: $(date)"
echo "======================================"

notify-send "CampusCompass" "Preparing local AI workload..."

cd "$CC" || exit 1

# Make sure old failed states do not block restart
systemctl --user reset-failed \
    campuscompass-model.service \
    campuscompass-embedding.service \
    campuscompass-reranker.service \
    campuscompass-app.service \
    >/dev/null 2>&1 || true

systemctl --user daemon-reload

# Wait briefly for BTG ports/resources to fully disappear
for i in $(seq 1 15); do
    if ! ss -ltn 2>/dev/null | grep -Eq ':(80|8001)\b'; then
        break
    fi
    echo "Waiting for BTG teardown..."
    sleep 1
done

echo "Starting CampusCompass services..."

systemctl --user start campuscompass-model.service
systemctl --user start campuscompass-embedding.service
systemctl --user start campuscompass-reranker.service
systemctl --user start campuscompass-app.service

echo
echo "Service state:"
systemctl --user is-active \
    campuscompass-model.service \
    campuscompass-embedding.service \
    campuscompass-reranker.service \
    campuscompass-app.service

notify-send "CampusCompass" "Models loading..."

if timeout 90s .venv/bin/python scripts/wait-health.py; then
    echo "Health check passed."
else
    echo "HEALTH CHECK FAILED"

    systemctl --user status \
        campuscompass-model.service \
        campuscompass-embedding.service \
        campuscompass-reranker.service \
        campuscompass-app.service \
        --no-pager -l

    notify-send -u critical \
        "CampusCompass" \
        "Startup failed. Check CampusCompass log."

    exit 1
fi

if ! curl -fsS http://127.0.0.1:8000 >/dev/null 2>&1; then
    echo "Port 8000 failed final validation."
    notify-send -u critical "CampusCompass" "App failed final validation."
    exit 1
fi

echo "CampusCompass ready: $(date)"

notify-send "CampusCompass" "Ready."


[ "${HUB_NO_BROWSER:-0}" = "1" ] && exit 0

# Use an isolated Chromium profile so BTG cannot interfere
PROFILE="$HOME/.cache/educause-demo-hub/campuscompass-chromium"

mkdir -p "$PROFILE"
chmod 700 "$PROFILE"

rm -f \
"$PROFILE/SingletonLock" \
"$PROFILE/SingletonSocket" \
"$PROFILE/SingletonCookie" \
2>/dev/null || true

/snap/bin/chromium \
    --user-data-dir="$PROFILE" \
    --no-first-run \
    --no-default-browser-check \
    --app=http://127.0.0.1:8000 \
    >/dev/null 2>&1 &

exit 0
