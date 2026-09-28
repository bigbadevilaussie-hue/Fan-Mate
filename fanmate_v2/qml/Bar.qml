import QtQuick

Item {
    id: barRoot

    property string label: "NETWORK"
    property real value: 0
    property real vmax: 100
    property real warnFrom: -1
    property string valueText: ""
    property color accent: "#55d7ff"
    property color danger: "#ff304f"
    property color track: "#141a1e"
    property real barHeight: 14

    implicitHeight: labelText.height + barHeight + 10

    Text {
        id: labelText
        text: barRoot.label
        color: barRoot.accent
        font.family: "Helvetica Neue"
        font.pixelSize: 12
        font.weight: Font.Medium
    }

    Rectangle {
        id: trackRect
        anchors.top: labelText.bottom
        anchors.topMargin: 4
        anchors.left: parent.left
        anchors.right: parent.right
        height: barRoot.barHeight
        color: barRoot.track
        border.color: barRoot.accent
        border.width: 1
        radius: 2

        Rectangle {
            visible: barRoot.warnFrom >= 0
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: (parent.width - 2) * ((barRoot.vmax - barRoot.warnFrom) / barRoot.vmax)
            color: barRoot.danger
            opacity: 0.35
            radius: 2
        }

        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: 1
            width: Math.max(0, (parent.width - 2) *
                   Math.min(1, barRoot.value / barRoot.vmax))
            color: barRoot.accent
            radius: 2

            Behavior on width {
                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
            }
        }
    }

    Text {
        anchors.left: trackRect.right
        anchors.leftMargin: 8
        anchors.verticalCenter: trackRect.verticalCenter
        text: barRoot.valueText
        color: "#ffffff"
        font.family: "Menlo"
        font.pixelSize: 12
    }
}
