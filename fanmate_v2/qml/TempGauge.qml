import QtQuick
import QtQuick.Shapes

Item {
    id: gaugeRoot

    property real value: 0.0
    property real vmin: 18.0
    property real vmax: 38.0

    property real tempGear1: 30.0
    property real tempGear2: 32.0
    property real tempGear3: 34.0
    property real tempGear4: 36.0

    property color accent: "#55d7ff"
    property color accentDim: "#2b9fc7"
    property color cGreen:  "#2ecc71"
    property color cYellow: "#f1c40f"
    property color cOrange: "#e67e22"
    property color cRed:    "#e74c3c"

    implicitWidth: 240
    implicitHeight: 240
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

    function zoneColor(v) {
        if (v < tempGear1) return cGreen
        if (v < tempGear2) return cYellow
        if (v < tempGear3) return cOrange
        if (v < tempGear4) return cRed
        return "#d20f39"    // Critical: deep red, matches StatusLamps tempColors[4]
    }

    readonly property real tickStep: 5
    readonly property int  firstTick: Math.ceil(vmin / tickStep)
    readonly property int  tickCount: Math.max(0, Math.floor(vmax / tickStep) - firstTick + 1)

    readonly property bool hasData: value > 0
    readonly property color valueColor: hasData ? zoneColor(value) : accentDim

    readonly property real needleAngle: angDeg(hasData ? value : vmin)
    property real needlePos: needleAngle
    Behavior on needlePos {
        SpringAnimation { spring: 2.5; damping: 0.3; epsilon: 0.05 }
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
        ShapePath {
            strokeColor: gaugeRoot.cGreen; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.angDeg(gaugeRoot.vmin) + 270
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.tempGear2) - gaugeRoot.angDeg(gaugeRoot.vmin)
            }
        }
        ShapePath {
            strokeColor: gaugeRoot.cYellow; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.angDeg(gaugeRoot.tempGear2) + 270
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.tempGear3) - gaugeRoot.angDeg(gaugeRoot.tempGear2)
            }
        }
        ShapePath {
            strokeColor: gaugeRoot.cOrange; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.angDeg(gaugeRoot.tempGear3) + 270
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.tempGear4) - gaugeRoot.angDeg(gaugeRoot.tempGear3)
            }
        }
        ShapePath {
            strokeColor: gaugeRoot.cRed; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.angDeg(gaugeRoot.tempGear4) + 270
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.vmax) - gaugeRoot.angDeg(gaugeRoot.tempGear4)
            }
        }
    }

    Repeater {
        model: gaugeRoot.tickCount
        Rectangle {
            property real v: (gaugeRoot.firstTick + index) * gaugeRoot.tickStep
            property real d: gaugeRoot.angDeg(v)
            width: 2; height: 16
            color: gaugeRoot.zoneColor(v)
            antialiasing: true
            x: gaugeRoot.xAt(d, gaugeRoot.rArc - 8) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rArc - 8) - height / 2
            rotation: d
            transformOrigin: Item.Center
        }
    }

    Repeater {
        model: gaugeRoot.tickCount
        Rectangle {
            property real v: (gaugeRoot.firstTick + index) * gaugeRoot.tickStep + gaugeRoot.tickStep / 2
            property real d: gaugeRoot.angDeg(v)
            visible: v < gaugeRoot.vmax
            width: 1; height: 8
            color: "#2a3a44"
            antialiasing: true
            x: gaugeRoot.xAt(d, gaugeRoot.rArc - 4) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rArc - 4) - height / 2
            rotation: d
            transformOrigin: Item.Center
        }
    }

    Repeater {
        model: gaugeRoot.tickCount
        Text {
            property real v: (gaugeRoot.firstTick + index) * gaugeRoot.tickStep
            property real d: gaugeRoot.angDeg(v)
            text: v
            color: gaugeRoot.accentDim
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

    Item {
        anchors.centerIn: parent
        width: 1; height: 1
        rotation: gaugeRoot.needlePos
        Rectangle {
            x: -1.5; y: -gaugeRoot.rArc + 12
            width: 3; height: gaugeRoot.rArc - 12
            color: gaugeRoot.valueColor
            antialiasing: true
        }
        Rectangle {
            x: -1; y: -gaugeRoot.rArc + 8
            width: 2; height: 8
            color: gaugeRoot.valueColor
            antialiasing: true; radius: 1
        }
    }


    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: 36
        text: gaugeRoot.hasData
              ? gaugeRoot.value.toFixed(1) + "\u00B0C"
              : "--.-\u00B0C"
        color: gaugeRoot.valueColor
        font.family: "Menlo"
        font.pixelSize: 16
        font.weight: Font.Bold
        z: 10
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: 56
        text: "PHONE"
        color: gaugeRoot.accentDim
        font.family: "Helvetica Neue"
        font.pixelSize: 10
        font.weight: Font.Bold
        font.letterSpacing: 3
    }

    Rectangle {
        anchors.centerIn: parent
        width: 12; height: 12; radius: 6
        color: gaugeRoot.valueColor; antialiasing: true
    }
    Rectangle {
        anchors.centerIn: parent
        width: 4; height: 4; radius: 2
        color: "#000000"; antialiasing: true
    }

}
