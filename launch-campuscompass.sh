#!/usr/bin/env bash
set -e

if [ "${HUB_TRANSITION_MANAGED:-0}" != "1" ]; then "$HOME/.local/share/educause-demo-hub/stop-all.sh" || exit $?; fi

cd "$HOME/Projects/CampusCompass"

notify-send "CampusCompass" "Starting local models and advising app..."

systemctl --user start \
campuscompass-model.service \
campuscompass-embedding.service \
campuscompass-reranker.service \
campuscompass-app.service

if [ -x ".venv/bin/python" ] && [ -f "scripts/wait-health.py" ]; then
    .venv/bin/python scripts/wait-health.py
else
    for i in $(seq 1 60); do
        if curl -fsS http://127.0.0.1:8000 >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
fi

if curl -fsS http://127.0.0.1:8000 >/dev/null 2>&1; then
    notify-send "CampusCompass" "Ready."
    xdg-open http://127.0.0.1:8000
else
    notify-send -u critical "CampusCompass" \
    "CampusCompass did not become ready."
    exit 1
fi
