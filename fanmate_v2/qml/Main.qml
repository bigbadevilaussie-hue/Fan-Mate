import QtQuick
import QtQuick.Window
import QtQuick.Controls

ApplicationWindow {
    id: root
    width: 820
    height: 400
    visible: true
    title: "Fan-Mate v2"
    color: "#000000"
    property string guiVersion: "1.06"

    // ---------- drawer ----------
    Drawer {
        id: menu
        width: 200
        height: root.height
        edge: Qt.LeftEdge
        interactive: true

        background: Rectangle {
            color: "#181825"
            border.color: "#313145"
            border.width: 1
        }

        Column {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 6

            Text {
                text: "🌀  Fan-Mate"
                color: "#89b4fa"
                font.family: "Helvetica Neue"
                font.pixelSize: 18
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
                topPadding: 8
                bottomPadding: 8
            }

            Rectangle { width: parent.width; height: 1; color: "#313145" }

            MenuButton {
                text: "🌐  Serial page"
                onTriggered: dev.open_url("http://fan-mate.local/serial")
            }
            MenuButton {
                text: "📍  Dashboard"
                onTriggered: dev.open_url("http://fan-mate.local/")
            }
            MenuButton {
                text: "📡  Update Firmware"
                onTriggered: {
                    menu.close()
                    otaDialog.open()
                }
            }

            Rectangle { width: parent.width; height: 1; color: "#313145" }

            MenuButton {
                text: "❌  Quit"
                textColor: "#e64553"
                onTriggered: dev.quit_app()
            }

            Item { width: 1; height: 1 }
        }
    }

    // ---------- main content ----------
    Item {
        id: content
        anchors.fill: parent

        // push content when drawer opens
        transform: Translate {
            x: menu.position * 200
        }

        // hamburger button
        Rectangle {
            id: menuBtn
            x: 12
            y: 12
            width: 40
            height: 40
            radius: 6
            color: menuBtnArea.pressed ? "#2a2a3a" : "transparent"
            border.color: "#313145"
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: "☰"
                color: "#cdd6f4"
                font.pixelSize: 22
            }

            MouseArea {
                id: menuBtnArea
                anchors.fill: parent
                onClicked: menu.opened ? menu.close() : menu.open()
            }
        }

        // Top info strip
        Item {
            id: topStrip
            anchors.horizontalCenter: parent.horizontalCenter
            y: 18
            width: parent.width - 80
            height: 40

            // LED row (left)
            Row {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                Rectangle { width: 10; height: 10; radius: 5
                    color: dev.alert == 0 ? "#50e890" : "#0a1a0f"
                    border.color: "#50e890"; border.width: 1; antialiasing: true }
                Rectangle { width: 10; height: 10; radius: 5
                    color: dev.alert == 1 ? "#ffd23f" : "#1a1608"
                    border.color: "#ffd23f"; border.width: 1; antialiasing: true }
                Rectangle { width: 10; height: 10; radius: 5
                    color: dev.alert == 2 ? "#ff8a30" : "#1a0e05"
                    border.color: "#ff8a30"; border.width: 1; antialiasing: true }
                Rectangle { width: 10; height: 10; radius: 5
                    color: dev.alert == 3 ? "#ff304f" : "#1a050a"
                    border.color: "#ff304f"; border.width: 1; antialiasing: true }
            }

            // Outdoor temp
            Column {
                anchors.left: parent.left
                anchors.leftMargin: 90
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0
                Text {
                    text: "OUTDOOR"
                    color: "#4a5568"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 8
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                }
                Text {
                    text: (dev.outdoor > -90)
                          ? dev.outdoor.toFixed(1) + "°C"
                          : "--.-°C"
                    color: "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 14
                    font.weight: Font.Medium
                }
            }

            // Room temp (placeholder until NTC wired)
            Column {
                anchors.left: parent.left
                anchors.leftMargin: 200
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0
                Text {
                    text: "ROOM"
                    color: "#4a5568"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 8
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                }
                Text {
                    text: "--.-°C"
                    color: "#4a5568"
                    font.family: "Menlo"
                    font.pixelSize: 14
                    font.weight: Font.Medium
                }
            }

            // Time
            Column {
                anchors.left: parent.left
                anchors.leftMargin: 300
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0
                Text {
                    text: "TIME"
                    color: "#4a5568"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 8
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                }
                Text {
                    id: timeText
                    color: "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 14
                    font.weight: Font.Medium
                    Timer {
                        interval: 1000
                        running: true
                        repeat: true
                        triggeredOnStart: true
                        onTriggered: {
                            var d = new Date()
                            var h = d.getHours()
                            var m = d.getMinutes()
                            var ampm = h >= 12 ? "PM" : "AM"
                            h = h % 12; if (h === 0) h = 12
                            timeText.text = (h < 10 ? " " : "") + h + ":" +
                                            (m < 10 ? "0" + m : m) + " " + ampm
                        }
                    }
                }
            }

            // Status (right)
            Column {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0
                Text {
                    anchors.right: parent.right
                    text: "STATUS"
                    color: "#4a5568"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 8
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                }
                Text {
                    id: statusText
                    anchors.right: parent.right
                    font.family: "Helvetica Neue"
                    font.pixelSize: 14
                    font.weight: Font.Bold
                    text: {
                        if (dev.fan_stall) return "FAN STALL"
                        if (dev.sleep)     return "SLEEPING"
                        if (dev.alert >= 3) return "KILL"
                        if (dev.alert == 2) return "OH SHIT"
                        if (dev.alert == 1) return "WARNING"
                        if (dev.boost)      return "BOOSTING"
                        if (!dev.opal)      return "OPAL DOWN"
                        return "NONE"
                    }
                    color: {
                        if (dev.fan_stall) return "#e74c3c"
                        if (dev.alert >= 3) return "#e74c3c"
                        if (dev.alert == 2) return "#e74c3c"
                        if (dev.alert == 1) return "#e67e22"
                        if (dev.boost)      return "#2ecc71"
                        return "#7a8194"
                    }
                }
            }
        }

        // Three dials
        BoostBar {
            x: 30
            y: 100
            width: 48
            height: 260
            gear: dev.boostLvl || 0
        }

        TrafficGauge {
            x: 80
            y: 140
            width: 180
            height: 180
            value: (dev.netKbps || 0) / 1024.0
            vmin: 0
            vmax: 3
            boostThresholdMb: (dev.boostThreshold || 700) / 1024.0
        }

        RpmGauge {
            x: 280
            y: 90
            width: 285
            height: 285
            value: dev.rpm || 0
            vmin: 0
            vmax: 7500
            rpmWarn: 2000
            rpmFast: 4000
            rpmMax: 6000
        }

        TempGauge {
            x: 590
            y: 140
            width: 180
            height: 180
            value: dev.temp || 0
            vmin: 18.0
            vmax: (dev.tempKill || 36.0) + 2.0
            tempWarning: dev.tempWarning || 32.0
            tempPanic:   dev.tempPanic   || 34.0
            tempKill:    dev.tempKill    || 36.0
        }

        // footer
        Text {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 8
            text: "GUI v" + root.guiVersion + "  ·  FW " + dev.fw
            color: "#333"
            font.family: "Menlo"
            font.pixelSize: 10
        }
    }

    OtaDialog {
        id: otaDialog
    }
}
