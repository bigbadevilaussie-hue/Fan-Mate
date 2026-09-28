import QtQuick
import QtQuick.Shapes

Item {
    id: gaugeRoot

    property real value: 3120
    property real vmin: 0
    property real vmax: 5000
    property real warnRpm: 4500
    property color accent: "#55d7ff"
    property color accentDim: "#2b9fc7"
    property color danger: "#ff304f"

    implicitWidth: 320
    implicitHeight: 320
    readonly property real cx: width / 2
    readonly property real cy: height / 2
    readonly property real rArc: width / 2 - 42
    readonly property real rNum: rArc + 24
    readonly property real startDeg: -135
    readonly property real sweepDeg: 270

    function angDeg(v) {
        var c = Math.max(vmin, Math.min(vmax, v))
        return startDeg + sweepDeg * (c - vmin) / (vmax - vmin)
    }
    function xAt(deg, r) { return cx + r * Math.sin(deg * Math.PI / 180) }
    function yAt(deg, r) { return cy - r * Math.cos(deg * Math.PI / 180) }

    readonly property real needleAngle: angDeg(value)
    readonly property real warnAngle: angDeg(warnRpm)

    property real needlePos: needleAngle
    Behavior on needlePos {
        SpringAnimation { spring: 2.5; damping: 0.3; epsilon: 0.05 }
    }
    onNeedleAngleChanged: needlePos = needleAngle

    readonly property real glowAmount: Math.max(0, Math.min(1,
        (value - vmin) / (vmax - vmin)))

    Rectangle {
        anchors.centerIn: parent
        width: parent.width * 1.35
        height: parent.height * 1.35
        radius: width / 2
        opacity: gaugeRoot.glowAmount * 0.14
        gradient: Gradient {
            GradientStop { position: 0.0
                color: gaugeRoot.value >= gaugeRoot.warnRpm
                       ? gaugeRoot.danger : gaugeRoot.accent }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }

    Repeater {
        model: [0, 1, 2, 3, 4, 5]
        Text {
            property real d: gaugeRoot.angDeg(modelData * 1000)
            property bool isWarn: (modelData * 1000) >= gaugeRoot.warnRpm
            text: modelData
            color: isWarn ? gaugeRoot.danger : gaugeRoot.accentDim
            font.family: "Menlo"
            font.pixelSize: 12
            font.weight: Font.Medium
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            width: 30; height: 18
            x: gaugeRoot.xAt(d, gaugeRoot.rNum) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rNum) - height / 2
        }
    }

    Repeater {
        model: [0, 1000, 2000, 3000, 4000, 5000]
        Rectangle {
            property real d: gaugeRoot.angDeg(modelData)
            property bool isWarn: modelData >= gaugeRoot.warnRpm
            width: 2; height: 16
            color: isWarn ? gaugeRoot.danger : gaugeRoot.accentDim
            antialiasing: true
            x: gaugeRoot.xAt(d, gaugeRoot.rArc - 8) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rArc - 8) - height / 2
            rotation: d
            transformOrigin: Item.Center
        }
    }

    Repeater {
        model: [500, 1500, 2500, 3500, 4500]
        Rectangle {
            property real d: gaugeRoot.angDeg(modelData)
            property bool isWarn: modelData >= gaugeRoot.warnRpm
            width: 1; height: 8
            color: isWarn ? gaugeRoot.danger : "#2a3a44"
            antialiasing: true
            x: gaugeRoot.xAt(d, gaugeRoot.rArc - 4) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rArc - 4) - height / 2
            rotation: d
            transformOrigin: Item.Center
        }
    }

    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4
        ShapePath {
            strokeColor: "#141a1e"; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: 135; sweepAngle: 270
            }
        }
    }

    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4
        visible: gaugeRoot.value > gaugeRoot.vmin
        ShapePath {
            strokeColor: gaugeRoot.accent; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: 135
                sweepAngle: Math.min(
                    gaugeRoot.warnAngle + 135,
                    gaugeRoot.angDeg(gaugeRoot.value) + 135)
            }
        }
    }

    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4
        visible: gaugeRoot.value > gaugeRoot.warnRpm
        ShapePath {
            strokeColor: gaugeRoot.danger; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.warnAngle + 135
                sweepAngle: 135 - gaugeRoot.warnAngle
            }
        }
    }

    Item {
        anchors.centerIn: parent
        width: 1; height: 1
        rotation: gaugeRoot.needlePos
        Rectangle {
            x: -1.5; y: -gaugeRoot.rArc + 12
            width: 3; height: gaugeRoot.rArc - 12
            color: gaugeRoot.value >= gaugeRoot.warnRpm
                   ? gaugeRoot.danger : gaugeRoot.accent
            antialiasing: true
        }
        Rectangle {
            x: -1; y: -gaugeRoot.rArc + 8
            width: 2; height: 8
            color: gaugeRoot.value >= gaugeRoot.warnRpm
                   ? gaugeRoot.danger : gaugeRoot.accent
            antialiasing: true; radius: 1
        }
        Rectangle {
            x: -2; y: 0; width: 4; height: 14
            color: "#3a3a3a"; antialiasing: true; radius: 2
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 12; height: 12; radius: 6
        color: gaugeRoot.value >= gaugeRoot.warnRpm
               ? gaugeRoot.danger : gaugeRoot.accent
        antialiasing: true
    }
    Rectangle {
        anchors.centerIn: parent
        width: 4; height: 4; radius: 2
        color: "#000000"; antialiasing: true
    }

    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 2
        spacing: 2

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "FAN"
            color: gaugeRoot.accentDim
            font.family: "Helvetica Neue"
            font.pixelSize: 10
            font.weight: Font.Bold
            font.letterSpacing: 3
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: gaugeRoot.value.toFixed(0) + " RPM"
            color: "#ffffff"
            font.family: "Helvetica Neue"
            font.pixelSize: 26
            font.weight: Font.Light
        }
    }
}
