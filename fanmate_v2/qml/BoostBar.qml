import QtQuick

Item {
    id: barRoot

    property int gear: 0   // 0-4

    implicitWidth: 72
    implicitHeight: 340

    readonly property var names:  ["Parked", "Cruising", "Fast", "Racing", "Nitro"]
    readonly property var colors: ["#7a8194", "#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"]

    Column {
        anchors.fill: parent
        spacing: 6

        Repeater {
            model: 5

            Rectangle {
                width: parent.width
                height: (parent.height - 4 * 6) / 5
                radius: 6

                // index 0 = top of column = Nitro (gear 4)
                // index 4 = bottom = Parked (gear 0)
                readonly property int lampGear: 4 - index
                readonly property bool active: barRoot.gear === lampGear
                readonly property color lampColor: barRoot.colors[lampGear]

                color: active ? lampColor : "#0d1216"
                border.color: active ? lampColor : "#2a2a3a"
                border.width: 1

                Behavior on color {
                    ColorAnimation { duration: 180 }
                }

                Text {
                    anchors.centerIn: parent
                    text: barRoot.names[lampGear]
                    color: active ? "#0d1216" : "#4a5568"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 11
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                }
            }
        }
    }
}
