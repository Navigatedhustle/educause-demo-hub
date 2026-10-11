#!/usr/bin/env python3

import os
import subprocess
import json
import threading
import urllib.request
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GdkPixbuf
from controller import DEMOS

HOME = os.path.expanduser("~")
ENGINE = os.path.join(HOME, ".local", "share", "educause-demo-hub")


class DemoHub(Gtk.Window):

    def __init__(self):
        super().__init__(title="HP ZGX Nano Demo Hub")

        self.set_default_size(760, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(30)

        main = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16
        )
        self.add(main)

        # Header
        title = Gtk.Label()
        title.set_markup(
            "<span size='26000' weight='bold'>HP ZGX NANO</span>"
        )
        main.pack_start(title, False, False, 0)

        subtitle = Gtk.Label()
        subtitle.set_markup(
            "<span size='16000'>HP ZGX Nano Demo Hub</span>"
        )
        main.pack_start(subtitle, False, False, 0)

        description = Gtk.Label(
            label=(
                "One system. Multiple local AI workloads.\n"
                "Choose the experience you want to demonstrate."
            )
        )
        description.set_justify(Gtk.Justification.CENTER)
        main.pack_start(description, False, False, 8)

        self.status = Gtk.Label()
        self.status.set_markup(
            "<b>Status:</b> Nano ready"
        )
        main.pack_start(self.status, False, False, 6)

        # Demo buttons
        self.buttons = []
        for demo, details in DEMOS.items():
            name, description, url, script = details[:4]
            self.add_button(main, name, description, demo)

        self.stages = Gtk.Label()
        self.stages.set_line_wrap(True)
        main.pack_start(self.stages, False, False, 0)
        self.retry = Gtk.Button(label="Retry")
        self.retry.set_no_show_all(True)
        self.retry.connect('clicked', lambda b: self.launch(b, self.retry_demo, 'Retrying...'))
        main.pack_start(self.retry, False, False, 0)
        self.opened = None
        self.retry_demo = None

        # Stop button
        stop = Gtk.Button()
        stop.set_size_request(-1, 62)

        stop_label = Gtk.Label()
        stop_label.set_markup(
            "<span size='14000' weight='bold'>■ STOP CURRENT DEMO</span>"
        )

        stop.add(stop_label)
        stop.connect(
            "clicked",
            self.launch,
            None,
            "Clearing current workload..."
        )

        main.pack_start(stop, False, False, 8)

        footer = Gtk.Label()
        footer.set_markup(
            "<small>"
            "Local AI • One workload at a time • HP ZGX Nano"
            "</small>"
        )
        main.pack_end(footer, False, False, 0)
        GLib.timeout_add(500, self.poll)

    def add_button(self, container, name, description, script):

        button = Gtk.Button()
        button.set_size_request(-1, 78)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=3
        )

        name_label = Gtk.Label()
        name_label.set_markup(
            f"<span size='15500' weight='bold'>{name}</span>"
        )

        desc_label = Gtk.Label(label=description)

        box.pack_start(name_label, True, True, 0)
        box.pack_start(desc_label, True, True, 0)

        if script == 'atlas':
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            image = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(ENGINE, 'atlas.png'), 96, 54, True))
            row.pack_start(image, False, False, 10)
            row.pack_start(box, True, True, 0)
            button.add(row)
        else:
            button.add(box)

        button.connect(
            "clicked",
            self.launch,
            script,
            f"Switching to {name}..."
        )

        container.pack_start(button, False, False, 0)
        self.buttons.append(button)

    def launch(self, button, script, message):

        self.status.set_text('Status: ' + message)
        def request():
            try:
                data = {'demo': script} if script else {}
                req = urllib.request.Request('http://127.0.0.1:8790/api/' + ('start' if script else 'stop'), data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req, timeout=3).close()
            except Exception as error:
                GLib.idle_add(self.status.set_text, 'Status: ' + str(error))
        threading.Thread(target=request, daemon=True).start()

    def poll(self):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8790/api/status', timeout=.2) as response:
                state = json.load(response)
            self.status.set_text('Status: ' + state['message'])
            busy = state['phase'] in ('starting', 'stopping')
            for button in self.buttons:
                button.set_sensitive(not busy)
            progress = '   '.join(('✓ ' if ready else '○ ') + name for name, ready in state['stages'].items())
            self.stages.set_text((f"{state['elapsed']:.1f}s elapsed · " + progress) if busy else state['log_tail'] if state['phase'] == 'error' else '')
            self.retry_demo = state['demo']
            self.retry.set_visible(state['phase'] == 'error' and bool(state['demo']))
            if state['phase'] == 'running':
                marker = (state['generation'], state['demo'])
                if self.opened != marker:
                    self.opened = marker
                    details = DEMOS[state['demo']]
                    url = details[2] if len(details) > 4 and details[4] == 'external' else 'http://127.0.0.1:8790/'
                    subprocess.Popen([os.path.join(ENGINE, 'open-demo-browser.sh'), url], start_new_session=True)
        except Exception:
            self.status.set_text('Status: Hub connection lost. Retrying...')
        return True


window = DemoHub()
window.connect("destroy", Gtk.main_quit)
window.show_all()

Gtk.main()
