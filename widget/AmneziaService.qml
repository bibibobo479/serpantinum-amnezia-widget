// SPDX-License-Identifier: AGPL-3.0-or-later
pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

Item {
    id: service
    property int subscribers: 0
    property var status: ({state: "unavailable", available: false})
    property string error: ""
    property bool busy: action.running || cooldown.running
    readonly property string helper: decodeURIComponent(Qt.resolvedUrl("amnezia.py").toString().replace(/^file:\/\//, ""))

    function subscribe() { subscribers++; }
    function unsubscribe() { subscribers = Math.max(0, subscribers - 1); }
    function perform(command) {
        if (busy) return;
        if (command !== "open" && command !== "connect" && command !== "disconnect") return;
        error = "";
        action.command = ["python3", helper, command];
        action.running = true;
    }
    Process {
        id: watcher
        running: service.subscribers > 0 && !retry.running
        command: ["python3", service.helper, "watch"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    service.status = JSON.parse(data);
                    if (service.status.error) service.error = service.status.error;
                    else if (["missing_gi", "backend_unavailable", "invalid_response"].indexOf(service.error) >= 0) service.error = "";
                } catch (e) { service.error = "invalid_response"; }
            }
        }
        onExited: (code, status) => {
            if (service.subscribers > 0) {
                service.status = {state: "error", available: false};
                if (!service.error) service.error = "backend_unavailable";
                retry.restart();
            }
        }
    }
    Timer { id: retry; interval: 10000 }
    Timer { id: cooldown; interval: 1800 }
    Process {
        id: action
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    let result = JSON.parse(this.text);
                    if (!result.ok) service.error = result.error || "action_failed";
                } catch (e) { service.error = "action_failed"; }
            }
        }
        onExited: (code, status) => cooldown.restart()
    }
}
