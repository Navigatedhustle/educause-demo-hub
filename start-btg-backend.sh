#!/usr/bin/env bash
set -e

notify-send "Beat The Guard" "Loading local AI security model..."

if ! systemctl --no-ask-password start \
    btg-model.service \
    btg-app.service
then
    notify-send -u critical "Beat The Guard" \
    "Could not start BTG services."
    exit 1
fi

# Wait for the web application
for i in $(seq 1 90); do
    if curl -fsS http://127.0.0.1/api/board >/dev/null 2>&1; then
        notify-send "Beat The Guard" "Backend ready."
        exit 0
    fi

    sleep 1
done

notify-send -u critical "Beat The Guard" \
"BTG backend did not become ready."
exit 1
