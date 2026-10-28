# Validation — 2026-10-28

Environment: installed Serpantinum 2.2.13 (`bc63054`), Arch Linux, Hyprland/Wayland, Quickshell, native Amnezia VPN tray item.

- Eight core/installer tests pass: native state semantics, localized/mnemonic labels, unknown/duplicate actions, traffic reset and exclusion of unrelated interfaces, repeat install, conservative removal and refusal to replace unrelated files.
- Two integration tests pass on a **private session bus**: fake native tray and DBusMenu exercise connect/disconnect/open, fresh action availability checks and streaming status through real Gio calls.
- The actual registered QML face loads using Serpantinum's theme and reports the running Amnezia instance. Read-only live status and interface traffic were checked. No real VPN disconnect/reconnect was performed.
- Card/minimum-size rendering checked in a separate preview. Installation registers `amnezia` in the native widget catalog; only its own marked block/files are modified.

Connection status is intentionally not a handshake assertion. The tray API does not distinguish all transition states. Other host versions, compositors and native menu languages are not comprehensively tested.
