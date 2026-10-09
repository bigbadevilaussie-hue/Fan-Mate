import QtQuick

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
        var arr = (reportData && reportData.net && reportData.net.samples) ? reportData.net.samples : []
        spNet.setSamples(arr)
        visible = true
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 40
        color: "#232334"
        border.color: "#313145"
        border.width: 1
        radius: 10

        Column {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 14

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
                width: parent.width
                height: parent.height - 90
                maxSamples: 120
                intervalMs: 1000000
                value: 0
                valid: false
                lineColor: "#55d7ff"
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
