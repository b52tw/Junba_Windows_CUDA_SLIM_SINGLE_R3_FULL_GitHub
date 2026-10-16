# CUDA Fix Single EXE｜UTF-8 CI 修正版

## 問題與證據

GitHub Actions 在「Verify bundled NVIDIA DLL sources」執行內嵌 Python 時，Windows runner 的 stdout 編碼為 cp1252，`audit_cuda_dlls()` 回傳的中文報告由 `print()` 輸出，導致：

`UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-4`

這次失敗點在 DLL 檢查輸出階段；尚未進入 PyInstaller 編譯，**並不代表 CUDA DLL 實際缺少**。

## 修正

- Windows Job 固定 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`。
- 不再使用 PowerShell here-string pipe 到 `python -`，改執行 `python -X utf8 -m tools.verify_cuda_dlls`。
- 控制台輸出 ASCII-safe，完整中文報告保存在 `r/CUDA_DLL_SOURCES.txt`（UTF-8）。
- 真缺 DLL 仍 `exit 2`，**不會跳過或假裝成功**。
- 保留原 CUDA runtime wheels 安裝、Single EXE、EXE 自測、使用者 RTX 實機自測安排。

## 上傳方式

**建議覆蓋既有 GitHub Repository**：先把這包完整 ZIP 解壓，再上傳根目錄所有檔案；確保 `.github/workflows/build-windows-cuda-single.yml` 在正確路徑。不要把 ZIP 直接當原始碼上傳。選擇既有 Actions `Build Junba Windows CUDA Fix - Single EXE only` 重跑新 commit。

若只想做最小修改，只需要覆蓋：

1. `.github/workflows/build-windows-cuda-single.yml`
2. `tools/verify_cuda_dlls.py`

成功的 GitHub Actions 才會出現 `Junba-Windows-CUDA-Fix-Single`，內含 `Junba-CUDA-Fix-Single.exe`。

## 驗證邊界

Linux 端執行 Python 語法與測試，不等於 GitHub Windows / PyInstaller 建置已成功。GitHub runner 無 NVIDIA 顯卡，無法代替 RTX 3060 Ti 執行真實 CUDA 推論；請在取得 EXE 後跑設定頁 GPU 自測。
