import os
from mem0 import Memory
from julius.core.config import CHROMA_DB_DIR, OLLAMA_BASE_URL, LLM_MODEL, EMBEDDING_MODEL

# Ensure the Chroma DB directory exists
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Configuration for Mem0 OSS using local stack config
config = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "julio_memories",
            "path": CHROMA_DB_DIR,
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": LLM_MODEL,
            "ollama_base_url": OLLAMA_BASE_URL,
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": EMBEDDING_MODEL,
            "ollama_base_url": OLLAMA_BASE_URL,
            "embedding_dims": 768,
        },
    },
}

# Initialize Memory
print("[Memory] Inicializando sistema de memória Mem0 + ChromaDB...")
try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        memory = Memory.from_config(config)
    print("[Memory] Sistema de memória inicializado com sucesso!")
except Exception as e:
    print(f"[Memory][Erro] Falha ao inicializar o Mem0. Detalhes: {e}")
    memory = None

USER_ID = "julio"

def search_memory(query: str) -> list[str]:
    """
    Pesquisa as memórias de longo prazo relevantes no banco de dados local.
    Filtra primeiro com heurísticas simples para evitar consultas inúteis ao banco.
    """
    if not memory:
        return []

    # Heurística para ignorar termos de saudações curtas ou perguntas básicas sobre o agente
    query_lower = query.lower().strip()
    query_clean = "".join(c for c in query_lower if c.isalnum() or c.isspace())
    words = query_clean.split()
    
    if len(words) <= 3:
        return []
        
    is_agent_question = any(w in query_clean for w in [
        "seu nome", "quem e voce", "quem e tu", "sua idade", "como vai", 
        "tudo bem", "quem e julius", "qual o seu", "qual e o seu"
    ])
    if is_agent_question:
        return []
        
    try:
        results = memory.search(query, filters={"user_id": USER_ID})
        memories = []
        
        if isinstance(results, dict) and "results" in results:
            items = results["results"]
        elif isinstance(results, list):
            items = results
        else:
            items = []
            
        for item in items:
            if isinstance(item, dict):
                # Filter by distance score. A lower score means higher semantic similarity.
                # Threshold of 0.93 is configured for nomic-embed-text to discard distant/unrelated facts.
                score = item.get("score", 1.0)
                if score > 0.93:
                    continue
                text = item.get("memory") or item.get("text")
                if text:
                    memories.append(text)
            elif isinstance(item, str):
                memories.append(item)
                
        return memories[:5]
    except Exception as e:
        print(f"[Memory][Erro] Erro ao pesquisar memória: {e}")
        return []

def save_memory(text: str):
    """
    Adiciona novos fatos extraídos de um turno de conversa na memória de longo prazo (em background).
    Filtra primeiro com heurísticas simples para evitar chamadas desnecessárias ao LLM.
    """
    # Analisa a entrada do usuário para decidir se vale a pena gastar processamento extraindo fatos
    text_lower = text.lower()
    user_line = ""
    for line in text_lower.split("\n"):
        if line.startswith("user:"):
            user_line = line.replace("user:", "").strip()
            
    if user_line:
        # Se for uma pergunta/frase sem pronomes ou verbos pessoais/declarativos, não salvamos fatos
        is_question = user_line.endswith("?") or any(user_line.startswith(q) for q in ["qual", "onde", "como", "quem", "quando", "por que", "o que", "quanto", "que horas"])
        has_personal_marker = any(word in user_line for word in [" eu ", "meu", "minha", "gosto", "prefiro", "sou ", "tenho ", "trabalho ", "chamo", "moro"])
        
        # Excluir explicitamente perguntas sobre o nome do agente
        is_about_name = "nome" in user_line and ("seu" in user_line or "julius" in user_line or "junior" in user_line or "juna" in user_line)
        
        if is_question and (not has_personal_marker or is_about_name):
            # Perguntas genéricas ou sobre o Julius não geram novos fatos pessoais do usuário
            return

        # Ignorar saudações e frases extremamente curtas e vazias de significado pessoal
        words = user_line.split()
        if len(words) <= 3 and not has_personal_marker:
            return

    # Só mostra a mensagem se a verificação de heurísticas passar
    print("\n[Memory] Analisando conversa em background para consolidação de fatos...")
    
    import threading
    
    def run():
        if not memory:
            return
        try:
            memory.add(text, user_id=USER_ID)
            print("\n[Memory] Fatos novos consolidados em background com sucesso!")
        except Exception as e:
            print(f"\n[Memory][Erro] Erro ao salvar memória em background: {e}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
