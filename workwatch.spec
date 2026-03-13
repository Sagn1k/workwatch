# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for WorkWatch binary build."""

a = Analysis(
    ['workwatch/cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['workwatch', 'workwatch.config', 'workwatch.mail_reader', 'workwatch.parser', 'workwatch.timer', 'workwatch.log_display', 'workwatch.daemon', 'workwatch.notifier'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'email', 'xml', 'pydoc'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='workwatch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
