import unittest
import time
from julius.memory import search_memory, save_memory

class TestMemory(unittest.TestCase):
    def test_memory_save_and_retrieve(self):
        print("\n[Test] Iniciando teste de memória local...")
        # Save a test fact
        save_memory("O Júlio gosta de programar em Python e prefere usar Docker para containerizar.")
        
        # Query it
        memories = search_memory("Qual linguagem o Júlio usa?")
        self.assertIsInstance(memories, list)
        print(f"[Test] Memórias recuperadas com sucesso: {memories}")

if __name__ == "__main__":
    unittest.main()
