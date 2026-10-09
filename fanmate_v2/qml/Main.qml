import QtQuick
import QtQuick.Window
import QtQuick.Controls

ApplicationWindow {
    id: root
    width: 900
    height: 530
    visible: true
    title: "Fan-Mate v2"
    color: "#000000"
    property string guiVersion: "1.12"

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
        // (top info strip removed — content moved to bottom row)
        // ================================================================
        // LEFT: NET gauge + graph (in one bordered rectangle)
        // ================================================================
        Rectangle {
            x: 30
            y: 100
            width: 220
            height: 330
            color: "transparent"
            border.color: "#4a5568"
            border.width: 1
            radius: 6

            TrafficGauge {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 20
                width: 180
                height: 180
                value: (dev.netKbps || 0) / 1024.0
                vmin: 0
                vmax: 4
                boostThresholdMb: (dev.boostThreshold || 900) / 1024.0
            }

            MiniGraph {
                id: netGraph
                anchors.horizontalCenter: parent.horizontalCenter
                y: 260
                width: 180
                height: 48
                vmin: 0
                vmax: 4
                threshold: (dev.boostThreshold || 900) / 1024.0
                dataJson: dev.netHistJson
                lineColor: {
                    var t = (dev.boostThreshold || 900) / 1024.0
                    var v = (dev.netKbps || 0) / 1024.0
                    if (v >= t * 3) return "#e74c3c"
                    if (v >= t * 2) return "#e67e22"
                    if (v >= t * 1) return "#f1c40f"
                    return "#2ecc71"
                }
                fillColor: Qt.rgba(lineColor.r, lineColor.g, lineColor.b, 0.18)
            }
        }

        // ================================================================
        // MIDDLE: FAN gauge + graph (bigger rectangle)
        // ================================================================
        Rectangle {
            x: 290
            y: 100
            width: 320
            height: 330
            color: "transparent"
            border.color: "#4a5568"
            border.width: 1
            radius: 6

            RpmGauge {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 20
                width: 285
                height: 285
                value: dev.rpm || 0
                vmin: 0
                vmax: 7500
                rpmWarn: 2000
                rpmFast: 4000
                rpmMax: 6000
            }

            MiniGraph {
                id: rpmGraph
                anchors.horizontalCenter: parent.horizontalCenter
                y: 260
                width: 285
                height: 48
                vmin: 0
                vmax: 7500
                threshold: 3000
                dataJson: dev.rpmHistJson
                lineColor: {
                    var v = dev.rpm || 0
                    if (v >= 6000) return "#e74c3c"
                    if (v >= 4500) return "#e67e22"
                    if (v >= 3000) return "#f1c40f"
                    return "#2ecc71"
                }
                fillColor: Qt.rgba(lineColor.r, lineColor.g, lineColor.b, 0.18)
            }
        }

        // ================================================================
        // RIGHT: PHONE gauge + graph (in one bordered rectangle)
        // ================================================================
        Rectangle {
            x: 650
            y: 100
            width: 220
            height: 330
            color: "transparent"
            border.color: "#4a5568"
            border.width: 1
            radius: 6

            TempGauge {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 20
                width: 180
                height: 180
                value: dev.temp || 0
                vmin: 18.0
                vmax: (dev.tempGear4 || 39.0) + 2.0
                tempGear1: dev.tempGear1 || 33.0
                tempGear2: dev.tempGear2 || 35.0
                tempGear3: dev.tempGear3 || 37.0
                tempGear4: dev.tempGear4 || 39.0
            }

            MiniGraph {
                id: tempGraph
                anchors.horizontalCenter: parent.horizontalCenter
                y: 260
                width: 180
                height: 48
                vmin: 18
                vmax: (dev.tempGear4 || 39) + 2
                threshold: dev.tempGear2 || 35
                dataJson: dev.tempHistJson
                lineColor: {
                    var v = dev.temp || 0
                    var g4 = dev.tempGear4 || 39
                    var g3 = dev.tempGear3 || 37
                    var g2 = dev.tempGear2 || 35
                    if (v >= g4) return "#e74c3c"
                    if (v >= g3) return "#e67e22"
                    if (v >= g2) return "#f1c40f"
                    return "#2ecc71"
                }
                fillColor: Qt.rgba(lineColor.r, lineColor.g, lineColor.b, 0.18)
            }
        }

        // bottom info row
        Item {
            id: bottomRow
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 28
            width: 560
            height: 36

            Row {
                anchors.centerIn: parent
                spacing: 56

                Column {
                    spacing: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "🌤️ OUT"
                        color: "#4a5568"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 8
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: (dev.outdoor > -90) ? dev.outdoor.toFixed(1) + "°C" : "--.-°C"
                        color: "#cdd6f4"
                        font.family: "Menlo"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                    }
                }

                Column {
                    spacing: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "🏠 ROOM"
                        color: "#4a5568"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 8
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: (dev.room > -90) ? dev.room.toFixed(1) + "°C" : "--.-°C"
                        color: "#cdd6f4"
                        font.family: "Menlo"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                    }
                }

                Column {
                    spacing: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "🕐 TIME"
                        color: "#4a5568"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 8
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }
                    Text {
                        id: bottomTimeText
                        anchors.horizontalCenter: parent.horizontalCenter
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
                                bottomTimeText.text = (h < 10 ? " " : "") + h + ":" +
                                                      (m < 10 ? "0" + m : m) + " " + ampm
                            }
                        }
                    }
                }

                Column {
                    spacing: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "📱 PHONE"
                        color: "#4a5568"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 8
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: dev.phone ? "YES" : "NO"
                        color: dev.phone ? "#2ecc71" : "#7a8194"
                        font.family: "Menlo"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                    }
                }
            }
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
