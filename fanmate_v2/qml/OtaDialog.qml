import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

Dialog {
    id: otaDialog
    title: "Update Firmware"
    modal: true
    width: 420
    height: 260

    property string selectedPath: ""
    property string selectedSize: ""
    property int    progress: 0
    property string statusMsg: "Choose a .bin file"
    property bool   uploading: false

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
        spacing: 12
        padding: 16

        // File info
        Rectangle {
            width: parent.width
            height: 60
            color: "#232334"
            radius: 6
            border.color: "#313145"
            border.width: 1

            Column {
                anchors.centerIn: parent
                spacing: 2

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: otaDialog.selectedPath === "" ? "No file selected"
                                                        : otaDialog.selectedPath.split("/").pop()
                    color: otaDialog.selectedPath === "" ? "#4a5568" : "#cdd6f4"
                    font.family: "Menlo"
                    font.pixelSize: 12
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: otaDialog.selectedSize
                    color: "#7a8194"
                    font.family: "Menlo"
                    font.pixelSize: 10
                }
            }
        }

        // Pick button
        Rectangle {
            width: parent.width
            height: 36
            radius: 6
            color: pickArea.pressed ? "#313145" : "#232334"
            border.color: "#89b4fa"
            border.width: 1
            opacity: otaDialog.uploading ? 0.4 : 1.0

            Text {
                anchors.centerIn: parent
                text: "Choose fanmate.ino.bin"
                color: "#89b4fa"
                font.family: "Helvetica Neue"
                font.pixelSize: 12
            }

            MouseArea {
                id: pickArea
                anchors.fill: parent
                enabled: !otaDialog.uploading
                onClicked: fileDialog.open()
            }
        }

        // Progress bar
        Rectangle {
            width: parent.width
            height: 8
            color: "#141a1e"
            radius: 4
            visible: otaDialog.uploading || otaDialog.progress > 0

            Rectangle {
                width: parent.width * (otaDialog.progress / 100.0)
                height: parent.height
                color: otaDialog.progress >= 100 ? "#2ecc71" : "#89b4fa"
                radius: 4
                Behavior on width {
                    NumberAnimation { duration: 150 }
                }
            }
        }

        // Status
        Text {
            width: parent.width
            text: otaDialog.statusMsg
            color: otaDialog.statusMsg.indexOf("error") >= 0 ||
                   otaDialog.statusMsg.indexOf("HTTP") >= 0 ? "#e74c3c" : "#7a8194"
            font.family: "Menlo"
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }

        // Buttons
        Row {
            spacing: 10
            anchors.horizontalCenter: parent.horizontalCenter

            Rectangle {
                width: 100
                height: 34
                radius: 6
                color: uploadArea.pressed ? "#1e66f5" : "#232334"
                border.color: "#89b4fa"
                border.width: 1
                opacity: (otaDialog.selectedPath === "" || otaDialog.uploading) ? 0.4 : 1.0

                Text {
                    anchors.centerIn: parent
                    text: otaDialog.uploading ? "Uploading..." : "Upload"
                    color: "#cdd6f4"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 12
                    font.bold: true
                }

                MouseArea {
                    id: uploadArea
                    anchors.fill: parent
                    enabled: otaDialog.selectedPath !== "" && !otaDialog.uploading
                    onClicked: {
                        otaDialog.uploading = true
                        otaDialog.progress = 0
                        otaDialog.statusMsg = "Starting..."
                        dev.upload_firmware(otaDialog.selectedPath)
                    }
                }
            }

            Rectangle {
                width: 100
                height: 34
                radius: 6
                color: closeArea.pressed ? "#313145" : "#232334"
                border.color: "#313145"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: otaDialog.uploading ? "Hide" : "Close"
                    color: "#cdd6f4"
                    font.family: "Helvetica Neue"
                    font.pixelSize: 12
                }

                MouseArea {
                    id: closeArea
                    anchors.fill: parent
                    onClicked: otaDialog.close()
                }
            }
        }
    }

    FileDialog {
        id: fileDialog
        title: "Select Firmware"
        nameFilters: ["Firmware (*.bin)", "All files (*)"]
        currentFolder: "file:///Users/Nick/Documents/Arduino/fanmate/build/esp32.esp32.esp32c3/"
        onAccepted: {
            var path = selectedFile.toString().replace("file://", "")
            otaDialog.selectedPath = path
            // get size via bridge? For now show path
            otaDialog.selectedSize = "ready to upload"
            otaDialog.statusMsg = "Ready"
        }
    }

    // Wire bridge signals
    Connections {
        target: dev
        function onOtaProgress(pct) { otaDialog.progress = pct }
        function onOtaStatus(msg)   {
            otaDialog.statusMsg = msg
            if (msg.indexOf("Done") >= 0) {
                otaDialog.uploading = false
            }
        }
        function onOtaError(msg)    {
            otaDialog.statusMsg = "error: " + msg
            otaDialog.uploading = false
        }
    }
}
