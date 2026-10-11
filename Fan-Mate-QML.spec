# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['fanmate_v2/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('fanmate_v2/qml', 'fanmate_v2/qml'),
        ('fanmate.png', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickTemplates2',
        'PySide6.QtQmlModels',
        'PySide6.QtQuickShapes',
        'PySide6.QtQuickLayouts',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'fanmate_v2',
        'fanmate_v2.bridge',
        'fanmate.state',
        'fanmate.http_client',
        'fanmate.weather',
        'fanmate.reports',
        'fanmate.helpers',
        'fanmate.config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebChannel',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Fan-Mate-QML',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Fan-Mate-QML',
)
app = BUNDLE(
    coll,
    name='Fan-Mate-QML.app',
    icon='/tmp/fanmate.icns',
    bundle_identifier='com.fanmate.qml',
    info_plist={'NSHighResolutionCapable': True},
)
