import QtQuick

Rectangle {
    id: btn
    width: parent.width
    height: 40
    radius: 6
    color: area.pressed ? "#2a2a3a" : "transparent"

    property string text: ""
    property color textColor: "#cdd6f4"

    signal triggered()

    Text {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 10
        text: btn.text
        color: btn.textColor
        font.family: "Helvetica Neue"
        font.pixelSize: 13
    }

    MouseArea {
        id: area
        anchors.fill: parent
        onClicked: btn.triggered()
    }
}
