# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files
# -----------------------------
# Playwright browser path (Windows)
# -----------------------------
playwright_cache = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'ms-playwright')

# Collect mermaid_cli data files (templates)
mermaid_datas = collect_data_files('mermaid_cli')

# Collect all files from Playwright cache
playwright_datas = []
if os.path.exists(playwright_cache):
    for root, dirs, files in os.walk(playwright_cache):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(root, playwright_cache)
            target_path = os.path.join('playwright', rel_path)
            playwright_datas.append((full_path, target_path))

a = Analysis(
    ['login_page.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('styles', 'styles'),
        ('datas','datas')
    ] + mermaid_datas,
    hiddenimports=[
        # Required SciPy internals for skimage.metrics
        'scipy._lib._ccallback_c',
        'scipy._lib._testutils',
        'scipy._lib.messagestream',
        'scipy.linalg._cythonized_array_utils',
        'scipy._cyutility',

        # Playwright modules
        'playwright',
        'playwright.sync_api',
        'playwright._impl._driver',
        'playwright._impl._browser',
        'playwright._impl._page',
        'playwright._impl._connection',
        'playwright._impl._api_structures',
        'playwright._impl._network',
        'playwright._impl._fetch',
        'playwright._impl._events',
        'playwright._impl._input',
        'playwright._impl._path_utils',
        'playwright._impl._sync_base',
        'playwright._impl._transport',

        # Mermaid CLI modules
        'mermaid_cli',
        'mermaid_cli.mermaid',
        'mermaid_cli.playwright_renderer',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['onnx', 'onnx.reference'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AgentFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=['icon_3.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AgentFlow',
)

