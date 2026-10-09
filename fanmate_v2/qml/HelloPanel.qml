import QtQuick
import QtQuick.Layouts

Rectangle {
    id: helloPanel
    anchors.fill: parent
    color: "#0a0a12"
    visible: false
    z: 100

    property var reportData: ({})

    function open() {
        var raw = dev.report2hJson()
        try { reportData = JSON.parse(raw) } catch (e) { reportData = ({}) }
        var netArr = (reportData && reportData.net && reportData.net.samples) ? reportData.net.samples : []
        var fanArr = (reportData && reportData.fan && reportData.fan.samples) ? reportData.fan.samples : []
        spNet.setSamples(netArr)
        spFan.setSamples(fanArr)
        visible = true
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 14
        color: "#232334"
        border.color: "#313145"
        border.width: 1
        radius: 10

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 6

            Text {
                text: "Last 2 Hours  ·  Network KB/s"
                color: "#89b4fa"
                font.family: "Helvetica Neue"
                font.pixelSize: 16
                font.bold: true
            }

            Text {
                text: (reportData && reportData.start ? reportData.start : "--:--")
                      + "  \u2013  "
                      + (reportData && reportData.end ? reportData.end : "--:--")
                      + "     peak "
                      + ((reportData && reportData.net && reportData.net.peak) || 0)
                      + "   avg "
                      + ((reportData && reportData.net && reportData.net.avg) || 0)
                color: "#7a8194"
                font.family: "Menlo"
                font.pixelSize: 11
            }

            Sparkline {
                id: spNet
                Layout.fillWidth: true
                Layout.fillHeight: true
                maxSamples: 120
                intervalMs: 1000000
                value: 0
                valid: false
                lineColor: "#55d7ff"
                autoScale: true
                minSpan: 1
                hardMin: 0
            }

            Text {
                text: "Fan %  ·  peak "
                      + ((reportData && reportData.fan && reportData.fan.peak) || 0)
                      + "   on "
                      + ((reportData && reportData.fan && reportData.fan.on_pct) || 0) + "%"
                color: "#7a8194"
                font.family: "Menlo"
                font.pixelSize: 11
            }

            Sparkline {
                id: spFan
                Layout.fillWidth: true
                Layout.preferredHeight: 80
                Layout.minimumHeight: 60
                maxSamples: 120
                intervalMs: 1000000
                value: 0
                valid: false
                lineColor: "#2ecc71"
                autoScale: true
                minSpan: 1
                hardMin: 0
            }
        }

        Rectangle {
            id: closeBtn
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: 12
            width: 28; height: 28; radius: 6
            color: closeArea.pressed ? "#313145" : "transparent"
            border.color: "#313145"
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: "\u2715"
                color: "#cdd6f4"
                font.pixelSize: 14
            }

            MouseArea {
                id: closeArea
                anchors.fill: parent
                onClicked: helloPanel.visible = false
            }
        }
    }
}
