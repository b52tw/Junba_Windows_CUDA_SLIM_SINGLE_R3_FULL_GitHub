from __future__ import annotations
from app.core.models import Segment, TranscriptResult
from app.core.audio_tools import audio_duration_seconds


class LocalWhisperProvider:
    def __init__(self, model_name='large-v3', device='auto', compute_type='auto'):
        from faster_whisper import WhisperModel
        if device == 'auto':
            device = 'cuda' if self._cuda_available() else 'cpu'
        if compute_type == 'auto':
            compute_type = 'float16' if device == 'cuda' else 'int8'
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)
        self.device = device
        self.compute_type = compute_type
        # Catch missing CUDA/cuDNN symbols or driver/runtime problems before
        # spending minutes on a long user recording. CTranslate2 often loads
        # GPU kernels lazily at the FIRST inference, not at model construction.
        if device == 'cuda':
            self._cuda_inference_warmup()

    def _cuda_inference_warmup(self):
        import tempfile
        import wave
        from pathlib import Path
        with tempfile.TemporaryDirectory(prefix='junba_cuda_warmup_') as td:
            path = Path(td) / 'gpu_test.wav'
            with wave.open(str(path), 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(b'\x00\x00' * 16000)
            segments, _ = self.model.transcribe(
                str(path), language='zh', beam_size=1, vad_filter=False,
                word_timestamps=False, condition_on_previous_text=False,
            )
            # Iterator exhaustion is essential: decoding may start lazily.
            list(segments)

    @staticmethod
    def _cuda_available() -> bool:
        try:
            import ctranslate2
            return ctranslate2.get_cuda_device_count() > 0
        except Exception:
            return False

    def transcribe(self, path: str, language: str | None = None, stop_flag=None, progress_cb=None, wait_cb=None) -> TranscriptResult:
        kwargs = dict(beam_size=5, vad_filter=True, word_timestamps=True)
        if language and language != 'auto':
            kwargs['language'] = language
        duration = audio_duration_seconds(path)
        if progress_cb:
            progress_cb(0, '準備 Whisper 推論')
        segments_gen, info = self.model.transcribe(path, **kwargs)
        segs: list[Segment] = []
        parts: list[str] = []
        for seg in segments_gen:
            if wait_cb:
                wait_cb()
            if stop_flag and stop_flag():
                break
            text = (seg.text or '').strip()
            if text:
                segs.append(Segment(float(seg.start), float(seg.end), text))
                parts.append(text)
            if progress_cb:
                pct = int((float(seg.end) / duration) * 100) if duration > 0 else min(99, len(segs))
                progress_cb(max(1, min(99, pct)), f'{float(seg.end):.1f}/{duration:.1f} 秒' if duration > 0 else f'{len(segs)} 段')
        if progress_cb:
            progress_cb(100, 'Whisper 轉錄完成')
        return TranscriptResult('\n'.join(parts), segs, getattr(info, 'language', None), f'faster-whisper ({self.device}/{self.compute_type})')
