# Amnezia VPN desktop widget for Serpantinum

A native-catalog widget for [Serpantinum by ilyamiro](https://github.com/ilyamiro/serpantinum): connect/disconnect the selected Amnezia profile, open the app, view tray state and `amn*` interface traffic. Move/resize/remove it through Serpantinum's normal widget editor.

## Install

Requires a writable per-user Serpantinum installation, Amnezia VPN with a working system tray item, Python 3.9+ and PyGObject/Gio (`python-gobject` on Arch, `python3-gi` on Debian/Ubuntu). Tested with Serpantinum 2.2.13 (`bc63054`), Arch Linux and Hyprland.

```bash
curl -fsSL https://raw.githubusercontent.com/bibibobo479/serpantinum-amnezia-widget/main/install.py | python3 -
serpantinum reload
```

Run **without sudo**. The command executes this repository's installer; download and read `install.py` first if you prefer. It downloads four widget files plus license/notices pinned to tag `v1.0.0`, backs up the registry once and inserts a marked entry. In the widget editor, select **Amnezia VPN**. Optional custom location: `python3 install.py --serpantinum /path/to/serpantinum/src/quickshell`. A local source checkout installs offline.

The installer changes the local built-in catalog; this is not an upstream addition or a claim of endorsement. Read-only/system/Nix store installations are unsupported by this installer. After a Serpantinum update, rerun it if the host replaced the widget registration.

## Behavior and limitations

The widget invokes native `com.canonical.dbusmenu` actions and `org.kde.StatusNotifierItem.Activate`, not an undocumented VPN control socket. It reads no VPN profile, key, password, server list or log, makes no external network requests and needs no administrative privileges. Server/protocol selection remains in Amnezia.

**Connected / connecting** is deliberately combined: Amnezia exposes the same native menu enabled flags during preparation, connection, reconnecting and disconnecting as while connected. This is not a successful-handshake or internet-connectivity check. Use the Amnezia app for exact state.

Traffic shows only `amn` plus digits interfaces. It may be absent for OpenVPN/Xray or differently named interfaces. Counter resets and recreated interfaces reset the measurement baseline. One shared watcher updates every two seconds and on native menu events, and stops when no visible widget is subscribed.

English, Russian and several other native menu translations are recognized. Unknown/ambiguous menus disable connection controls instead of guessing item IDs. Command availability is checked again at click time. Russian Serpantinum uses Russian widget text; other shell languages currently use English.

Remove desktop instances first, then `python3 install.py --uninstall` and `serpantinum reload`. Removal preserves later registry changes, host settings and Amnezia's connection.

## Tests and license

See [validation](VALIDATION.md) and the root README for isolated D-Bus integration tests. Real VPN toggling is not performed by the test suite.

AGPL-3.0-or-later, copyright 2026 bibibobo479. Serpantinum is copyright 2026 Illia Miroshnichenko and contributors, also AGPL-3.0-or-later. See [LICENSE](../LICENSE) and [NOTICE.md](../NOTICE.md). Unofficial independent integration; no Serpantinum or Amnezia binaries/assets are bundled.
