import unittest
import os
from julius.agent.tools import get_time, get_system_design_scenario, save_evaluation, search_web
from julius.core.config import DATA_DIR

class TestTools(unittest.TestCase):
    def test_get_time(self):
        print("\n[Test] Testing get_time tool...")
        time_str = get_time.invoke({})
        self.assertIsInstance(time_str, str)
        self.assertTrue("at" in time_str or "," in time_str)
        print(f"[Test] get_time returned: {time_str}")
        
    def test_get_system_design_scenario(self):
        print("\n[Test] Testing get_system_design_scenario tool...")
        res = get_system_design_scenario.invoke({"topic": "rate_limiter"})
        self.assertIn("Design a Rate Limiter", res)
        self.assertIn("Requirements", res)
        print(f"[Test] get_system_design_scenario returned: {res}")
        
    def test_save_evaluation(self):
        print("\n[Test] Testing save_evaluation tool...")
        feedback = "Candidate did well on high level design but lacked deep dive in data partitioning."
        res = save_evaluation.invoke({"feedback_notes": feedback})
        self.assertIn("successfully saved", res)
        print(f"[Test] save_evaluation returned: {res}")
        
        # Verify file exists
        eval_file = os.path.join(DATA_DIR, "evaluations.txt")
        self.assertTrue(os.path.exists(eval_file))
        
        # Cleanup
        try:
            os.remove(eval_file)
        except OSError:
            pass

if __name__ == "__main__":
    unittest.main()
