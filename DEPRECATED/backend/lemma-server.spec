# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Lemma backend server."""

import sys
import os

block_cipher = None

# 收集需要隐藏导入的包
hidden_imports = [
    'chromadb', 'tiktoken', 'pydantic', 'yaml', 'httpx', 'jinja2',
    'matplotlib', 'numpy', 'scipy', 'aiofiles', 'python_multipart',
    'fastapi', 'uvicorn', 'websockets', 'openai',
    'openai._client', 'openai.resources', 'openai.resources.chat',
    'chromadb.api', 'chromadb.utils.embedding_functions',
    'matplotlib.backends.backend_agg',
    'lemma.api.server',
    'lemma.engine.domain',
]

# 收集所有需要的数据文件
datas = []
domains_src = os.path.abspath(os.path.join(SPECPATH, '..', 'domains'))
if os.path.isdir(domains_src):
    datas.append((domains_src, 'domains'))

a = Analysis(
    ['server_main.py'],
    pathex=[os.path.abspath(os.path.join(SPECPATH, 'src'))],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='lemma-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
