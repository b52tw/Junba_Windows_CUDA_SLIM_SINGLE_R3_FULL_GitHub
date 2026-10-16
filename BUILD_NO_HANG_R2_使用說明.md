# Junba AI Transcriber Windows CUDA Fix｜Single EXE 防卡住完整封包 R2

本 ZIP 可直接解壓並將第一層全部檔案上傳 GitHub Repository 根目錄，毋須另下載其他修補包。

## 本次變更

- 以原 Windows CUDA Fix UTF-8 R1 完整專案為基底。
- 整合「No Hang」GitHub workflow：`.github/workflows/build-windows-cuda-single.yml`。
- CUDA 12/cuDNN 9 相依套件與 DLL 來源檢查保留。
- Windows PyInstaller Onefile 成功後，立即複製並上傳 `Junba-CUDA-Fix-Single.exe` Artifact。
- 三項執行檢查個別最多等 240 秒，失敗會記錄在另一個 Diagnostics Artifact；測試結果可能使 workflow 變紅，但已上傳的 EXE 仍可下載。
- 保留 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8` 避免先前 cp1252 編碼例外。
- 只建置 Windows Single EXE；**沒有** Portable 和 Android 建置作業。

## 建置步驟

1. 新增空白 GitHub Repository（不需初始化 README），將 ZIP 解壓後的第一層所有檔案與隱藏的 `.github` 資料夾上傳到根目錄。
2. Actions → `Build Junba Windows CUDA Fix - Single EXE only (No Hang)` → 執行 workflow。
3. 首先檢查「Upload Single EXE immediately (before smoke tests)」是否打勾。
4. 到執行紀錄 Artifacts 下載 `Junba-Windows-CUDA-Fix-Single`，取得 `Junba-CUDA-Fix-Single.exe`。
5. 如後段 smoke tests 失敗或逾時，可下載 `Junba-Windows-CUDA-Diagnostics` 查看原因，並將報告回傳排查。

**重要限制：** 已用 Python 靜態檢查和 ZIP 完整性檢查驗證封包；並未在 Windows GitHub runner 或你本人 RTX 3060 Ti 上實際跑完完整建置。因此 Artifact 名稱是預定輸出名稱，GPU 推論成功與否須以你實際運作結果為準。

**儲存完整性：** 對這份 ZIP 使用 SHA256 驗證檔比對下載後的值；ZIP SHA 不等於最後 GitHub 編出來的 EXE SHA。
