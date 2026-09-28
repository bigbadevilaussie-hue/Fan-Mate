import QtQuick
import QtQuick.Shapes

Item {
    id: gaugeRoot

    property real value: 0
    property real vmin: 0
    property real vmax: 3
    property color bezel: "#888888"
    property color yellow: "#ffd23f"
    property color orange: "#ff8a30"
    property color red: "#ff304f"

    implicitWidth: 240
    implicitHeight: 240
    readonly property real cx: width / 2
    readonly property real cy: height / 2
    readonly property real rBezel: width / 2 - 4
    readonly property real rArc: rBezel - 14

    function angDeg(v) {
        var c = Math.max(vmin, Math.min(vmax, v))
        return -135 + 270 * (c - vmin) / (vmax - vmin)
    }
    function xAt(deg, r) { return cx + r * Math.sin(deg * Math.PI / 180) }
    function yAt(deg, r) { return cy - r * Math.cos(deg * Math.PI / 180) }

    readonly property color valueColor:
        value >= 2.5 ? red :
        value >= 1.5 ? orange :
        value >= 0.5 ? yellow : "#333"

    readonly property real needleAngle: angDeg(value)
    property real needlePos: needleAngle
    Behavior on needlePos {
        SpringAnimation { spring: 3.0; damping: 0.3; epsilon: 0.05 }
    }
    onNeedleAngleChanged: needlePos = needleAngle

    Rectangle {
        anchors.centerIn: parent
        width: rBezel * 2
        height: rBezel * 2
        radius: rBezel
        color: "transparent"
        border.color: gaugeRoot.bezel
        border.width: 2
        antialiasing: true
    }

    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4
        ShapePath {
            strokeColor: "#141a1e"; strokeWidth: 4; fillColor: "transparent"
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
        visible: gaugeRoot.value > 0
        ShapePath {
            strokeColor: gaugeRoot.valueColor
            strokeWidth: 4
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: 135
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.value) + 135
            }
        }
    }

    Rectangle {
        property real d: gaugeRoot.angDeg(1)
        width: 3; height: 16
        color: gaugeRoot.yellow
        antialiasing: true
        x: gaugeRoot.xAt(d, gaugeRoot.rArc - 8) - width / 2
        y: gaugeRoot.yAt(d, gaugeRoot.rArc - 8) - height / 2
        rotation: d
        transformOrigin: Item.Center
    }

    Rectangle {
        property real d: gaugeRoot.angDeg(2)
        width: 3; height: 16
        color: gaugeRoot.orange
        antialiasing: true
        x: gaugeRoot.xAt(d, gaugeRoot.rArc - 8) - width / 2
        y: gaugeRoot.yAt(d, gaugeRoot.rArc - 8) - height / 2
        rotation: d
        transformOrigin: Item.Center
    }

    Rectangle {
        property real d: gaugeRoot.angDeg(3)
        width: 3; height: 16
        color: gaugeRoot.red
        antialiasing: true
        x: gaugeRoot.xAt(d, gaugeRoot.rArc - 8) - width / 2
        y: gaugeRoot.yAt(d, gaugeRoot.rArc - 8) - height / 2
        rotation: d
        transformOrigin: Item.Center
    }

    Item {
        anchors.centerIn: parent
        width: 1; height: 1
        rotation: gaugeRoot.needlePos
        Rectangle {
            x: -1.5; y: -gaugeRoot.rArc + 10
            width: 3; height: gaugeRoot.rArc - 10
            color: gaugeRoot.valueColor
            antialiasing: true
        }
        Rectangle {
            x: -2; y: 0; width: 4; height: 12
            color: "#3a3a3a"; antialiasing: true; radius: 2
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 10; height: 10; radius: 5
        color: gaugeRoot.valueColor
        antialiasing: true
    }
    Rectangle {
        anchors.centerIn: parent
        width: 4; height: 4; radius: 2
        color: "#000000"; antialiasing: true
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 2
        text: "BOOST"
        color: "#2b9fc7"
        font.family: "Helvetica Neue"
        font.pixelSize: 10
        font.weight: Font.Bold
        font.letterSpacing: 3
    }
}
