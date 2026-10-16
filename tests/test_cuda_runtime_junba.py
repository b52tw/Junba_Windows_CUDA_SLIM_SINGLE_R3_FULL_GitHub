"""Hardware-independent tests; actual CUDA must be tested on user's GPU."""
import os
from pathlib import Path
from unittest import mock

from app.core.cuda_runtime import CUDA_REQUIRED, audit_cuda_dlls, configure_cuda_dlls


def test_audit_find_all_required_dlls(tmp_path):
    for name in CUDA_REQUIRED:
        (tmp_path / name).write_bytes(b'dummy')
    with mock.patch('app.core.cuda_runtime.cuda_library_candidates', return_value=[tmp_path]), \
         mock.patch('app.core.cuda_runtime.bundled_cuda_dir', return_value=tmp_path):
        okay, report = audit_cuda_dlls()
        assert okay
        assert 'PASS cudnn64_9.dll' in report


def test_audit_missing_libs_fails(tmp_path):
    with mock.patch('app.core.cuda_runtime.cuda_library_candidates', return_value=[tmp_path]):
        okay, report = audit_cuda_dlls()
        assert not okay
        assert 'FAIL cublas64_12.dll' in report


def test_configure_non_windows_is_noop():
    if os.name != 'nt':
        assert configure_cuda_dlls() == []


def test_worker_gpu_error_keeps_exception_message():
    worker = Path(__file__).resolve().parents[1] / 'app' / 'core' / 'worker.py'
    data = worker.read_text(encoding='utf-8')
    assert 'NVIDIA CUDA 推論失敗：{type(exc).__name__}: {exc}' in data


def test_single_spec_does_not_contain_portable_output():
    spec = Path(__file__).resolve().parents[1] / 'JunbaAITranscriber_onefile.spec'
    content = spec.read_text(encoding='utf-8')
    assert "binaries += [(str(p), 'cuda_libs')" in content
    assert 'COLLECT(' not in content
