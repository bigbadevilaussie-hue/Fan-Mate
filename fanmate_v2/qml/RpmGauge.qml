import QtQuick
import QtQuick.Shapes

Item {
    id: gaugeRoot

    property real value: 3120
    property real vmin: 0
    property real vmax: 5000
    property real warnTemp: 4500      // red zone starts here
    property string label: "FAN RPM"
    property string unit: "x1000"
    property color accent: "#00d4ff"
    property color danger: "#ff0055"

    implicitWidth: 300
    implicitHeight: 300
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
    readonly property real warnAngle: angDeg(warnTemp)

    property real needlePos: needleAngle
    Behavior on needlePos {
        SpringAnimation { spring: 2.5; damping: 0.3; epsilon: 0.05 }
    }
    onNeedleAngleChanged: needlePos = needleAngle

    // --- Dim track ---
    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4
        ShapePath {
            strokeColor: "#1a1a1a"; strokeWidth: 8; fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: 135; sweepAngle: 270
            }
        }
    }

    // --- Red danger zone (before the needle, so needle overlays it) ---
    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4
        ShapePath {
            strokeColor: gaugeRoot.danger; strokeWidth: 8; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.warnAngle + 135
                sweepAngle: 135 - gaugeRoot.warnAngle
            }
        }
    }

    // --- Cyan active arc (0 up to current value, capped at warnAngle) ---
    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4
        visible: gaugeRoot.value > gaugeRoot.vmin
        ShapePath {
            strokeColor: gaugeRoot.accent; strokeWidth: 8; fillColor: "transparent"
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

    // --- Major ticks (every 1000) ---
    Repeater {
        model: [0, 1, 2, 3, 4, 5]
        Rectangle {
            property real d: gaugeRoot.angDeg(modelData * 1000)
            width: 2; height: 12; color: "#666"
            antialiasing: true
            x: gaugeRoot.xAt(d, gaugeRoot.rArc - 8) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rArc - 8) - height / 2
        }
    }

    // --- Minor ticks (every 500) ---
    Repeater {
        model: [500, 1500, 2500, 3500, 4500]
        Rectangle {
            property real d: gaugeRoot.angDeg(modelData)
            width: 1; height: 6; color: "#333"
            antialiasing: true
            x: gaugeRoot.xAt(d, gaugeRoot.rArc - 6) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rArc - 6) - height / 2
        }
    }

    // --- Numbers outside the arc (0 through 5, x1000) ---
    Repeater {
        model: [0, 1, 2, 3, 4, 5]
        Text {
            property real d: gaugeRoot.angDeg(modelData * 1000)
            property real rT: gaugeRoot.rNum
            text: modelData
            color: "#888"
            font.family: "SF Mono"
            font.pixelSize: 14
            font.weight: Font.Medium
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            width: 24; height: 18
            x: gaugeRoot.xAt(d, rT) - width / 2
            y: gaugeRoot.yAt(d, rT) - height / 2
        }
    }

    // --- x1000 label in upper-center ---
    Text {
        text: gaugeRoot.unit
        color: "#555"
        font.family: "SF Mono"
        font.pixelSize: 10
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: gaugeRoot.height * 0.30
    }

    // --- Current value in center ---
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: gaugeRoot.height * 0.40
        text: gaugeRoot.value.toFixed(0)
        color: "#ffffff"
        font.family: "Helvetica Neue"
        font.pixelSize: 36
        font.weight: Font.Light
    }

    // --- Thin tapered needle ---
    Item {
        anchors.centerIn: parent
        width: 1; height: 1
        rotation: gaugeRoot.needlePos

        // Needle shaft
        Rectangle {
            x: -1.5
            y: -gaugeRoot.rArc + 12
            width: 3
            height: gaugeRoot.rArc - 12
            color: gaugeRoot.accent
            antialiasing: true
        }
        // Needle tip (tapered point)
        Rectangle {
            x: -1
            y: -gaugeRoot.rArc + 8
            width: 2
            height: 8
            color: gaugeRoot.accent
            antialiasing: true
            radius: 1
        }
        // Counterweight
        Rectangle {
            x: -2
            y: 0
            width: 4
            height: 16
            color: "#444"
            antialiasing: true
            radius: 2
        }
    }

    // --- Hub (small, simple) ---
    Rectangle {
        anchors.centerIn: parent
        width: 14; height: 14; radius: 7
        color: gaugeRoot.accent
        antialiasing: true
    }
    Rectangle {
        anchors.centerIn: parent
        width: 5; height: 5; radius: 2.5
        color: "#000000"
        antialiasing: true
    }

    // --- Unit label below the gauge ---
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 4
        text: gaugeRoot.label
        color: "#666"
        font.family: "Helvetica Neue"
        font.pixelSize: 11
        font.weight: Font.Medium
        font.letterSpacing: 2
    }
}
