from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
class CudaSlimProfileTests(unittest.TestCase):
    def test_openvino_pins_removed(self):
        requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8').lower()
        for name in ('openvino==', 'openvino-genai==', 'openvino-tokenizers=='):
            self.assertNotIn(name, requirements)
    def test_cuda_libs_still_all_collected(self):
        spec = (ROOT / 'JunbaAITranscriber_onefile.spec').read_text(encoding='utf-8')
        for needle in ("('cublas', 'cudnn', 'cuda_runtime')", "_folder.glob('*.dll')",
                       "'cudnn64_9.dll'", "binaries += [(str(p), 'cuda_libs')"):
            self.assertIn(needle, spec)
        self.assertIn("'openvino', 'openvino_genai', 'openvino_tokenizers'", spec)
        self.assertNotIn("    'openvino',\n", spec)
    def test_onefile_and_artifact_before_checks(self):
        wf = (ROOT / '.github/workflows/build-windows-cuda-single.yml').read_text(encoding='utf-8')
        self.assertIn('JunbaAITranscriber_onefile.spec', wf)
        self.assertIn('Junba-CUDA-Slim-Single.exe', wf)
        self.assertLess(wf.index('Upload Single EXE immediately'), wf.index('Bounded Single EXE smoke tests'))
        self.assertIn('Timeout=120', wf)
    def test_optional_openvino_does_not_fail_general_diagnostics(self):
        s = (ROOT / 'app/core/diagnostics.py').read_text(encoding='utf-8')
        self.assertIn('OpenVINO / GenAI / NPU 未封裝', s)
        self.assertNotIn("('openvino', 'OpenVINO Runtime')", s)
    def test_windows_runtime_loads_cuda(self):
        hook = (ROOT / 'hooks/runtime_safe_windows.py').read_text(encoding='utf-8')
        self.assertIn('configure_cuda_dlls()', hook)
