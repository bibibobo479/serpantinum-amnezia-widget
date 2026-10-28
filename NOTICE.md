# Notices

Widget source and installer: Copyright (c) 2026 bibibobo479, GNU Affero General Public License version 3 or any later version. See LICENSE. Source for the installed version is available from this repository's matching release tag.

The widget is designed to load within **Serpantinum**, copyright (C) 2026 Illia Miroshnichenko and contributors, distributed under AGPL-3.0-or-later: https://github.com/ilyamiro/serpantinum . It uses the installed shell's registry interface, theme, scaler conventions and reusable UI components. Those components are not relicensed or copied into this package. Changes to the local registry consist of an explicitly marked registration block; the installer preserves the remainder of the original file and its notices. The screenshot shows our card rendered with the installed shell's theme and button component.

**Amnezia VPN** is a separate project: https://github.com/amnezia-vpn/amnezia-client . This integration communicates with the running app through the session D-Bus tray/menu interfaces. No Amnezia executable, source file, logo, VPN configuration or private data is distributed here. Inspection of its public native tray implementation established the meaning and limitation of menu enabled flags: https://github.com/amnezia-vpn/amnezia-client/blob/dev/client/ui/utils/systemTrayNotificationHandler.cpp .

Names identify compatibility only. This project is not affiliated with or endorsed by the Serpantinum or Amnezia maintainers. Its installation adds a widget to the user's local built-in catalog; no upstream merge is implied.
