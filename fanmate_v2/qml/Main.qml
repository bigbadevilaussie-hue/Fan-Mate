import QtQuick
import QtQuick.Window

Window {
    id: root
    width: 1100
    height: 460
    visible: true
    title: "Fan-Mate v2"
    color: "#000000"
    property string guiVersion: "1.03"

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 24
        spacing: 34

        Rectangle { width: 12; height: 12; radius: 6
            color: dev.alert == 0 ? "#50e890" : "#0a1a0f"
            border.color: "#50e890"; border.width: 1; antialiasing: true }
        Rectangle { width: 12; height: 12; radius: 6
            color: dev.alert == 1 ? "#ffd23f" : "#1a1608"
            border.color: "#ffd23f"; border.width: 1; antialiasing: true }
        Rectangle { width: 12; height: 12; radius: 6
            color: dev.alert == 2 ? "#ff8a30" : "#1a0e05"
            border.color: "#ff8a30"; border.width: 1; antialiasing: true }
        Rectangle { width: 12; height: 12; radius: 6
            color: dev.alert == 3 ? "#ff304f" : "#1a050a"
            border.color: "#ff304f"; border.width: 1; antialiasing: true }
    }

    TrafficGauge {
        x: 80
        y: 120
        width: 240
        height: 240
        value: (dev.netKbps || 0) / 1024.0
        vmin: 0
        vmax: 3
        boostThresholdMb: (dev.boostThreshold || 700) / 1024.0
    }

    RpmGauge {
        x: 360
        y: 50
        width: 380
        height: 380
        value: dev.rpm || 0
        vmin: 0
        vmax: 7500
        rpmWarn: 2000
        rpmFast: 4000
        rpmMax: 6000
    }

    TempGauge {
        x: 780
        y: 120
        width: 240
        height: 240
        value: dev.temp || 0
        vmin: 18.0
        vmax: (dev.tempKill || 36.0) + 2.0
        tempWarning: dev.tempWarning || 32.0
        tempPanic:   dev.tempPanic   || 34.0
        tempKill:    dev.tempKill    || 36.0
    }

    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 12
        text: "GUI v" + root.guiVersion + "  ·  FW " + dev.fw
        color: "#333"
        font.family: "Menlo"
        font.pixelSize: 10
    }
}
