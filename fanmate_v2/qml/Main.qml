import QtQuick
import QtQuick.Window

Window {
    id: root
    width: 900
    height: 500
    visible: true
    title: "Fan-Mate v2"
    color: "#000000"

    TempGauge {
        anchors.centerIn: parent
        width: 280
        height: 280
        value: dev.temp || 25.0
        warnTemp: dev.tempWarning || 36.0
    }

    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 20
        text: "GUI 4.0 · FW " + dev.fw
        color: "#444"
        font.family: "Helvetica Neue"
        font.pixelSize: 10
    }
}
