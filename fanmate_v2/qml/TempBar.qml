import QtQuick

Item {
    id: barRoot

    property int level: 0       // 0-4 heat gear
    property int alertLvl: 0    // 0=idle, 1=delta guard

    implicitWidth: 72
    implicitHeight: 340

    readonly property var names:  ["Normal", "Warm", "Hot", "Hotter", "Critical"]
    readonly property var colors: ["#7a8194", "#f1c40f", "#e67e22", "#e74c3c", "#d20f39"]

    Column {
        anchors.fill: parent
        spacing: 6

        Repeater {
            model: 5

            Rectangle {
                width: parent.width
                height: (parent.height - 4 * 6) / 5
                radius: 6

                // index 0 = top of column = Critical (gear 4)
                // index 4 = bottom = Normal (gear 0)
                readonly property int lampLevel: 4 - index

                // delta guard: light Warm (level 1) in orange
                readonly property bool deltaWarm:
                    barRoot.alertLvl === 1 && barRoot.level === 0
                readonly property bool isWarmSlot: lampLevel === 1

                readonly property bool active:
                    (deltaWarm && isWarmSlot) ||
                    (!deltaWarm && barRoot.level === lampLevel)

                readonly property color baseColor: barRoot.colors[lampLevel]
                readonly property color lampColor:
                    (deltaWarm && isWarmSlot) ? "#e67e22" : baseColor

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
