import unittest
import numpy as np
from julius.stt import STTTranscriber

class TestSTT(unittest.TestCase):
    def test_stt_transcription(self):
        print("\n[Test] Inicializando Whisper STT...")
        stt = STTTranscriber()
        self.assertIsNotNone(stt.model)
        
        # Test transcribing synthetic silent audio
        audio = np.zeros(16000, dtype=np.float32)
        text = stt.transcribe(audio)
        self.assertIsInstance(text, str)
        print("[Test] Whisper STT carregado e testado com sucesso!")

if __name__ == "__main__":
    unittest.main()
