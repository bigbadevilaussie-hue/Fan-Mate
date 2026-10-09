import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtWebEngine

ApplicationWindow {
    id: root
    width: 900
    height: 440
    visible: true
    title: "Fan-Mate v2"
    color: "#000000"
    property string guiVersion: "1.14"

    function openSerialPanel() {
        serialPanel.visible = true
        serialWeb.url = dev.freshSerialUrl()
        dev.fetchSerial()
    }

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
                text: "📟  Serial"
                onTriggered: {
                    menu.close()
                    root.openSerialPanel()
                }
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
            alertLvl: dev.alert || 0
        }

        BoostBar {
            x: 24
            y: 90
            width: 72
            height: 260
            gear: dev.boostLvl || 0
        }

        TempBar {
            x: parent.width - 24 - width
            y: 90
            width: 72
            height: 260
            level: dev.tempLvl || 0
            alertLvl: dev.alert || 0
        }

        TrafficGauge {
            id: netGauge
            x: 100
            y: 140
            width: 180
            height: 180
            value: (dev.netKbps || 0) / 1024.0
            vmin: 0
            vmax: 3
            boostThresholdMb: (dev.boostThreshold || 700) / 1024.0
        }

        RpmGauge {
            id: rpmGauge
            x: (parent.width - width) / 2
            y: 90
            width: 240
            height: 240
            value: dev.rpm || 0
            vmin: 0
            vmax: 7500
            rpmWarn: 2000
            rpmFast: 4000
            rpmMax: 6000
        }

        TempGauge {
            id: tempGauge
            x: 620
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

        // Three sparklines under their gauges
        Sparkline {
            x: netGauge.x + (netGauge.width - width) / 2
            y: netGauge.y + netGauge.height + 6
            width: 140
            height: 32
            maxSamples: 30
            value: netGauge.value
            lineColor: netGauge.valueColor
            autoScale: true
            minSpan: 1.0
            hardMin: 0
            threshold: netGauge.boostThresholdMb
            thresholdInScale: false
        }

        Sparkline {
            x: rpmGauge.x + (rpmGauge.width - width) / 2
            y: rpmGauge.y + rpmGauge.height + 6
            width: 140
            height: 32
            maxSamples: 30
            value: rpmGauge.value
            lineColor: rpmGauge.valueColor
            autoScale: true
            minSpan: 500
            hardMin: 0
            threshold: rpmGauge.rpmWarn
            thresholdInScale: false
        }

        Sparkline {
            x: tempGauge.x + (tempGauge.width - width) / 2
            y: tempGauge.y + tempGauge.height + 6
            width: 140
            height: 32
            maxSamples: 30
            value: tempGauge.value
            valid: tempGauge.hasData
            lineColor: tempGauge.valueColor
            autoScale: true
            minSpan: 3
            threshold: tempGauge.tempGear2
            thresholdInScale: false
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
                    width: 64
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "🌤️ OUT"
                        color: "#4a5568"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 9
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: (dev.outdoor > -90) ? dev.outdoor.toFixed(1) + "°C" : "--.-°C"
                        color: "#cdd6f4"
                        font.family: "Menlo"
                        font.pixelSize: 15
                        font.weight: Font.Bold
                    }
                }

                Column {
                    spacing: 1
                    anchors.verticalCenter: parent.verticalCenter
                    width: 64
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "🏠 ROOM"
                        color: "#4a5568"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 9
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: (dev.room > -90) ? dev.room.toFixed(1) + "°C" : "--.-°C"
                        color: "#cdd6f4"
                        font.family: "Menlo"
                        font.pixelSize: 15
                        font.weight: Font.Bold
                    }
                }

                Column {
                    spacing: 1
                    anchors.verticalCenter: parent.verticalCenter
                    width: 64
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "🕐 TIME"
                        color: "#4a5568"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 9
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }
                    Text {
                        id: bottomTimeText
                        anchors.horizontalCenter: parent.horizontalCenter
                        color: "#cdd6f4"
                        font.family: "Menlo"
                        font.pixelSize: 15
                        font.weight: Font.Bold
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
                    width: 64
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "📱 PHONE"
                        color: "#4a5568"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 9
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: dev.phone ? "YES" : "NO"
                        color: dev.phone ? "#2ecc71" : "#7a8194"
                        font.family: "Menlo"
                        font.pixelSize: 15
                        font.weight: Font.Bold
                    }
                }
            }
        }

        // footer
        Text {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 8
            text: "GUI v" + root.guiVersion + "  ·  FW " + (dev.fw || "?")
            color: "#333"
            font.family: "Menlo"
            font.pixelSize: 10
        }
    }


    // ================================================================
    // Serial panel — card with WebEngine view of the device serial page
    // ================================================================
    Rectangle {
        id: serialPanel
        anchors.fill: parent
        color: "#0a0a12"
        visible: false
        z: 100

        Rectangle {
            anchors.fill: parent
            anchors.margins: 12
            color: "#181825"
            radius: 8
            border.color: "#313145"
            border.width: 1

            Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                // --- top control row ---
                Row {
                    width: parent.width
                    height: 30
                    spacing: 8

                    Text {
                        text: "📟  Serial"
                        color: "#89b4fa"
                        font.family: "Helvetica Neue"
                        font.pixelSize: 14
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Item { width: parent.width - 340; height: 1 }

                    Rectangle {
                        width: 80; height: 26; radius: 4
                        anchors.verticalCenter: parent.verticalCenter
                        color: refArea.pressed ? "#313145" : "#232334"
                        border.color: "#89b4fa"
                        border.width: 1
                        Text {
                            anchors.centerIn: parent
                            text: "Refresh"
                            color: "#cdd6f4"
                            font.family: "Helvetica Neue"
                            font.pixelSize: 11
                        }
                        MouseArea {
                            id: refArea
                            anchors.fill: parent
                            onClicked: {
                                serialWeb.reload()
                                dev.fetchSerial()
                            }
                        }
                    }

                    Rectangle {
                        width: 90; height: 26; radius: 4
                        anchors.verticalCenter: parent.verticalCenter
                        color: copyArea.pressed ? "#1e66f5" : "#232334"
                        border.color: "#89b4fa"
                        border.width: 1
                        Text {
                            anchors.centerIn: parent
                            text: "Copy All"
                            color: "#cdd6f4"
                            font.family: "Helvetica Neue"
                            font.pixelSize: 11
                        }
                        MouseArea {
                            id: copyArea
                            anchors.fill: parent
                            onClicked: dev.copyToClipboard(dev.serialText)
                        }
                    }

                    Rectangle {
                        width: 60; height: 26; radius: 4
                        anchors.verticalCenter: parent.verticalCenter
                        color: closeArea.pressed ? "#313145" : "#232334"
                        border.color: "#313145"
                        border.width: 1
                        Text {
                            anchors.centerIn: parent
                            text: "Close"
                            color: "#cdd6f4"
                            font.family: "Helvetica Neue"
                            font.pixelSize: 11
                        }
                        MouseArea {
                            id: closeArea
                            anchors.fill: parent
                            onClicked: serialPanel.visible = false
                        }
                    }
                }

                // --- WebEngine view ---
                Rectangle {
                    width: parent.width
                    height: parent.height - 38
                    color: "#ffffff"
                    radius: 4
                    clip: true

                    WebEngineView {
                        id: serialWeb
                        anchors.fill: parent
                        anchors.margins: 2
                        zoomFactor: 1.15
                    }
                }
            }
        }
    }

    // Auto-refresh /serial-raw for Copy while panel is visible
    Timer {
        interval: 2000
        running: serialPanel.visible
        repeat: true
        onTriggered: dev.fetchSerial()
    }

    OtaDialog {
        id: otaDialog
    }

    Connections {
        target: dev
        function onOtaUploading() { root.openSerialPanel() }
        function onOtaDone()      { root.openSerialPanel() }
    }
}
