"""ASCII-safe GitHub Windows DLL audit. UTF-8 full report is saved to disk."""
from __future__ import annotations

import sys
from pathlib import Path


def ascii_safe(value: str) -> str:
    # Even if the host console is cp1252, this never raises UnicodeEncodeError.
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    out = Path("r/CUDA_DLL_SOURCES.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        from app.core.cuda_runtime import audit_cuda_dlls
        ok, report = audit_cuda_dlls()
    except Exception as exc:
        ok, report = False, f"FAIL DLL audit raised {type(exc).__name__}: {exc}"
    out.write_text(("CUDA_DLL_AUDIT_OK\n" if ok else "CUDA_DLL_AUDIT_FAILED\n") + report + "\n", encoding="utf-8")
    # stdout may use a legacy Windows code page: keep the log readable and safe.
    print(ascii_safe(report), flush=True)
    print("CUDA DLL sources: PASS" if ok else "CUDA DLL sources: FAIL (see r/CUDA_DLL_SOURCES.txt)", flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
