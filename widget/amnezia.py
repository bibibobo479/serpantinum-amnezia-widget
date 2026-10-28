#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 bibibobo479
"""Read/control Amnezia's native tray menu. Never read VPN profiles or keys."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import unicodedata

SNI = 'org.kde.StatusNotifierItem'
MENU = 'com.canonical.dbusmenu'
WATCHER = 'org.kde.StatusNotifierWatcher'
CONNECT = {'connect', 'подключить', 'подключиться', 'підключити', 'verbinden', 'conectar', 'connecter', 'se connecter', 'connetti', 'bağlan', '连接', '連接'}
DISCONNECT = {'disconnect', 'отключить', 'отключиться', 'відключити', 'trennen', 'desconectar', 'déconnecter', 'se déconnecter', 'disconnetti', 'bağlantıyı kes', '断开连接', '中斷連接'}


def label(text):
    return unicodedata.normalize('NFKC', str(text)).replace('&', '').replace('_', '').strip(' .…').casefold()


def menu_actions(layout):
    """Only recognize named native actions; never guess IDs from menu positions."""
    actions = {}
    def visit(node):
        ident, props, children = node
        if props.get('visible', True):
            name = label(props.get('label', ''))
            key = 'connect' if name in CONNECT else 'disconnect' if name in DISCONNECT else None
            if key:
                if key in actions:
                    raise ValueError('ambiguous_menu')
                actions[key] = (ident, bool(props.get('enabled', True)))
            for child in children:
                visit(child)
    visit(layout)
    return actions


def state_from(actions):
    connect = actions.get('connect', (None, False))[1]
    disconnect = actions.get('disconnect', (None, False))[1]
    if set(actions) != {'connect', 'disconnect'} or connect == disconnect:
        return 'unknown'
    # Amnezia uses the SAME flags for Connected, Connecting and Disconnecting.
    # Do not present this as verified connectivity or a successful handshake.
    return 'active' if disconnect else 'offline'


class Traffic:
    def __init__(self, root=Path('/sys/class/net')):
        self.root, self.previous = root, None

    def read(self, active, now=None):
        now = time.monotonic() if now is None else now
        names = sorted(p.name for p in self.root.glob('amn*') if re.fullmatch(r'amn\d+', p.name)) if active else []
        current = {}
        for name in names:
            try:
                base = self.root/name/'statistics'
                current[name] = (int((base/'rx_bytes').read_text()), int((base/'tx_bytes').read_text()))
            except (OSError, ValueError):
                continue
        rx = tx = 0.0
        if self.previous and set(current) == set(self.previous[1]):
            elapsed = now-self.previous[0]
            if elapsed > 0:
                for name, counters in current.items():
                    before = self.previous[1][name]
                    # A recreated interface or counter reset is a new baseline.
                    if counters[0] >= before[0] and counters[1] >= before[1]:
                        rx += (counters[0]-before[0])/elapsed
                        tx += (counters[1]-before[1])/elapsed
        self.previous = (now, current)
        return {'interfaces': list(current), 'rx_rate': rx, 'tx_rate': tx}


class Client:
    def __init__(self):
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.target = None
        self.actions = {}
        self.traffic = Traffic()

    def call(self, dest, path, interface, method, signature=None, args=()):
        params = self.GLib.Variant(signature, args) if signature else None
        return self.bus.call_sync(dest, path, interface, method, params, None,
                                  self.Gio.DBusCallFlags.NONE, 1200, None).unpack()

    def discover(self):
        items = self.call(WATCHER, '/StatusNotifierWatcher', 'org.freedesktop.DBus.Properties',
                          'Get', '(ss)', (WATCHER, 'RegisteredStatusNotifierItems'))[0]
        for item in items[:128]:
            dest, _, tail = item.partition('/')
            path = '/'+tail if tail else '/StatusNotifierItem'
            try:
                props = self.call(dest, path, 'org.freedesktop.DBus.Properties', 'GetAll', '(s)', (SNI,))[0]
            except self.GLib.Error:
                continue
            if str(props.get('Id', '')).casefold() == 'amneziavpn' or str(props.get('Title', '')).casefold() == 'amneziavpn':
                self.target = (dest, path, props.get('Menu'))
                return True
        self.target = None
        return False

    def snapshot(self):
        result = {'state': 'unavailable', 'can_connect': False, 'can_disconnect': False, 'available': False}
        try:
            if self.target or self.discover():
                dest, path, menu = self.target
                if not menu or menu == '/':
                    result.update(state='unknown', available=True)
                else:
                    layout = self.call(dest, menu, MENU, 'GetLayout', '(iias)',
                                       (0, -1, ['label', 'enabled', 'visible']))[1]
                    self.actions = menu_actions(layout)
                    state = state_from(self.actions)
                    result.update(state=state, available=True,
                                  can_connect=state == 'offline', can_disconnect=state == 'active')
        except (self.GLib.Error, ValueError, TypeError):
            self.target = None
            self.actions = {}
            result['state'] = 'unavailable'
        result.update(self.traffic.read(result['state'] == 'active'))
        return result

    def act(self, action):
        state = self.snapshot()  # Fresh native enabled state, not a stale widget toggle.
        if action == 'open':
            if self.target:
                dest, path, _ = self.target
                self.call(dest, path, SNI, 'Activate', '(ii)', (0, 0))
            else:
                executable = shutil.which('AmneziaVPN')
                if not executable and Path('/opt/AmneziaVPN/bin/AmneziaVPN').is_file():
                    executable = '/opt/AmneziaVPN/bin/AmneziaVPN'
                if not executable:
                    return {'ok': False, 'error': 'not_installed'}
                env = dict(os.environ)
                for key in ('QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH', 'QML_IMPORT_PATH', 'QML2_IMPORT_PATH', 'QT_STYLE_OVERRIDE', 'QT_QPA_PLATFORMTHEME'):
                    env.pop(key, None)
                env['QT_QPA_PLATFORM'] = 'xcb'
                subprocess.Popen([executable], env=env, start_new_session=True, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {'ok': True, 'requested': 'open'}
        if action not in ('connect', 'disconnect') or not state.get('can_'+action):
            return {'ok': False, 'error': 'action_unavailable'}
        ident, enabled = self.actions[action]
        dest, _, menu = self.target
        self.call(dest, menu, MENU, 'Event', '(isvu)', (ident, 'clicked', self.GLib.Variant('i', 0), 0))
        return {'ok': True, 'requested': action}


def emit(data):
    print(json.dumps(data, ensure_ascii=False, separators=(',', ':')), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('status', 'watch', 'connect', 'disconnect', 'open'), nargs='?', default='status')
    args = parser.parse_args()
    try:
        client = Client()
        if args.command == 'watch':
            # One process per QML singleton, no subprocess polling or network requests.
            # Menu signals refresh immediately, a timer covers missing signals/restarts.
            pending = [False]
            def update(*unused):
                pending[0] = False
                emit(client.snapshot())
                return False
            def changed(*unused):
                if not pending[0]:
                    pending[0] = True
                    client.GLib.timeout_add(120, update)
            client.bus.signal_subscribe(None, MENU, None, None, None, client.Gio.DBusSignalFlags.NONE, changed)
            client.bus.signal_subscribe(None, WATCHER, None, None, None, client.Gio.DBusSignalFlags.NONE, changed)
            def tick():
                update()
                return True
            client.GLib.timeout_add_seconds(2, tick)
            update()
            client.GLib.MainLoop().run()
        else:
            emit(client.snapshot() if args.command == 'status' else client.act(args.command))
    except ImportError:
        emit({'ok': False, 'state': 'error', 'error': 'missing_gi'})
        return 1
    except Exception:
        # D-Bus errors can contain app-provided strings. Do not log private payloads.
        emit({'ok': False, 'state': 'error', 'error': 'backend_unavailable'})
        return 1
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (BrokenPipeError, KeyboardInterrupt):
        pass
