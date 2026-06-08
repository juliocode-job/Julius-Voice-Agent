import unittest
from julius.tts import TTSPlayer

class TestTTS(unittest.TestCase):
    def test_tts_initialization(self):
        print("\n[Test] Inicializando TTSPlayer...")
        player = TTSPlayer()
        # Verify that at least one of the players is initialized
        self.assertTrue(
            player.kokoro_player is not None or player.piper_exe is not None,
            "At least Kokoro or Piper TTS fallback must be successfully initialized."
        )
        print("[Test] TTSPlayer carregado com sucesso!")

if __name__ == "__main__":
    unittest.main()
