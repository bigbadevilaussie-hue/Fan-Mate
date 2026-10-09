import QtQuick
import QtQuick.Controls

Dialog {
    id: otaDialog
    title: "Update Firmware"
    modal: true
    width: 340
    height: 260
    padding: 12
    anchors.centerIn: parent

    property int  progress: 0
    property string statusMsg: ""
    property bool uploading: false
    property bool done: false

    // Firmware metadata from bridge (evaluated when dialog opens)
    property string srcVer: "?"
    property string devVer: "?"
    property string fwSize: "?"
    property string fwMd5: "?"
    property string fwBuilt: "?"
    property bool   fwStale: false
    property bool   fwExists: false
    property bool   sameVersion: false

    function loadMetadata() {
        otaDialog.srcVer = dev.firmwareSourceVer
        otaDialog.devVer = dev.deviceVersion
        otaDialog.fwSize = dev.firmwareSize
        otaDialog.fwMd5 = dev.firmwareMd5
        otaDialog.fwBuilt = dev.firmwareBuilt
        otaDialog.fwStale = (dev.firmwareStale === "1")
        otaDialog.fwExists = (dev.firmwareExists === "1")
        otaDialog.sameVersion = (otaDialog.srcVer === otaDialog.devVer &&
                                 otaDialog.srcVer !== "?")
        otaDialog.progress = 0
        otaDialog.uploading = false
        otaDialog.done = false
        otaDialog.statusMsg = otaDialog.fwExists ? "" : "No firmware — run Export Compiled Binary first"
    }

    onOpened: loadMetadata()
    onClosed: {
        otaDialog.uploading = false
        otaDialog.done = false
    }

    background: Rectangle {
        color: "#181825"
        border.color: "#313145"
        border.width: 1
        radius: 8
    }

    header: Item {
        height: 40
        Text {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 16
            text: "📡  Update Firmware"
            color: "#89b4fa"
            font.family: "Helvetica Neue"
            font.pixelSize: 15
            font.bold: true
        }
    }

    contentItem: Column {
        spacing: 6

        // Metadata box
        Rectangle {
            width: parent.width
            height: 118
            color: "#232334"
            radius: 6
            border.color: "#313145"
            border.width: 1

            Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 2

                Text {
                    text: "File:        fanmate.ino.bin"
                    color: "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 11
                }
                Text {
                    text: "Size:        " + otaDialog.fwSize
                    color: "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 11
                }
                Text {
                    text: "MD5:         " + otaDialog.fwMd5
                    color: "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 11
                }
                Text {
                    text: "Source ver:  " + otaDialog.srcVer
                    color: "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 11
                }
                Text {
                    text: "Built:       " + otaDialog.fwBuilt
                    color: "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 11
                }
                Text {
                    text: "Device ver:  " + otaDialog.devVer
                    color: "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 11
                }
            }
        }

        // Stale warning
        Text {
            visible: otaDialog.fwStale
            width: parent.width
            text: "⚠  Config.h is newer than the .bin. Re-export before updating."
            color: "#d99a00"
            font.family: "Menlo"
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }

        // Progress bar (visible only while uploading / after done)
        Rectangle {
            width: parent.width
            height: 8
            color: "#141a1e"
            radius: 4
            visible: otaDialog.uploading || otaDialog.done

            Rectangle {
                width: parent.width * (otaDialog.progress / 100.0)
                height: parent.height
                color: otaDialog.progress >= 100 ? "#2ecc71" : "#89b4fa"
                radius: 4
                Behavior on width { NumberAnimation { duration: 150 } }
            }
        }

        // Status line
        Text {
            width: parent.width
            text: otaDialog.statusMsg
            color: otaDialog.statusMsg.indexOf("error") >= 0 ||
                   otaDialog.statusMsg.indexOf("HTTP") >= 0 ? "#e74c3c" : "#7a8194"
            font.family: "Menlo"
            font.pixelSize: 11
            wrapMode: Text.Wrap
            visible: otaDialog.statusMsg !== ""
        }

        // Buttons
        Row {
            spacing: 12
            x: (parent.width - width) / 2

            // No / Close / Hide — left button
            Rectangle {
                width: 100
                height: 34
                radius: 6
                color: noArea.pressed ? "#313145" : "#232334"
                border.color: otaDialog.sameVersion ? "#89b4fa" : "#313145"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: otaDialog.uploading ? "Hide" : (otaDialog.done ? "Close" : "No")
                    color: "#cdd6f4"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 12
                }

                MouseArea {
                    id: noArea
                    anchors.fill: parent
                    onClicked: otaDialog.close()
                }
            }

            // Yes — right button, hidden when uploading or done
            Rectangle {
                width: 100
                height: 34
                radius: 6
                visible: !otaDialog.uploading && !otaDialog.done
                color: yesArea.pressed ? "#1e66f5" : "#232334"
                border.color: otaDialog.sameVersion ? "#313145" : "#89b4fa"
                border.width: 1
                opacity: otaDialog.fwExists ? 1.0 : 0.4

                Text {
                    anchors.centerIn: parent
                    text: "Yes"
                    color: "#cdd6f4"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 12
                    font.bold: true
                }

                MouseArea {
                    id: yesArea
                    anchors.fill: parent
                    enabled: otaDialog.fwExists
                    onClicked: {
                        otaDialog.close()
                        dev.upload_firmware(dev.firmwarePath)
                    }
                }
            }
        }
    }

    Connections {
        target: dev
        function onOtaProgress(pct) { otaDialog.progress = pct }
        function onOtaStatus(msg)   {
            otaDialog.statusMsg = msg
        }
        function onOtaDone() {
            otaDialog.uploading = false
            otaDialog.done = true
            otaDialog.close()
        }
        function onOtaError(msg)    {
            otaDialog.statusMsg = "error: " + msg
            otaDialog.uploading = false
            otaDialog.done = true
        }
    }
}
