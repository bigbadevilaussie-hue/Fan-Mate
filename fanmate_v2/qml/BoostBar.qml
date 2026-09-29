import QtQuick

Item {
    id: barRoot

    property int gear: 0   // 0-4

    property color cGreen:  "#2ecc71"
    property color cYellow: "#f1c40f"
    property color cOrange: "#e67e22"
    property color cRed:    "#e74c3c"
    property color cDim:    "#141a1e"

    implicitWidth: 60
    implicitHeight: 340

    readonly property color gearColor:
        gear === 0 ? cDim    :
        gear === 1 ? cGreen  :
        gear === 2 ? cYellow :
        gear === 3 ? cOrange : cRed

    Rectangle {
        id: track
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: label.bottom
        anchors.topMargin: 10
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 10
        width: 28
        radius: 4
        color: barRoot.cDim
        border.color: "#2a2a3a"
        border.width: 1

        Column {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 3
            spacing: 3

            Repeater {
                model: 4   // four segments, bottom = gear 1
                Rectangle {
                    width: parent.width
                    height: (track.height - 3 * 3 - 6) / 4
                    radius: 2
                    color: {
                        var segGear = 4 - index   // bottom segment = gear 1
                        if (barRoot.gear >= segGear) {
                            if (segGear === 1) return barRoot.cGreen
                            if (segGear === 2) return barRoot.cYellow
                            if (segGear === 3) return barRoot.cOrange
                            return barRoot.cRed
                        }
                        return "#0d1216"
                    }
                    border.color: "#1f1f2a"
                    border.width: 1

                    Behavior on color {
                        ColorAnimation { duration: 250 }
                    }
                }
            }
        }
    }

    Text {
        id: label
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 4
        text: "BOOST"
        color: barRoot.gear === 0 ? "#2b2b2b" : barRoot.gearColor
        font.family: "Helvetica Neue"
        font.pixelSize: 10
        font.weight: Font.Bold
        font.letterSpacing: 2
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: track.bottom
        anchors.topMargin: 6
        text: barRoot.gear === 0 ? "N" : String(barRoot.gear)
        color: barRoot.gear === 0 ? "#333333" : barRoot.gearColor
        font.family: "Menlo"
        font.pixelSize: 16
        font.weight: Font.Bold
    }
}
