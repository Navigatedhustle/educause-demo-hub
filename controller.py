"""One serialized lifecycle for the native menu and local browser companion."""
import concurrent.futures
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
ATLAS = HOME / 'atlas-claude'
CACHE = HOME / '.cache' / 'educause-demo-hub'
CACHE.mkdir(parents=True, exist_ok=True)
DEMOS = {
    'atlas': ('Atlas: Local Executive AI Assistant', 'Ask business and research questions out loud. Answers, charts and proof, fully offline on this Nano.', 'http://localhost:8100', 'start-atlas.sh'),
    'campuscompass': ('CampusCompass', 'Local AI Higher Education Advising', 'http://127.0.0.1:8000', 'start-campuscompass.sh', 'external'),
    'observatory': ('ZGX Research Observatory', 'Local AI Research Experience', 'http://127.0.0.1:8120', 'start-observatory.sh'),
    'btg-player': ('Beat The Guard Player', 'Interactive Local AI Security Challenge', 'http://127.0.0.1/play?station=1', 'start-btg-player.sh'),
    'btg-admin': ('Beat The Guard Admin', 'Operator Dashboard and Game Controls', 'http://127.0.0.1/admin', 'start-btg-admin.sh'),
    'demo-center': ('HP ZGX Demo Center', 'HP Local AI Demo Library', 'http://localhost:8085/zgx-demo-launcher.html', 'start-demo-center.sh'),
}
STAGES = {
    'Language model': 'http://127.0.0.1:8101/health',
    'Speech': 'http://127.0.0.1:8110/health',
    'Decisions': 'http://127.0.0.1:8120/v1/models',
    'Vision': 'http://127.0.0.1:8130/health',
    'Embeddings': 'http://127.0.0.1:8140/health',
    'UI': 'http://127.0.0.1:8100/api/config',
}


def available_gib():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) / 1048576
    raise RuntimeError('Cannot read available memory')


def healthy(url):
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            body = response.read()
        if '/health' in url or '/v1/models' in url or '/api/config' in url:
            data = json.loads(body)
            if not isinstance(data, dict):
                return False
            if '/v1/models' in url:
                return bool(data.get('data') or data.get('models'))
            if '/health' in url:
                return data.get('ok', data.get('status') == 'ok') is True
            return bool(data.get('personas'))
        return bool(body)
    except (OSError, ValueError):
        return False


def atlas_health():
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(STAGES)) as pool:
        return dict(zip(STAGES, pool.map(healthy, STAGES.values())))


def listeners():
    ports = set()
    for filename in ('/proc/net/tcp', '/proc/net/tcp6'):
        for row in Path(filename).read_text().splitlines()[1:]:
            fields = row.split()
            if fields[3] == '0A':
                ports.add(int(fields[1].split(':')[1], 16))
    return ports


def owned_processes(atlas_only=False):
    """Identify exact demo service commands and demo-specific browser profiles."""
    result = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            args = entry.joinpath('cmdline').read_bytes().decode().strip('\0').split('\0')
            if not args[0]:
                continue
            cwd = entry.joinpath('cwd').resolve()
            executable = Path(args[0]).name
            service = executable.startswith('python') or executable in ('uvicorn', 'llama-server', 'nemo-speech')
            atlas = (executable in ('llama-server', 'nemo-speech') and args[0].startswith(str(ATLAS) + '/')) or (executable.startswith('python') and ((cwd == ATLAS and 'atlas.server:app' in args) or any(a in (str(ATLAS / 'atlas/vision_server.py'), str(ATLAS / 'atlas/embed_server.py')) for a in args) or (cwd == ATLAS / 'vendor/kev' and 'kev.serve' in args)))
            if atlas:
                result.append(int(entry.name))
                continue
            if atlas_only:
                continue
            obs = HOME / 'HP_ZGX_Research_Observatory_V4' / 'zgx-research-observatory-v04'
            demos = (HOME / 'demos').resolve()
            demo_server = service and ((cwd == obs and 'app:app' in args) or (cwd == demos and ('http.server' in args or any(a.endswith('demo_install_server.py') for a in args))))
            profiles = [str(CACHE / p) for p in ('chromium', 'campuscompass-chromium')] + [str(obs / 'data/chromium-profile'), str(HOME / 'zgx-demo-center-chrome'), str(HOME / 'snap/chromium/common/btg-admin'), str(HOME / 'snap/chromium/common/hp-zgx-nano-campuscompass')]
            browser = executable in ('chrome', 'chromium', 'chrome_crashpad_handler') and (any(a == '--user-data-dir=' + p for p in profiles for a in args) or any(a.startswith('http://127.0.0.1/play') or a == 'http://127.0.0.1/board' for a in args))
            watchdog = any(a == str(HOME / 'Projects/BeatTheGuard/scripts/board_kiosk.sh') for a in args)
            if demo_server or browser or watchdog:
                result.append(int(entry.name))
        except (OSError, UnicodeError, IndexError):
            pass
    return result


def terminate(pids, sig=signal.SIGTERM):
    for pid in pids:
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            pass


class Controller:
    def __init__(self):
        self.lock = threading.RLock()
        self.transition = threading.Lock()
        self.cancel = threading.Event()
        self.generation = 0
        self.baseline = None
        self.child = None
        self.state = dict(phase='menu', demo=None, message='Nano ready', stages={}, started=None, log_tail='', generation=0)

    def update(self, **kwargs):
        with self.lock:
            self.state.update(kwargs)

    def snapshot(self):
        with self.lock:
            state = self.state.copy()
        state['elapsed'] = round(time.monotonic() - state['started'], 1) if state['started'] else 0
        state['available_gib'] = round(available_gib(), 2)
        return state

    def request(self, demo=None):
        if demo is not None and demo not in DEMOS:
            raise ValueError('Unknown demo')
        with self.lock:
            if demo and self.state['demo'] == demo and self.state['phase'] in ('starting', 'running'):
                return self.snapshot()
            if demo is None and self.state['phase'] == 'stopping':
                return self.snapshot()
            self.cancel.set()
            self.cancel = threading.Event()
            event = self.cancel
            self.generation += 1
            generation = self.generation
            self.update(phase='starting' if demo else 'stopping', demo=demo, message='Preparing workload...' if demo else 'Clearing current workload...', stages={}, started=time.monotonic(), log_tail='', generation=generation)
            threading.Thread(target=self.run, args=(demo, event, generation), daemon=True).start()
        return self.snapshot()

    def command(self, args, timeout=45):
        with (CACHE / 'transition.log').open('a') as log:
            result = subprocess.run(args, stdout=log, stderr=log, timeout=timeout)
        if result.returncode:
            raise RuntimeError(f'Could not complete {Path(args[0]).name}. See transition.log.')

    def stop_resources(self):
        atlas_was_up = bool(owned_processes(True))
        # Stop any still-active launcher BEFORE stop.sh so it cannot restart services.
        if self.child and self.child.poll() is None:
            os.killpg(self.child.pid, signal.SIGTERM)
            try:
                self.child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(self.child.pid, signal.SIGKILL)
                self.child.wait(timeout=3)
        self.child = None
        self.command([str(ATLAS / 'stop.sh')], timeout=45)
        terminate(owned_processes())
        # These are the existing hub demos; no global kill or port-based kill.
        self.command(['systemctl', '--no-ask-password', 'stop', 'btg-app.service', 'btg-model.service'])
        units = subprocess.check_output(['systemctl', '--user', 'list-unit-files', '--type=service', '--no-legend'], text=True)
        targets = [line.split()[0] for line in units.splitlines() if line.startswith(('campuscompass-', 'jarvis-'))]
        if targets:
            self.command(['systemctl', '--user', 'stop', *targets], timeout=60)
        self.command(['docker', 'stop', '-t', '3', 'btg-sentinel']) if 'btg-sentinel' in subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines() else None
        deadline = time.monotonic() + 30
        threshold = max(50, self.baseline - 2) if atlas_was_up and self.baseline else 50 if atlas_was_up else 0
        ports = pids = []
        while time.monotonic() < deadline:
            pids = owned_processes()
            busy = listeners()
            ports = sorted(p for p in busy if 8100 <= p <= 8199 or p in (80, 8000, 8001, 8081, 8082, 8083, 8085, 8086, 3100))
            if not pids and not ports and available_gib() >= threshold:
                self.baseline = None
                return
            if deadline - time.monotonic() < 25:
                terminate(pids, signal.SIGKILL)
            time.sleep(.5)
        raise RuntimeError(f'Stop verification failed: ports {ports}, demo processes {pids}, available memory {available_gib():.1f} GiB (need {threshold:.1f}).')

    def run(self, demo, cancel, generation):
        def publish(**kwargs):
            with self.lock:
                if self.generation == generation:
                    self.state.update(kwargs)
        with self.transition:
            if cancel.is_set():
                return
            try:
                if demo == 'atlas' and all(atlas_health().values()):
                    publish(phase='running', message='Atlas already running — ready', stages=atlas_health())
                    return
                self.stop_resources()
                if cancel.is_set():
                    return
                if demo is None:
                    publish(phase='menu', demo=None, message='Nano cleared. Ready for next demo.', started=None)
                    return
                publish(message='Waiting for available memory...')
                deadline = time.monotonic() + 60
                while available_gib() < 50:
                    if cancel.wait(.5):
                        return
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f'Not enough memory to start: {available_gib():.1f} GiB available; need 50 GiB. Stop other workloads and Retry.')
                self.baseline = available_gib() if demo == 'atlas' else None
                log_path = CACHE / f'{demo}-start.log'
                env = dict(os.environ, HUB_TRANSITION_MANAGED='1', HUB_NO_BROWSER='1')
                with log_path.open('w') as log:
                    script = ATLAS / 'start.sh' if demo == 'atlas' else ROOT / DEMOS[demo][3]
                    self.child = subprocess.Popen([str(script)], cwd=ATLAS if demo == 'atlas' else ROOT, env=env, stdout=log, stderr=log, start_new_session=True)
                publish(message='Loading local services...', started=time.monotonic())
                deadline = time.monotonic() + 180
                while time.monotonic() < deadline:
                    if cancel.is_set():
                        return
                    stages = atlas_health() if demo == 'atlas' else {'UI': healthy(DEMOS[demo][2])}
                    # BTG must have its real model ready, not just an HTTP shell.
                    if demo.startswith('btg-'):
                        stages['Language model'] = healthy('http://127.0.0.1:8001/v1/models')
                    publish(stages=stages)
                    launcher_ready = demo not in ('campuscompass', 'demo-center') or self.child.poll() == 0
                    if all(stages.values()) and launcher_ready:
                        publish(phase='running', message=f'{DEMOS[demo][0]} ready')
                        return
                    if self.child.poll() not in (None, 0):
                        raise RuntimeError('Startup failed. Check the log below and Retry.')
                    if cancel.wait(.5):
                        return
                raise RuntimeError('This demo did not become ready within 180 seconds. Check the log below and Retry.')
            except Exception as error:
                if cancel.is_set():
                    return
                log_path = CACHE / f'{demo}-start.log'
                tail = '\n'.join(log_path.read_text(errors='replace').splitlines()[-20:]) if log_path.exists() else ''
                # Failed startups cannot keep allocating memory after displaying error.
                try:
                    self.stop_resources()
                except Exception as cleanup_error:
                    error = RuntimeError(f'{error} Cleanup: {cleanup_error}')
                publish(phase='error', message=str(error), log_tail=tail)
