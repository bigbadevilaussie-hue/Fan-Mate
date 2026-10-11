import QtQuick
import QtQuick.Controls

// Dyna Tune KPI board. Fullscreen overlay like the Serial panel.
// Usage in Main.qml:  DynaTunePanel { id: dynaPanel }   then  dynaPanel.open()
Rectangle {
    id: panel
    anchors.fill: parent
    color: "#0a0a12"
    visible: false
    z: 100

    readonly property var d: dev.dynaTune
    readonly property bool ready: d && d.hasData === true

    function open()  { visible = true; dev.loadDynaTune() }
    function close() { visible = false }

    function statusColor(s) {
        return s === "FAIL" ? "#f38ba8" : s === "WARN" ? "#f9e2af" : "#a6e3a1"
    }
    function statusIcon(s) {
        return s === "FAIL" ? "\u2717" : s === "WARN" ? "\u26a0" : "\u2713"
    }

    // swallow clicks so nothing underneath reacts
    MouseArea { anchors.fill: parent }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 12
        color: "#181825"
        radius: 8
        border.color: "#313145"
        border.width: 1

        // ---------- header ----------
        Item {
            id: header
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 10
            height: 34

            Text {
                text: "\uD83C\uDF9B\uFE0F  Dyna Tune"
                color: "#89b4fa"
                font.family: "Helvetica Neue"
                font.pixelSize: 16
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }

            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8

                Rectangle {
                    width: 80; height: 26; radius: 4
                    color: rArea.pressed ? "#313145" : "#232334"
                    border.color: "#89b4fa"; border.width: 1
                    opacity: dev.dynaTuneLoading ? 0.5 : 1
                    Text {
                        anchors.centerIn: parent
                        text: dev.dynaTuneLoading ? "Loading\u2026" : "Refresh"
                        color: "#cdd6f4"
                        font.family: "Helvetica Neue"; font.pixelSize: 11
                    }
                    MouseArea {
                        id: rArea
                        anchors.fill: parent
                        onClicked: dev.loadDynaTune()
                    }
                }
                Rectangle {
                    width: 60; height: 26; radius: 4
                    color: cArea.pressed ? "#313145" : "#232334"
                    border.color: "#313145"; border.width: 1
                    Text {
                        anchors.centerIn: parent
                        text: "Close"
                        color: "#cdd6f4"
                        font.family: "Helvetica Neue"; font.pixelSize: 11
                    }
                    MouseArea {
                        id: cArea
                        anchors.fill: parent
                        onClicked: panel.close()
                    }
                }
            }
        }

        // ---------- empty / loading ----------
        Text {
            visible: !panel.ready
            anchors.centerIn: parent
            text: dev.dynaTuneLoading ? "Analysing logs\u2026"
                  : (panel.d && panel.d.message ? panel.d.message : "No data yet")
            color: "#7a8194"
            font.family: "Menlo"; font.pixelSize: 12
        }

        // ---------- body ----------
        ScrollView {
            id: scroll
            visible: panel.ready
            anchors.top: header.bottom
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 10
            clip: true
            contentWidth: availableWidth

            Column {
                width: scroll.availableWidth
                spacing: 8

                // meta line
                Text {
                    width: parent.width
                    text: panel.ready
                          ? panel.d.version + "   \u00b7   " + panel.d.window + "   \u00b7   " + panel.d.span
                          : ""
                    color: "#7a8194"
                    font.family: "Menlo"; font.pixelSize: 10
                    wrapMode: Text.WordWrap
                }
                Text {
                    width: parent.width
                    text: panel.ready ? panel.d.filterText : ""
                    color: panel.ready && panel.d.filterOk ? "#a6e3a1" : "#7a8194"
                    font.family: "Menlo"; font.pixelSize: 10
                    wrapMode: Text.WordWrap
                }
                Text {
                    visible: panel.ready && panel.d.lastRec !== ""
                    width: parent.width
                    text: panel.ready ? panel.d.lastRec : ""
                    color: "#89b4fa"
                    font.family: "Menlo"; font.pixelSize: 10
                    wrapMode: Text.WordWrap
                }

                // verdict card
                Rectangle {
                    width: parent.width
                    height: verdictCol.height + 24
                    radius: 6
                    color: "#1e1e2e"
                    border.color: "#313145"; border.width: 1

                    Column {
                        id: verdictCol
                        x: 14; y: 12
                        width: parent.width - 28
                        spacing: 10

                        Row {
                            spacing: 12
                            Text {
                                text: panel.ready ? panel.d.verdict.icon : ""
                                color: panel.ready ? panel.statusColor(panel.d.verdict.status) : "#fff"
                                font.family: "Menlo"; font.pixelSize: 30; font.bold: true
                            }
                            Column {
                                anchors.verticalCenter: parent.verticalCenter
                                Text {
                                    text: "Fan-Mate"
                                    color: "#7a8194"
                                    font.family: "Helvetica Neue"; font.pixelSize: 12
                                }
                                Text {
                                    text: panel.ready ? panel.d.verdict.text : ""
                                    color: panel.ready ? panel.statusColor(panel.d.verdict.status) : "#fff"
                                    font.family: "Helvetica Neue"; font.pixelSize: 20; font.bold: true
                                }
                            }
                        }

                        Row {
                            spacing: 6
                            Repeater {
                                model: panel.ready ? panel.d.pills : []
                                Rectangle {
                                    width: pillText.width + 20
                                    height: 22; radius: 4
                                    color: "#181825"
                                    border.color: panel.statusColor(modelData.status)
                                    border.width: 1
                                    Text {
                                        id: pillText
                                        anchors.centerIn: parent
                                        text: modelData.text
                                        color: panel.statusColor(modelData.status)
                                        font.family: "Helvetica Neue"
                                        font.pixelSize: 11; font.bold: true
                                    }
                                }
                            }
                        }
                    }
                }

                // section cards with chips
                Repeater {
                    model: panel.ready ? panel.d.sections : []
                    Rectangle {
                        width: scroll.availableWidth
                        height: chipFlow.height + 20
                        radius: 6
                        color: "#1e1e2e"
                        border.color: "#313145"; border.width: 1

                        Text {
                            id: secLabel
                            x: 12; y: 10
                            width: 74
                            text: modelData.label
                            color: "#cdd6f4"
                            font.family: "Menlo"; font.pixelSize: 10; font.bold: true
                        }
                        Flow {
                            id: chipFlow
                            x: 90; y: 10
                            width: parent.width - 102
                            spacing: 6
                            Repeater {
                                model: modelData.chips
                                Rectangle {
                                    width: chipText.width + 16
                                    height: 20; radius: 4
                                    color: "#181825"
                                    border.color: panel.statusColor(modelData.status)
                                    border.width: 1
                                    Text {
                                        id: chipText
                                        anchors.centerIn: parent
                                        text: panel.statusIcon(modelData.status) + " " + modelData.label
                                        color: panel.statusColor(modelData.status)
                                        font.family: "Menlo"; font.pixelSize: 10; font.bold: true
                                    }
                                }
                            }
                        }
                    }
                }

                // issues
                Rectangle {
                    visible: panel.ready && panel.d.issues.length > 0
                    width: parent.width
                    height: visible ? issuesCol.height + 24 : 0
                    radius: 6
                    color: "#1e1e2e"
                    border.color: "#313145"; border.width: 1
                    Column {
                        id: issuesCol
                        x: 14; y: 12
                        width: parent.width - 28
                        spacing: 4
                        Text {
                            text: panel.ready ? panel.d.issuesTitle : ""
                            color: "#cdd6f4"
                            font.family: "Helvetica Neue"; font.pixelSize: 12; font.bold: true
                        }
                        Repeater {
                            model: panel.ready ? panel.d.issues : []
                            Row {
                                spacing: 10
                                Text {
                                    width: 80
                                    text: modelData.label
                                    color: panel.statusColor(modelData.severity)
                                    font.family: "Menlo"; font.pixelSize: 11; font.bold: true
                                }
                                Text {
                                    text: modelData.metric
                                    color: "#cdd6f4"
                                    font.family: "Helvetica Neue"; font.pixelSize: 12
                                }
                            }
                        }
                    }
                }

                // recommendations
                Rectangle {
                    visible: panel.ready && panel.d.recs.length > 0
                    width: parent.width
                    height: visible ? recCol.height + 24 : 0
                    radius: 6
                    color: "#1e1e2e"
                    border.color: "#313145"; border.width: 1
                    Column {
                        id: recCol
                        x: 14; y: 12
                        width: parent.width - 28
                        spacing: 4
                        Text {
                            text: "RECOMMENDATIONS"
                            color: "#cdd6f4"
                            font.family: "Helvetica Neue"; font.pixelSize: 12; font.bold: true
                        }
                        Repeater {
                            model: panel.ready ? panel.d.recs : []
                            Text {
                                width: recCol.width
                                text: modelData
                                color: "#cdd6f4"
                                font.family: "Helvetica Neue"; font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }

                Text {
                    width: parent.width
                    text: panel.ready ? panel.d.footer : ""
                    color: "#7a8194"
                    font.family: "Menlo"; font.pixelSize: 10
                }
            }
        }
    }
}
