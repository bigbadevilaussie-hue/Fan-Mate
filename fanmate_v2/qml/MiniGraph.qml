import QtQuick

Item {
    id: g

    property string dataJson: "[]"
    property real vmin: 0
    property real vmax: 100
    property real threshold: -1
    property color lineColor: "#2ecc71"
    property color fillColor: Qt.rgba(0.18, 0.80, 0.44, 0.18)
    property color thresholdColor: "#e74c3c"
    property real lineWidth: 2

    property var _data: []

    onDataJsonChanged: {
        try { _data = JSON.parse(dataJson) } catch (e) { _data = [] }
        canvas.requestPaint()
    }

    Canvas {
        id: canvas
        anchors.fill: parent

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)

            var data = g._data
            if (!data || data.length < 2) return

            var w = width
            var h = height
            var range = g.vmax - g.vmin
            if (range <= 0) range = 1

            // threshold line
            if (g.threshold >= g.vmin && g.threshold <= g.vmax) {
                var ty = h - ((g.threshold - g.vmin) / range) * h
                ctx.strokeStyle = g.thresholdColor
                ctx.lineWidth = 1
                ctx.setLineDash([4, 3])
                ctx.beginPath()
                ctx.moveTo(0, ty)
                ctx.lineTo(w, ty)
                ctx.stroke()
                ctx.setLineDash([])
            }

            // build points
            var pts = []
            var n = data.length
            for (var i = 0; i < n; i++) {
                var v = data[i]
                if (v === null || v === undefined) continue
                var x = (i / Math.max(1, n - 1)) * w
                var y = h - ((v - g.vmin) / range) * h
                if (y < 0) y = 0
                if (y > h) y = h
                pts.push([x, y])
            }
            if (pts.length < 2) return

            // fill
            ctx.beginPath()
            ctx.moveTo(pts[0][0], h)
            for (var j = 0; j < pts.length; j++) ctx.lineTo(pts[j][0], pts[j][1])
            ctx.lineTo(pts[pts.length - 1][0], h)
            ctx.closePath()
            ctx.fillStyle = g.fillColor
            ctx.fill()

            // line
            ctx.beginPath()
            ctx.moveTo(pts[0][0], pts[0][1])
            for (var k = 1; k < pts.length; k++) ctx.lineTo(pts[k][0], pts[k][1])
            ctx.strokeStyle = g.lineColor
            ctx.lineWidth = g.lineWidth
            ctx.lineJoin = "round"
            ctx.lineCap = "round"
            ctx.stroke()

            // last point dot
            var lp = pts[pts.length - 1]
            ctx.beginPath()
            ctx.arc(lp[0] - 2, lp[1], 3, 0, Math.PI * 2)
            ctx.fillStyle = g.lineColor
            ctx.fill()
        }
    }

    // redraw on size change
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()

    // redraw on colour change
    onLineColorChanged: canvas.requestPaint()
    onFillColorChanged: canvas.requestPaint()
    onThresholdChanged: canvas.requestPaint()
    onVminChanged: canvas.requestPaint()
    onVmaxChanged: canvas.requestPaint()
}
