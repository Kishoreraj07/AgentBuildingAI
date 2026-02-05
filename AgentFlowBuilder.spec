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
        ('font', 'font'),
        ('gif', 'gif'),
        ('Icon', 'Icon'),
        ('json_info', 'json_info'),
        ('sound', 'sound'),
        ('styles', 'styles'),
        ('xpath_find.py', '.'),
        ('code_skeleton.py','.'),
        ('element_confirmation.py', '.'),
        ('verify_xpath.py', '.'),
        ('config.py', '.'),
        ('web_element_picker.py', '.'),
        ('style_loader.py', '.'),
        ('create_desktop_process.py', '.'),
        # Add the entire desktop_process folder with proper structure
        ('desktop_process', 'desktop_process'),
        # Add the entire native_process folder with proper structure
        ('native_process', 'native_process'),
        # Add individual files to ensure they're included in the desktop_process folder
        ('desktop_process/Desktop_code_skeleton_backup.py', 'desktop_process'),
        ('desktop_process/desktop_element_confirmation.py', 'desktop_process'),
        ('desktop_process/desktop_element_picker.py', 'desktop_process'),
        ('desktop_process/desktop_interact_element.py', 'desktop_process'),
        ('desktop_process/verify_desktop_attr.py', 'desktop_process'),
        ('desktop_process/Attributes_correction.py', 'desktop_process'),
        ('desktop_process/desktop_attr_find.py', 'desktop_process'),
        ('desktop_process/desktop_code_chat.py', 'desktop_process'),
        ('desktop_process/Desktop_code_skeleton.py', 'desktop_process'),
    ] + mermaid_datas,
    hiddenimports=[
        # Existing modules
        'xpath_find',
        'code_skeleton',
        'element_confirmation',
        'verify_xpath',
        'config',
        'web_element_picker',
        'style_loader',
        'create_desktop_process',

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

        # Desktop process modules
        'desktop_process',
        'desktop_process.Desktop_code_skeleton_backup',
        'desktop_process.desktop_element_confirmation',
        'desktop_process.desktop_element_picker',
        'desktop_process.desktop_interact_element',
        'desktop_process.verify_desktop_attr',
        'desktop_process.Attributes_correction',
        'desktop_process.desktop_attr_find',
        'desktop_process.desktop_code_chat',
        'desktop_process.Desktop_code_skeleton',
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
    a.binaries,
    a.datas,
    [],
    name='AgentFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon_3.ico'],
)
