import unittest
from julius.agent import agent_graph

class TestAgent(unittest.TestCase):
    def test_agent_graph_execution(self):
        print("\n[Test] Starting LangGraph Agent execution test...")
        config = {"configurable": {"thread_id": "test_session"}}
        inputs = {
            "messages": [("user", "Hello! What is your name?")],
            "memory_context": "The agent's name is Julius. He is an interviewer."
        }
        
        result = agent_graph.invoke(inputs, config=config)
        self.assertIn("messages", result)
        response_content = result["messages"][-1].content
        self.assertIsInstance(response_content, str)
        print(f"[Test] Response received successfully: '{response_content}'")

if __name__ == "__main__":
    unittest.main()
