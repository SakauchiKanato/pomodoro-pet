# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pomodoro_pet.py'],
    pathex=[],
    binaries=[],
    datas=[('Focused_Corgi.png', '.'), ('Hungry_Corgi.png', '.'), ('Satisfaction_Corgi.png', '.')],
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
    name='pomodoro_pet',
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
    icon=['app_icon.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pomodoro_pet',
)
app = BUNDLE(
    coll,
    name='pomodoro_pet.app',
    icon='app_icon.png',
    bundle_identifier=None,
)
