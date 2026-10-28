// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 bibibobo479
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import "../../../"
import "../../../reusables"

Item {
    id: root
    anchors.fill: parent
    property real minWidth: 260
    property real minHeight: 145
    property real maxWidth: 620
    property real maxHeight: 280
    property real minAspect: 1.4
    property real maxAspect: 3.2
    property bool isRound: false
    property bool subscribed: false
    readonly property bool russian: String(I18n.currentLang).toLowerCase().startsWith("ru")
    readonly property var vpn: AmneziaService.status
    readonly property bool active: vpn.state === "active"
    readonly property color accent: active ? ThemeBackend.green : ThemeBackend.mauve
    function tr(ru, en) { return russian ? ru : en; }
    function rate(value) {
        let n = Number(value) || 0;
        return n >= 1048576 ? (n / 1048576).toFixed(1) + " MiB/s" : (n / 1024).toFixed(1) + " KiB/s";
    }
    function subscribeIfVisible() {
        if (visible && !subscribed) { AmneziaService.subscribe(); subscribed = true; }
        else if (!visible && subscribed) { AmneziaService.unsubscribe(); subscribed = false; }
    }
    Component.onCompleted: subscribeIfVisible()
    onVisibleChanged: subscribeIfVisible()
    Component.onDestruction: { if (subscribed) AmneziaService.unsubscribe(); }

    Rectangle {
        anchors.fill: parent
        radius: ThemeBackend.borderRadius
        color: ThemeBackend.surface0
        opacity: ThemeBackend.elementOpacity
        border.width: 1
        border.color: Qt.alpha(root.accent, 0.3)
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8
        RowLayout {
            spacing: 10
            Text {
                text: String.fromCodePoint(0xF0582)
                font.family: ThemeBackend.iconFont
                font.pixelSize: 26
                color: root.accent
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: "Amnezia VPN"
                    font.family: ThemeBackend.fontFamily
                    font.pixelSize: 17
                    font.bold: true
                    color: ThemeBackend.text
                }
                Text {
                    Layout.fillWidth: true
                    text: root.active ? root.tr("Подключён / подключается", "Connected / connecting")
                        : root.vpn.state === "offline" ? root.tr("VPN отключён", "VPN disconnected")
                        : root.vpn.state === "unknown" ? root.tr("Проверьте статус в Amnezia", "Check status in Amnezia")
                        : root.vpn.state === "error" ? root.tr("Нет связи с виджетом", "Widget backend unavailable")
                        : root.tr("Amnezia не найдена в трее", "Amnezia is not in the tray")
                    color: ThemeBackend.subtext0
                    font.family: ThemeBackend.fontFamily
                    font.pixelSize: 11
                    elide: Text.ElideRight
                }
            }
            IconButton {
                size: 32
                buttonIcon: String.fromCodePoint(0xF03CC)
                iconFontSize: 16
                textColor: ThemeBackend.text
                accentColor: ThemeBackend.surface1
                enabled: !AmneziaService.busy
                onClicked: AmneziaService.perform("open")
                ToolTip.visible: hovered.hovered
                ToolTip.text: root.tr("Открыть Amnezia", "Open Amnezia")
                HoverHandler { id: hovered }
            }
        }
        Text {
            Layout.fillWidth: true
            text: AmneziaService.error === "missing_gi" ? root.tr("Установите python-gobject / python3-gi", "Install python-gobject / python3-gi")
                : AmneziaService.error === "not_installed" ? root.tr("Сначала установите Amnezia VPN", "Install Amnezia VPN first")
                : AmneziaService.error ? root.tr("Действие не выполнено. Откройте Amnezia.", "Action failed. Open Amnezia.")
                : root.active && root.vpn.interfaces && root.vpn.interfaces.length
                    ? "↓ " + root.rate(root.vpn.rx_rate) + "    ↑ " + root.rate(root.vpn.tx_rate)
                    : root.tr("Используется профиль, выбранный в Amnezia", "Uses the profile selected in Amnezia")
            font.family: ThemeBackend.fontFamily
            font.pixelSize: 11
            color: AmneziaService.error ? ThemeBackend.red : ThemeBackend.subtext0
            elide: Text.ElideRight
        }
        Item { Layout.fillHeight: true; implicitHeight: 0 }
        Button {
            id: toggle
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            enabled: !AmneziaService.busy && (root.vpn.can_connect || root.vpn.can_disconnect || !root.vpn.available)
            text: AmneziaService.busy ? root.tr("Выполняется…", "Working…")
                : root.vpn.can_disconnect ? root.tr("Отключить VPN", "Disconnect VPN")
                : root.vpn.can_connect ? root.tr("Подключить VPN", "Connect VPN")
                : root.tr("Открыть Amnezia", "Open Amnezia")
            onClicked: AmneziaService.perform(root.vpn.can_disconnect ? "disconnect" : root.vpn.can_connect ? "connect" : "open")
            background: Rectangle {
                radius: Math.min(10, ThemeBackend.borderRadius)
                color: toggle.down ? Qt.darker(root.accent, 1.15) : toggle.hovered ? Qt.lighter(root.accent, 1.08) : root.accent
                opacity: toggle.enabled ? 1 : 0.45
            }
            contentItem: Text {
                text: toggle.text
                font.family: ThemeBackend.fontFamily
                font.pixelSize: 12
                font.bold: true
                color: ThemeBackend.crust
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
