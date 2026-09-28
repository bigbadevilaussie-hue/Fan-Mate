import QtQuick
import QtQuick.Window

Window {
    id: root
    width: 1100
    height: 460
    visible: true
    title: "Fan-Mate v2"
    color: "#000000"

    // ---------- LED row ----------
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 24
        spacing: 34

        Rectangle {
            width: 12; height: 12; radius: 6
            color: dev.alert == 0 ? "#50e890" : "#0a1a0f"
            border.color: "#50e890"; border.width: 1
            antialiasing: true
        }
        Rectangle {
            width: 12; height: 12; radius: 6
            color: dev.alert == 1 ? "#ffd23f" : "#1a1608"
            border.color: "#ffd23f"; border.width: 1
            antialiasing: true
        }
        Rectangle {
            width: 12; height: 12; radius: 6
            color: dev.alert == 2 ? "#ff8a30" : "#1a0e05"
            border.color: "#ff8a30"; border.width: 1
            antialiasing: true
        }
        Rectangle {
            width: 12; height: 12; radius: 6
            color: dev.alert == 3 ? "#ff304f" : "#1a050a"
            border.color: "#ff304f"; border.width: 1
            antialiasing: true
        }
    }

    // ---------- three gauges ----------
    BoostGauge {
        x: 80
        y: 130
        width: 240
        height: 240
        value: dev.boostLvl || 0
    }

    RpmGauge {
        x: 360
        y: 70
        width: 380
        height: 380
        value: dev.rpm
        warnRpm: 4500
    }

    TempGauge {
        x: 780
        y: 130
        width: 240
        height: 240
        value: dev.temp || 25.0
        warnTemp: dev.tempWarning || 36.0
    }

    // ---------- footer ----------
    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 12
        text: "FW " + dev.fw
        color: "#333"
        font.family: "Menlo"
        font.pixelSize: 10
    }
}
