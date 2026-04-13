# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['start.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('exporter/templates', 'exporter/templates'),
        ('exporter/static', 'exporter/static'),
    ],
    hiddenimports=[
        'django.contrib.admin.apps',
        'django.contrib.auth.apps',
        'django.contrib.auth.context_processors',
        'django.contrib.contenttypes.apps',
        'django.contrib.sessions.apps', 
        'django.contrib.messages.apps',
        'django.contrib.messages.context_processors',
        'django.contrib.messages.middleware', 
        'django.contrib.sessions.middleware', 
        'django.contrib.sessions.serializers', 
        'django.contrib.staticfiles.apps',
        'django.template.loaders', 
    ],
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
    a.binaries,
    a.datas,
    [],
    name='Fluxx Exporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
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
