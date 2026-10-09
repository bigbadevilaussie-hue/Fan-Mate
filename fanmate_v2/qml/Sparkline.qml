import QtQuick
import QtQuick.Shapes

Item {
    id: root

    property real  value: 0
    property bool  valid: true
    property int   maxSamples: 90
    property int   intervalMs: 10000
    property color lineColor: "#55d7ff"

    property real vmin: 0
    property real vmax: 1
    property bool autoScale: true
    property real minSpan: 1
    property real hardMin: -1e9
    property real threshold: NaN
    property bool thresholdInScale: true

    property var  samples: []
    property var  _pts: []
    property real lo: vmin
    property real hi: vmax

    onValidChanged: if (valid) push()

    function push() {
        if (!valid) return
        var s = samples.slice(-(maxSamples - 1))
        s.push(value)
        samples = s
    }

    function rescale() {
        if (!autoScale || samples.length === 0) { lo = vmin; hi = vmax; return }
        var mn = Math.min.apply(null, samples)
        var mx = Math.max.apply(null, samples)
        if (thresholdInScale && !isNaN(threshold)) { mn = Math.min(mn, threshold); mx = Math.max(mx, threshold) }
        var span = Math.max(mx - mn, minSpan) * 1.2
        var mid = (mx + mn) / 2
        lo = Math.max(hardMin, mid - span / 2)
        hi = lo + span
    }
    onSamplesChanged: { _pts = linePoints(); rescale() }
    onVminChanged: rescale()
    onVmaxChanged: rescale()

    function yOf(v) {
        var t = (v - lo) / (hi - lo)
        t = Math.max(0, Math.min(1, t))
        return height - 1 - t * (height - 2)
    }

    function linePoints() {
        var n = samples.length
        var out = []
        if (n < 2 || width <= 0) return out
        var dx = width / (maxSamples - 1)
        var x0 = width - (n - 1) * dx
        for (var i = 0; i < n; i++)
            out.push(Qt.point(x0 + i * dx, yOf(samples[i])))
        return out
    }

    function fillPoints() {
        var p = linePoints()
        if (p.length < 2) return p
        p.push(Qt.point(p[p.length - 1].x, height))
        p.push(Qt.point(p[0].x, height))
        return p
    }

    Timer {
        interval: root.intervalMs
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.push()
    }

    Rectangle {
        visible: !isNaN(root.threshold) && root.threshold >= root.lo && root.threshold <= root.hi
        x: 0; width: parent.width; height: 1
        y: root.yOf(root.threshold)
        color: "#4a5568"
    }

    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4

        ShapePath {
            strokeColor: "transparent"
            fillColor: Qt.rgba(root.lineColor.r, root.lineColor.g, root.lineColor.b, 0.15)
            PathPolyline { path: root.fillPoints() }
        }
        ShapePath {
            strokeColor: root.lineColor
            strokeWidth: 1.5
            fillColor: "transparent"
            joinStyle: ShapePath.RoundJoin
            PathPolyline { path: root.linePoints() }
        }
    }

    Repeater {
        model: root._pts.length
        Rectangle {
            width: 3; height: 3; radius: 1.5
            color: root.lineColor
            x: root._pts[index].x - width / 2
            y: root._pts[index].y - height / 2
        }
    }
}
