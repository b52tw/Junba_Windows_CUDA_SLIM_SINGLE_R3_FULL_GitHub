# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules
from pathlib import Path
import site

# CUDA Slim Single EXE build profile for NVIDIA users.
# We intentionally omit Intel OpenVINO Runtime/GenAI/Tokenizers to avoid
# bundling two full ASR inference stacks. All cuDNN 9 engine DLLs are retained
# because pruning them without a real GPU test risks broken CUDA inference.
# GitHub Actions / Windows one-file build spec.
datas = []
binaries = []
hiddenimports = []

for pkg in [
    'faster_whisper',
    'ctranslate2',
    'av',
    'imageio_ffmpeg',
    'google.genai',
    'keyring',
    'docx',
    'platformdirs',
    'huggingface_hub',
    'opencc',
    'numpy',
]:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

for pkg in ['keyring.backends', 'google.genai']:
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# Bundle NVIDIA-provided CUDA 12/cuDNN 9 runtime binaries directly inside ONE EXE.
# The wheels are installed on the Windows GitHub runner (see workflow).
# Do not bundle nvcuda.dll; it comes from the end user's NVIDIA driver.
_cuda_files = {}
for _site in site.getsitepackages():
    _nv = Path(_site) / 'nvidia'
    if not _nv.is_dir():
        continue
    for _module in ('cublas', 'cudnn', 'cuda_runtime'):
        _root = _nv / _module
        for _sub in ('bin', 'lib'):
            _folder = _root / _sub
            if _folder.is_dir():
                for _dll in _folder.glob('*.dll'):
                    if _dll.name.lower() not in _cuda_files:
                        _cuda_files[_dll.name.lower()] = _dll
_cuda_required = ('cublas64_12.dll', 'cublaslt64_12.dll', 'cudnn64_9.dll')
_cuda_missing = [name for name in _cuda_required if name not in _cuda_files]
if _cuda_missing:
    raise RuntimeError('NVIDIA CUDA 12 / cuDNN 9 DLL missing from Windows Python wheels: ' + ', '.join(_cuda_missing))
# Packaging all cuDNN 9 sublibraries is necessary: only bundling cudnn64_9.dll
# can pass an import check but fail at first actual inference.
binaries += [(str(p), 'cuda_libs') for _, p in sorted(_cuda_files.items())]
print(f'[CUDA SLIM SINGLE] bundled {len(_cuda_files)} NVIDIA DLLs to cuda_libs: ' + ', '.join(sorted(_cuda_files)))

hiddenimports += ['app.core.cuda_runtime', 'app.providers.local_whisper', 'app.core.worker']

# De-duplicate to keep the spec deterministic.
hiddenimports = list(dict.fromkeys(hiddenimports))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hooks/runtime_safe_windows.py'],
    excludes=['torch', 'pyannote', 'tensorflow',
              'openvino', 'openvino_genai', 'openvino_tokenizers'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Junba',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version='packaging/version_info.txt',
    manifest='packaging/app.manifest',
)
