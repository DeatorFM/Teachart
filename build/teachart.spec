# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Project root directory
project_root = os.path.abspath('.')

# Collect all data files from resources
datas = [
    ('resources/icons', 'resources/icons'),
    ('resources/images', 'resources/images'),
    ('resources/svg', 'resources/svg'),
    ('resources/themes/compiled', 'resources/themes/compiled'),
    ('resources/themes/packed', 'resources/themes/packed'),
    ('source/resources/about.html', 'source/resources'),
    ('source/tcha/unicodechart.json', 'source/tcha'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'PyQt6.QtMultimedia',
    'source.tcha',
    'source.themes',
    'source.ui',
    'source.nativeelements',
    'source.resources',
]

# Analysis: what files to include
a = Analysis(
    ['source/main.py'],              # Entry point
    pathex=[project_root],            # Additional paths to search
    binaries=[],                      # Binary dependencies (DLLs, etc.)
    datas=datas,                      # Data files to include
    hiddenimports=hiddenimports,      # Modules to force-include
    hookspath=[],                     # Custom hook directories
    hooksconfig={},                   # Hook configuration
    runtime_hooks=[],                 # Scripts to run at startup
    excludes=[                        # Modules to exclude
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'setuptools',
        'test',
        'tests',
        'PySide6',                    # Exclude PySide6 (dev tools only)
    ],
    noarchive=False,
    optimize=0,
)

# PYZ: Create Python archive
pyz = PYZ(a.pure)

# EXE: Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Teachart',                  # Executable name
    debug=False,                      # Set True for debugging
    bootloader_ignore_signals=False,
    strip=False,                      # Don't strip symbols (keep for debugging)
    upx=True,                         # Use UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                    # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app.ico',   # Application icon (create if needed)
    version_file=None,                # Version info (optional, see below)
)

# COLLECT: For --onedir mode (uncomment if you want folder distribution)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='Teachart',
# )