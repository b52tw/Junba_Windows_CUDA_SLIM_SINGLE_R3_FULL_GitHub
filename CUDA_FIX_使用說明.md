# 峻爸 AI Transcriber v3.8.2｜Windows CUDA Fix（只建 Single EXE）

此為**完整 GitHub 原始碼封包**，不是已在本機編譯完成的 Windows `.exe`。因製作端不是 NVIDIA Windows 電腦，無法在這裡證明 RTX 3060 Ti 實際推論成功。GitHub Actions 會於 Windows 上建置 Single EXE、驗證包入 DLL；使用者電腦上的 GPU 實際測試，則從「設定 → 執行 GPU 實際推論測試」完成。

## 修改範圍

- Windows 版：GPU DLL 封裝、CUDA FP16 真推論測試、錯誤完整記錄及 CPU 備援。
- Windows 版保留 Gemini、OpenVINO、繁體中文輸出、KTV HTML、暫停和安全停止等原有功能。
- **沒有 Portable 建置，沒有 Android APK 原始碼或建置工作**。
- EXE 不內含 Whisper 模型檔；首次 CUDA 測試會下載 tiny 模型，正式辨識原本的模型選擇機制保持不變。

## GitHub 建置步驟

1. 建議建立一個新 Repository；**解壓後將第一層全部上傳到 Repository 根目錄**。不要上傳外層 ZIP 本身。
2. 確認有 `.github/workflows/build-windows-cuda-single.yml`、根目錄 `main.py`、`requirements.txt`、`JunbaAITranscriber_onefile.spec`。
3. Actions 選擇 **Build Junba Windows CUDA Fix - Single EXE only** → Run workflow。Push 到 `main` 也會執行。
4. 建置成功後取得 Artifact：`Junba-Windows-CUDA-Fix-Single`；其中 `Junba-CUDA-Fix-Single.exe` 才是程式。
5. 工作流程在 Windows runner 上安裝 NVIDIA 提供的 `nvidia-cublas-cu12==12.4.5.8`、`nvidia-cudnn-cu12==9.5.1.17`、`nvidia-cuda-runtime-cu12==12.4.127`。GitHub 有 DLL 驗證，但託管 runner 沒有 NVIDIA GPU，所以**不會宣稱 GitHub 上通過了 GPU 真推論測試**。

## RTX 3060 Ti 實機檢測

1. 保持既有 Windows NVIDIA 顯示驅動（太舊時可能需要升級；不必先安裝 CUDA Toolkit）。
2. 開啟 Single EXE → **設定** → **執行 GPU 實際推論測試（tiny）**。
3. 程式會使用合成的 2 秒無聲 WAV，在 NVIDIA CUDA / FP16 上執行 Whisper tiny。第一次需要網路下載約數十 MB 模型。測試不會上傳使用者錄音。
4. 成功才會出現 `PASS NVIDIA CUDA FP16 實際推論完成`，然後可使用原本 `large-v3` 模型進行正式辨識；**tiny 成功仍不保證大型模型的顯示記憶體足夠**。
5. 除了手動測試，正式轉錄每次載入 CUDA 模型時也會先用合成 1 秒 WAV 執行一次暖機推論，若失敗就即時留下錯誤並切回 CPU，不等到處理長音訊中途才發現。\n6. 失敗時會顯示完整 `Traceback`、RuntimeError 或缺 DLL 資訊。可複製文字交回來分析。
6. 使用上若 CUDA 正式推論失敗，仍會自動改 CPU，但**失敗的原始 Exception 內容會顯示在工作紀錄**，並輸出 `cuda_runtime_error.txt`。

也可在 PowerShell 用：

```powershell
.\Junba-CUDA-Fix-Single.exe --cuda-self-test "${env:USERPROFILE}\Desktop\JunbaCUDA測試.txt" tiny
```

此命令會以 exit code 0 表示成功，非 0 表示失敗。詳細診斷寫入指定文字檔。另可用 `--cuda-audit` 檢查檔案有否內建，不做推論。

## 重要限制

- 單檔 EXE 內含 NVIDIA DLL，體積會比較大，首次啟動需解壓到暫存資料夾，耗時與安全軟體掃描有關。
- **Single EXE 不能取代顯示卡驅動**。`nvcuda.dll` 由安裝在 Windows 上的 NVIDIA Driver 提供，不可把他人驅動 DLL 打包替代。
- 若硬體測試失敗且錯誤顯示 DLL/driver，請提供整段回報再修，不要先亂裝多個 CUDA Toolkit。
- NVIDIA/cuDNN 函式庫遵守 NVIDIA 軟體授權；公開再散布內含 DLL 的 EXE 時應另確認授權條款。
