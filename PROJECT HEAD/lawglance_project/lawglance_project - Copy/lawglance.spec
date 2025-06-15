# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Specify data files to include
added_files = [
    ('logo/*.png', 'logo'),
    ('src/ui/*.py', 'src/ui'),
    ('.env', '.'),
    ('data/*.docx', 'data'),
    ('data/*.txt', 'data'),
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'streamlit',
        'langchain',
        'langchain_openai',
        'langchain_chroma',
        'docx',
        'pillow'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LawGlance',
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
    icon='logo/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LawGlance',
)
