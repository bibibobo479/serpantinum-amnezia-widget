#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 bibibobo479
"""Register the Amnezia VPN widget in the installed Serpantinum widget catalog."""
import argparse
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.request

REPO = 'bibibobo479/serpantinum-amnezia-widget'
VERSION = 'v1.0.0'
WIDGET_FILES = ('AmneziaFace.qml', 'AmneziaService.qml', 'amnezia.py', 'qmldir')
FILES = (*WIDGET_FILES, 'LICENSE', 'NOTICE.md')
START = '        // BEGIN serpantinum-amnezia-widget\n'
END = '        // END serpantinum-amnezia-widget\n'
ENTRY = START + '''        "amnezia": {
            name: "Amnezia VPN",
            icon: String.fromCodePoint(0xF0582),
            defaultWidth: 330,
            defaultHeight: 165,
            defaultVariant: "default",
            variants: {
                "default": { file: "faces/amnezia/AmneziaFace.qml", icon: "1", label: "Amnezia VPN" }
            }
        },
''' + END


def registry_update(text, remove=False):
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise ValueError('Damaged extension markers; registry was not changed')
    if START in text:
        begin, end = text.index(START), text.index(END)+len(END)
        text = text[:begin]+text[end:]
    if remove:
        return text
    if re.search(r'["\']amnezia["\']\s*:', text):
        raise ValueError('Another amnezia widget is already registered; refusing to overwrite it')
    pattern = r'(\bproperty\s+var\s+types\s*:\s*\(\{\s*\n)'
    if len(re.findall(pattern, text)) != 1:
        raise ValueError('Unsupported WidgetRegistry.qml format; no files changed')
    return re.sub(pattern, lambda match: match.group(0)+ENTRY, text, count=1)


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.amnezia-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def detect(explicit=None):
    candidates = [Path(explicit).expanduser()] if explicit else []
    if not explicit:
        if os.environ.get('SERPANTINUM_DIR'):
            candidates.append(Path(os.environ['SERPANTINUM_DIR']))
        data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))
        candidates += [data/'serpantinum/src', Path('/usr/share/serpantinum/src')]
    for base in candidates:
        for root in (base, base/'quickshell', base/'src/quickshell'):
            if (root/'widgets/WidgetRegistry.qml').is_file():
                return root.resolve()
    raise ValueError('Serpantinum not found; pass --serpantinum /path/to/src/quickshell')


def payload():
    here = Path(__file__).resolve().parent/'widget'
    result = {}
    for name in FILES:
        source = here/name if name in WIDGET_FILES else here.parent/name
        if source.is_file():
            result[name] = source.read_bytes()
        else:
            relative = 'widget/'+name if name in WIDGET_FILES else name
            url = f'https://raw.githubusercontent.com/{REPO}/{VERSION}/{relative}'
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read(512*1024+1)
            if len(data) > 512*1024:
                raise ValueError('Unexpectedly large widget file')
            result[name] = data
    return result


def install(root, files=None, remove=False):
    registry = root/'widgets/WidgetRegistry.qml'
    original = registry.read_text()
    updated = registry_update(original, remove)
    target = root/'widgets/faces/amnezia'
    if target.is_symlink():
        raise ValueError('Widget directory must not be a symlink')
    if target.exists() and not (target/'.serpantinum-amnezia-widget').is_file():
        raise ValueError('Unrelated amnezia directory exists; not changed')
    if not os.access(registry.parent, os.W_OK):
        raise ValueError('Serpantinum is read-only. Use a writable per-user installation; do not run this installer as root')
    if remove:
        # Remove only our marked registry block, preserving later upstream/user changes.
        atomic(registry, updated.encode())
        if (target/'.serpantinum-amnezia-widget').is_file():
            for name in (*FILES, '.serpantinum-amnezia-widget'):
                (target/name).unlink(missing_ok=True)
            try:
                target.rmdir()
            except OSError:
                pass
        return
    if set(files or {}) != set(FILES):
        raise ValueError('Incomplete payload')
    backup = registry.with_name('WidgetRegistry.qml.before-amnezia')
    if not backup.exists():
        atomic(backup, original.encode())
    for name, content in files.items():
        atomic(target/name, content)
    atomic(target/'.serpantinum-amnezia-widget', (VERSION+'\n').encode())
    atomic(registry, updated.encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serpantinum', help='Serpantinum src or quickshell directory')
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise ValueError('Run as the desktop user without sudo')
    if not args.uninstall:
        try:
            from gi.repository import Gio
        except ImportError:
            raise ValueError('Install python-gobject (Arch) or python3-gi (Debian/Ubuntu) first') from None
    root = detect(args.serpantinum)
    install(root, None if args.uninstall else payload(), args.uninstall)
    print('Removed.' if args.uninstall else 'Installed: Amnezia VPN is now in the built-in widget catalog.')
    print('Reload Serpantinum, then open its widget editor. / Перезагрузите Serpantinum и откройте редактор виджетов.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        print('Installation stopped: '+str(error), file=sys.stderr)
        sys.exit(1)
