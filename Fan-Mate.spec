# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['fanmate.py'],
    pathex=[],
    binaries=[],
    datas=[('fanmate', 'fanmate'), ('fanmate.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Fan-Mate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/tmp/fanmate.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Fan-Mate',
)
app = BUNDLE(
    coll,
    name='Fan-Mate.app',
    icon='/tmp/fanmate.icns',
    bundle_identifier=None,
)
