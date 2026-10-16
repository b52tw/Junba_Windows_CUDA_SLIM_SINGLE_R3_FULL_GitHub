from unittest import mock
from pathlib import Path
from tools.verify_cuda_dlls import ascii_safe, main


def test_ascii_safe_report_has_no_non_ascii():
    rendered = ascii_safe('程式模式：Windows - 中文路徑')
    rendered.encode('cp1252', 'strict')
    assert '\\u7a0b' in rendered


def test_cuda_audit_pass_and_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with mock.patch('app.core.cuda_runtime.audit_cuda_dlls', return_value=(True, 'PASS cuBLAS\nGPU 驗證成功')):
        assert main() == 0
    assert (tmp_path/'r/CUDA_DLL_SOURCES.txt').read_text('utf-8').startswith('CUDA_DLL_AUDIT_OK')


def test_cuda_audit_missing_dll_is_still_blocking(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with mock.patch('app.core.cuda_runtime.audit_cuda_dlls', return_value=(False, 'FAIL cudnn64_9.dll 未找到')):
        assert main() == 2
    assert 'CUDA_DLL_AUDIT_FAILED' in (tmp_path/'r/CUDA_DLL_SOURCES.txt').read_text('utf-8')
