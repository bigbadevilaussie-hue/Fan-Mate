"""
Fan-Mate GUI v2 — launcher.
Run: python3 -m fanmate_v2.main
"""

import sys
import os
import signal

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from fanmate_v2.bridge import Bridge


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    bridge = Bridge()
    engine.rootContext().setContextProperty("dev", bridge)

    if getattr(sys, "frozen", False):
        # Nuitka / PyInstaller bundle: QML files are extracted next to the exe
        qml_path = os.path.join(os.path.dirname(sys.executable), "Main.qml")
    else:
        qml_path = os.path.join(os.path.dirname(__file__), "qml", "Main.qml")
    print("Loading:", qml_path)
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        print("ERROR: QML failed to load")
        sys.exit(-1)

    print("Window loaded, running...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
