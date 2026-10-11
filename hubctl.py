#!/usr/bin/env python3
"""Synchronous verified lifecycle for existing shell entrypoints."""
import json
import sys
import time
import urllib.request

action = 'stop' if sys.argv[1] == 'stop' else 'start'
payload = {} if action == 'stop' else {'demo': sys.argv[2]}
request = urllib.request.Request('http://127.0.0.1:8790/api/' + action, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(request, timeout=5) as response:
    generation = json.load(response)['generation']
deadline = time.monotonic() + 300
while time.monotonic() < deadline:
    with urllib.request.urlopen('http://127.0.0.1:8790/api/status', timeout=5) as response:
        state = json.load(response)
    if state['generation'] != generation:
        sys.exit('Transition superseded by another selection')
    if state['phase'] == 'error':
        sys.exit(state['message'])
    if state['phase'] == ('menu' if action == 'stop' else 'running'):
        print(state['message'])
        sys.exit(0)
    time.sleep(.5)
sys.exit('Transition timed out')
