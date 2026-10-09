import QtQuick

Rectangle {
    id: helloPanel
    anchors.fill: parent
    color: "#0a0a12"
    visible: false
    z: 100

    Rectangle {
        anchors.fill: parent
        anchors.margins: 40
        color: "#232334"
        border.color: "#313145"
        border.width: 1
        radius: 10

        Text {
            anchors.centerIn: parent
            text: "Hello Nick"
            color: "#89b4fa"
            font.family: "Helvetica Neue"
            font.pixelSize: 32
            font.bold: true
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
