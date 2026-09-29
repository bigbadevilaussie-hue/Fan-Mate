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
    property string guiVersion: "1.04"

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

        // LED row
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 24
            spacing: 34

            Rectangle { width: 12; height: 12; radius: 6
                color: dev.alert == 0 ? "#50e890" : "#0a1a0f"
                border.color: "#50e890"; border.width: 1; antialiasing: true }
            Rectangle { width: 12; height: 12; radius: 6
                color: dev.alert == 1 ? "#ffd23f" : "#1a1608"
                border.color: "#ffd23f"; border.width: 1; antialiasing: true }
            Rectangle { width: 12; height: 12; radius: 6
                color: dev.alert == 2 ? "#ff8a30" : "#1a0e05"
                border.color: "#ff8a30"; border.width: 1; antialiasing: true }
            Rectangle { width: 12; height: 12; radius: 6
                color: dev.alert == 3 ? "#ff304f" : "#1a050a"
                border.color: "#ff304f"; border.width: 1; antialiasing: true }
        }

        // Three dials
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
}
