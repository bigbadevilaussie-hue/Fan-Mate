import QtQuick
import QtQuick.Window
import QtQuick.Controls

ApplicationWindow {
    id: root
    width: 900
    height: 440
    visible: true
    title: "Fan-Mate v2"
    color: "#000000"
    property string guiVersion: "1.11"

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
        // Three dials
        StatusLamps {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 62
            width: 320
            height: 44
            boostLvl: dev.boostLvl || 0
            tempLvl: dev.tempLvl || 0
            opal: dev.opal || 0
            killMode: dev.killMode || 0
        }

        BoostBar {
            x: 24
            y: 90
            width: 72
            height: 260
            gear: dev.boostLvl || 0
        }

        TempBar {
            x: 800
            y: 90
            width: 72
            height: 260
            level: dev.tempLvl || 0
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
            vmax: (dev.tempGear4 || 36.0) + 2.0
            tempGear1: dev.tempGear1 || 30.0
            tempGear2: dev.tempGear2 || 32.0
            tempGear3: dev.tempGear3 || 34.0
            tempGear4: dev.tempGear4 || 36.0
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
