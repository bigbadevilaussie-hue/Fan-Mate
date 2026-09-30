import QtQuick

Item {
    id: barRoot

    property int level: 0   // 0-4

    implicitWidth: 72
    implicitHeight: 340

    readonly property var names:  ["Normal", "Warm", "Hot", "Hotter", "Critical"]
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

                readonly property int lampLevel: 4 - index
                readonly property bool active: barRoot.level === lampLevel
                readonly property color lampColor: barRoot.colors[lampLevel]

                color: active ? lampColor : "#0d1216"
                border.color: active ? lampColor : "#2a2a3a"
                border.width: 1

                Behavior on color {
                    ColorAnimation { duration: 180 }
                }

                Text {
                    anchors.centerIn: parent
                    text: barRoot.names[lampLevel]
                    color: active ? "#0d1216" : "#4a5568"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 10
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                }
            }
        }
    }
}
