# pdf_to_md.spec

# --- IMPORTS ---
import sys
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_data_files

# --- HIDDEN IMPORTS FOR PyMuPDF (fitz) ---
hiddenimports = collect_submodules('fitz')

# --- DATA FILES (examples folder) ---
datas = [
    ('examples', 'examples'),   # (source, destination inside bundle)
]

# --- ANALYSIS ---
a = Analysis(
    ['pdf_to_md.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# --- PYZ ---
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# --- EXECUTABLE ---
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='pdf_to_md',
    debug=False,
    strip=False,
    upx=True,
    console=True,   # set to False if you want a GUI/no console window
)
