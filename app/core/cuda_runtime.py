"""Windows CUDA 12 / cuDNN 9 loader and actual faster-whisper inference test.

The audit checks packages/DLLs, whereas the inference test proves real execution.
The latter must run on the end user's NVIDIA GPU: GitHub hosted runners normally
have no CUDA GPU and cannot attest real GPU inference.
"""
from __future__ import annotations

import ctypes
import os
import sys
import tempfile
import time
import traceback
import wave
from pathlib import Path

CUDA_REQUIRED = ('cublas64_12.dll', 'cublasLt64_12.dll', 'cudnn64_9.dll')
CUDA_OPTIONAL = ('cudart64_12.dll',)
_DLL_HANDLES: list[object] = []
_LOADED_DIR_HANDLES: list[object] = []


def bundled_cuda_dir() -> Path:
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))
    return base / 'cuda_libs'


def cuda_library_candidates() -> list[Path]:
    """Enumerate bundled and NVIDIA wheel locations (for source-mode tests)."""
    found: list[Path] = []
    bundle = bundled_cuda_dir()
    if bundle.is_dir():
        found.append(bundle)
    # In a frozen EXE, only the EXE's bundled DLLs count. Do not let a
    # GitHub runner's site-packages accidentally mask a broken package.
    if getattr(sys, '_MEIPASS', None) is not None:
        return found
    roots = []
    try:
        import site
        roots.extend(Path(p) for p in site.getsitepackages())
    except Exception:
        pass
    try:
        roots.append(Path(site.getusersitepackages()))
    except Exception:
        pass
    for root in roots:
        nv = root / 'nvidia'
        if not nv.is_dir():
            continue
        for module in ('cublas', 'cudnn', 'cuda_runtime'):
            lib_root = nv / module
            for sub in ('bin', 'lib'):
                d = lib_root / sub
                if d.is_dir() and d not in found:
                    found.append(d)
    return found


def audit_cuda_dlls() -> tuple[bool, str]:
    locations = cuda_library_candidates()
    names = {p.name.lower(): p for root in locations for p in root.glob('*.dll')}
    lines = [f'程式模式：{"Single EXE" if getattr(sys, "frozen", False) else "Python 原始碼"}',
             'CUDA 函式庫資料夾：' + (str(bundled_cuda_dir()) if bundled_cuda_dir().is_dir() else '(無內建; 尋找 NVIDIA wheel)')]
    for name in CUDA_REQUIRED + CUDA_OPTIONAL:
        dll = names.get(name.lower())
        lines.append(f'{"PASS" if dll else ("WARN" if name in CUDA_OPTIONAL else "FAIL")} {name}' + (f'：{dll}' if dll else '：找不到'))
    cudnn_parts = [name for name in names if name.startswith('cudnn_') and name.endswith('64_9.dll')]
    lines.append(f'cuDNN 9 延伸 DLL 數量：{len(cudnn_parts)}')
    ok = all(n.lower() in names for n in CUDA_REQUIRED)
    return ok, '\n'.join(lines)


def configure_cuda_dlls() -> list[str]:
    """Add DLL locations before CTranslate2 is imported; preload only core libs.

    Do not bundle nvcuda.dll: that DLL must be provided by the NVIDIA driver.
    """
    if os.name != 'nt':
        return []
    paths = cuda_library_candidates()
    if not paths:
        return []
    for d in paths:
        if hasattr(os, 'add_dll_directory'):
            try:
                _LOADED_DIR_HANDLES.append(os.add_dll_directory(str(d)))
            except OSError:
                pass
    os.environ['PATH'] = os.pathsep.join(str(d) for d in paths) + os.pathsep + os.environ.get('PATH', '')
    # Win32 LoadLibraryW commonly searches the process DLL directory as well.
    # Use SetDllDirectoryW only on the dedicated onefile bundle, not arbitrary PATHs.
    bundle = bundled_cuda_dir()
    if bundle.is_dir():
        ctypes.windll.kernel32.SetDllDirectoryW(str(bundle))
    errors = []
    dlls = {p.name.lower(): p for d in paths for p in d.glob('*.dll')}
    for name in ('cudart64_12.dll', 'cublasLt64_12.dll', 'cublas64_12.dll'):
        dll = dlls.get(name.lower())
        if dll:
            try:
                _DLL_HANDLES.append(ctypes.WinDLL(str(dll)))
            except OSError as exc:
                errors.append(f'{name}: {exc}')
    return errors


def actual_cuda_inference_test(model_name: str = 'tiny', *, download_if_missing: bool = True) -> tuple[bool, str]:
    """Attempt real CTranslate2 GPU inference using a synthetic PCM WAV.

    `tiny` downloads a small model on first use unless local_files_only=True.
    The output is only an execution proof, not a transcription accuracy test.
    """
    started = time.perf_counter()
    records = []
    audit_ok, audit_report = audit_cuda_dlls()
    records.extend((audit_report,))
    if os.name != 'nt':
        return False, '\n'.join(records + ['FAIL：此測試須在 Windows NVIDIA 顯卡電腦執行。'])
    try:
        dll_errors = configure_cuda_dlls()
        records.extend('DLL preload 提醒：' + item for item in dll_errors)
        if not audit_ok:
            raise RuntimeError('缺少 CUDA 12 cuBLAS 或 cuDNN 9 DLL，請改用包含 GPU runtime 的 Single EXE。')
        import ctranslate2
        count = ctranslate2.get_cuda_device_count()
        records.append(f'CTranslate2 版本：{getattr(ctranslate2, "__version__", "unknown")} / CUDA 裝置：{count}')
        if count < 1:
            raise RuntimeError('CTranslate2 偵測不到 NVIDIA CUDA 顯示卡或驅動。')
        from faster_whisper import WhisperModel
        with tempfile.TemporaryDirectory(prefix='junba_cuda_test_') as td:
            p = Path(td) / 'cuda_test.wav'
            # 2 seconds of harmless silence exercises real model decoding, with VAD off.
            with wave.open(str(p), 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
                w.writeframes(b'\x00\x00' * (16000 * 2))
            records.append(f'正在載入 {model_name}；首次下載模型可能需要網路。')
            model = WhisperModel(model_name, device='cuda', compute_type='float16',
                                 local_files_only=not download_if_missing)
            segments, info = model.transcribe(str(p), language='zh', beam_size=1,
                                              vad_filter=False, condition_on_previous_text=False,
                                              word_timestamps=False)
            _ = list(segments)  # CTranslate2 often performs inference lazily!
            del model
        elapsed = time.perf_counter() - started
        records.append(f'PASS NVIDIA CUDA FP16 實際推論完成；測試耗時 {elapsed:.1f} 秒。')
        return True, '\n'.join(records)
    except BaseException as exc:
        records.append(f'FAIL {type(exc).__name__}: {exc}')
        records.append('完整 traceback：\n' + traceback.format_exc())
        return False, '\n'.join(records)
