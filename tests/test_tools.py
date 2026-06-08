import unittest
from julius.agent.tools import get_time, set_reminder, get_weather, search_web

class TestTools(unittest.TestCase):
    def test_get_time(self):
        print("\n[Test] Testando ferramenta get_time...")
        time_str = get_time.invoke({})
        self.assertIsInstance(time_str, str)
        self.assertTrue("de" in time_str)
        print(f"[Test] get_time retornado: {time_str}")
        
    def test_set_reminder(self):
        print("\n[Test] Testando ferramenta set_reminder...")
        res = set_reminder.invoke({"text": "comprar pão", "when": "hoje às 18:00"})
        self.assertIn("Lembrete anotado", res)
        print(f"[Test] set_reminder retornado: {res}")
        
    def test_get_weather(self):
        print("\n[Test] Testando ferramenta get_weather...")
        res = get_weather.invoke({"city": "Sao Paulo"})
        self.assertIsInstance(res, str)
        print(f"[Test] get_weather retornado: {res}")

if __name__ == "__main__":
    unittest.main()
