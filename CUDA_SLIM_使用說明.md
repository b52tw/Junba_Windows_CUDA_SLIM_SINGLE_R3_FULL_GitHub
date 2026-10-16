# Junba AI Transcriber CUDA Slim（Windows Single EXE）

## 為什麼做精簡版
舊版約 1.6 GB，原因之一是把 NVIDIA CUDA/cuDNN 與 Intel OpenVINO/GenAI/Tokenizers 兩套大型推論堆疊一起封入 PyInstaller onefile。
每次執行 onefile 都需從 EXE 解壓大型 DLL 到暫存資料夾，遇到磁碟防毒掃描可能明顯延遲。

## 保留
- NVIDIA RTX / faster-whisper / CTranslate2 CUDA FP16，完整 CUDA 12 + cuBLAS + cuDNN 9 DLL。
- CPU 備援、Gemini、繁體中文、Word/TXT/Markdown/SRT/VTT、HTML KTV 播放與手動停止輸出。
- 不在 EXE 內嵌 Whisper large-v3 模型：模型由原本機制於使用時下載／讀取。
- Single EXE 一檔執行，Windows 版；不產 Portable、Android。

## 移除（明確取捨）
- Intel GPU/NPU 專用 OpenVINO Runtime、OpenVINO GenAI、OpenVINO Tokenizers。
- 介面上 OpenVINO 選項應因無 runtime 顯示為不可用；這不是缺 DLL 故障。
- 請勿再把上述三個 OpenVINO 套件自行加回 requirements 或 PyInstaller 的 collect_all。

## 編譯
將此 ZIP 解壓的第一層內容上傳 GitHub Repo 根目錄（包含隱藏 `.github` 目錄），在 Actions 選
`Build Junba Windows CUDA Slim - Single EXE only`。
Artifact：`Junba-Windows-CUDA-Slim-Single`，內有 `Junba-CUDA-Slim-Single.exe`、SHA256、`SIZE_REPORT.txt` 等。

編譯完立即上傳 EXE，再跑每項最多 120 秒的 CI 自檢；GUI 自檢可能因 CI 無桌面或 onefile 解壓耗時而警告，請看診斷報告。
GitHub Windows runner 無 NVIDIA GPU，**不能驗證真正 CUDA 推論**。必須在 RTX 電腦「設定 → 執行 GPU 實際推論測試」，看到 PASS 才可確認。

## 體積／速度務實預期
精簡 OpenVINO 預期可節省部分體積，但 cuDNN 9 的多個大型 DLL 仍需保留，無法保證會縮到某個數字。
每次啟動時 onefile 仍需解壓 CUDA DLL；若啟動仍慢，可考慮下一階段改成一個小 EXE 首次啟動下載 CUDA 元件到固定快取（需網路、首用下載，且不是完整離線一檔）。

## 測試
先用 RTX 電腦測 `--cuda-self-test` 或設定頁的 GPU 測試，然後用 1～3 分鐘音檔測 large-v3，檢查是否實際顯示 CUDA 而非 CPU 備援。
