import unittest
from julius.agent import agent_graph

class TestAgent(unittest.TestCase):
    def test_agent_graph_execution(self):
        print("\n[Test] Iniciando teste do agente LangGraph (Ollama)...")
        config = {"configurable": {"thread_id": "test_session"}}
        inputs = {
            "messages": [("user", "Olá! Qual é o seu nome?")],
            "memory_context": "O nome do agente é Julius. Ele é um assistente pessoal local."
        }
        
        result = agent_graph.invoke(inputs, config=config)
        self.assertIn("messages", result)
        response_content = result["messages"][-1].content
        self.assertIsInstance(response_content, str)
        print(f"[Test] Resposta obtida com sucesso: '{response_content}'")

if __name__ == "__main__":
    unittest.main()
