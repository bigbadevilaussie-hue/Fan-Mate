import QtQuick
import QtQuick.Shapes

Item {
    id: gaugeRoot

    property real value: 0.0
    property real vmin: 0.0
    property real vmax: 7500.0

    property real rpmWarn:  3000.0
    property real rpmFast:  4500.0
    property real rpmMax:   6000.0

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
    readonly property real rArc: width / 2 - 17
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
        if (v < rpmWarn) return cGreen
        if (v < rpmFast) return cYellow
        if (v < rpmMax)  return cOrange
        return cRed
    }

    readonly property bool hasData: true
    readonly property color valueColor: zoneColor(value)

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
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.rpmWarn) - gaugeRoot.angDeg(gaugeRoot.vmin)
            }
        }
        ShapePath {
            strokeColor: gaugeRoot.cYellow; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.angDeg(gaugeRoot.rpmWarn) + 270
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.rpmFast) - gaugeRoot.angDeg(gaugeRoot.rpmWarn)
            }
        }
        ShapePath {
            strokeColor: gaugeRoot.cOrange; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.angDeg(gaugeRoot.rpmFast) + 270
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.rpmMax) - gaugeRoot.angDeg(gaugeRoot.rpmFast)
            }
        }
        ShapePath {
            strokeColor: gaugeRoot.cRed; strokeWidth: 6; fillColor: "transparent"
            capStyle: ShapePath.FlatCap
            PathAngleArc {
                centerX: gaugeRoot.cx; centerY: gaugeRoot.cy
                radiusX: gaugeRoot.rArc; radiusY: gaugeRoot.rArc
                startAngle: gaugeRoot.angDeg(gaugeRoot.rpmMax) + 270
                sweepAngle: gaugeRoot.angDeg(gaugeRoot.vmax) - gaugeRoot.angDeg(gaugeRoot.rpmMax)
            }
        }
    }

    Repeater {
        model: [1, 2, 3, 4, 5, 6, 7]
        Rectangle {
            property real d: gaugeRoot.angDeg(modelData * 1000)
            width: 2; height: 9
            color: gaugeRoot.zoneColor(modelData * 1000)
            antialiasing: true
            x: gaugeRoot.xAt(d, gaugeRoot.rArc + 10) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rArc + 10) - height / 2
            rotation: d
            transformOrigin: Item.Center
        }
    }

    Repeater {
        model: [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
        Rectangle {
            property real d: gaugeRoot.angDeg(modelData * 1000)
            width: 1; height: 5
            color: "#3d5565"
            antialiasing: true
            x: gaugeRoot.xAt(d, gaugeRoot.rArc + 8) - width / 2
            y: gaugeRoot.yAt(d, gaugeRoot.rArc + 8) - height / 2
            rotation: d
            transformOrigin: Item.Center
        }
    }

    Repeater {
        model: [1, 2, 3, 4, 5, 6, 7]
        Text {
            property real d: gaugeRoot.angDeg(modelData * 1000)
            text: modelData
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
        anchors.verticalCenterOffset: 78
        text: gaugeRoot.value.toFixed(0) + " RPM"
        color: gaugeRoot.valueColor
        font.family: "Menlo"
        font.pixelSize: 11
        font.weight: Font.Medium
        z: 10
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: 94
        text: "FAN"
        color: gaugeRoot.accentDim
        font.family: "Menlo"
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
