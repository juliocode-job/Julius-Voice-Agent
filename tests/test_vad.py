import unittest
import numpy as np
from julius.vad import VADDetector

class TestVAD(unittest.TestCase):
    def test_vad_initialization(self):
        print("\n[Test] Inicializando Silero VAD...")
        detector = VADDetector()
        self.assertIsNotNone(detector.model)
        
        # Generate 512 samples of silent audio
        chunk = np.zeros(512, dtype=np.float32)
        res = detector.process_chunk(chunk)
        self.assertIsNone(res, "Silent audio chunk should not trigger VAD detection.")
        print("[Test] Silero VAD inicializado e validado com sucesso!")

if __name__ == "__main__":
    unittest.main()
