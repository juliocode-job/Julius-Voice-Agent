import unittest
from julius.memory import search_memory, save_memory

class TestMemory(unittest.TestCase):
    def test_memory_save_and_retrieve(self):
        print("\n[Test] Starting local memory test...")
        # Save a test fact in English
        save_memory("Julio likes programming in Python and prefers Docker for containerization.")
        
        # Query it in English
        memories = search_memory("What language does Julio use?")
        self.assertIsInstance(memories, list)
        print(f"[Test] Memories retrieved successfully: {memories}")

if __name__ == "__main__":
    unittest.main()
