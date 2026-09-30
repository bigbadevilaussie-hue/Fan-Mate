import QtQuick

Item {
    id: lampRoot

    property int boostLvl: 0
    property int tempLvl: 0
    property int opal: 1
    property int killMode: 0

    implicitWidth: 320
    implicitHeight: 44

    readonly property var zoneColors: ["#7a8194", "#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"]

    // 0 = off (grey), 1 = on (with colour), 2 = amber-warn
    function boostState() {
        return boostLvl >= 1 ? 1 : 0
    }
    function boostColor() {
        return boostLvl >= 1 ? zoneColors[boostLvl] : "#2a2a3a"
    }
    function tempState() {
        return tempLvl >= 1 ? 1 : 0
    }
    function tempColor() {
        return tempLvl >= 1 ? zoneColors[tempLvl] : "#2a2a3a"
    }
    function opalState() {
        return opal === 1 ? 1 : 1   // always on
    }
    function opalColor() {
        return opal === 1 ? "#2ecc71" : "#e74c3c"
    }
    function killState() {
        if (killMode === 1) return 1
        if (killMode === 2) return 2
        return 0
    }
    function killColor() {
        if (killMode === 1) return "#e74c3c"
        if (killMode === 2) return "#f1c40f"
        return "#2a2a3a"
    }

    Row {
        anchors.centerIn: parent
        spacing: 36

        // ---- BOOST ----
        Column {
            spacing: 4
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                width: 14; height: 14; radius: 7
                anchors.horizontalCenter: parent.horizontalCenter
                color: lampRoot.boostColor()
                border.color: lampRoot.boostLvl >= 1 ? lampRoot.boostColor() : "#3a3a48"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "BOOST"
                color: lampRoot.boostLvl >= 1 ? "#cdd6f4" : "#4a5568"
                font.family: "Helvetica Neue"
                font.pixelSize: 8
                font.weight: Font.Bold
                font.letterSpacing: 2
            }
        }

        // ---- TEMP ----
        Column {
            spacing: 4
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                width: 14; height: 14; radius: 7
                anchors.horizontalCenter: parent.horizontalCenter
                color: lampRoot.tempColor()
                border.color: lampRoot.tempLvl >= 1 ? lampRoot.tempColor() : "#3a3a48"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "TEMP"
                color: lampRoot.tempLvl >= 1 ? "#cdd6f4" : "#4a5568"
                font.family: "Helvetica Neue"
                font.pixelSize: 8
                font.weight: Font.Bold
                font.letterSpacing: 2
            }
        }

        // ---- OPAL ----
        Column {
            spacing: 4
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                width: 14; height: 14; radius: 7
                anchors.horizontalCenter: parent.horizontalCenter
                color: lampRoot.opalColor()
                border.color: lampRoot.opalColor()
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "OPAL"
                color: "#8a92a8"
                font.family: "Helvetica Neue"
                font.pixelSize: 8
                font.weight: Font.Bold
                font.letterSpacing: 2
            }
        }

        // ---- KILL ----
        Column {
            spacing: 4
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                width: 14; height: 14; radius: 7
                anchors.horizontalCenter: parent.horizontalCenter
                color: lampRoot.killColor()
                border.color: lampRoot.killMode > 0 ? lampRoot.killColor() : "#3a3a48"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "KILL"
                color: lampRoot.killMode > 0 ? "#cdd6f4" : "#4a5568"
                font.family: "Helvetica Neue"
                font.pixelSize: 8
                font.weight: Font.Bold
                font.letterSpacing: 2
            }
        }
    }
}
