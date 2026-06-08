import os
import sqlite3
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

# Import local tools and configs from the julius package
from julius.agent.tools import search_web, get_weather, set_reminder, get_time
from julius.core.config import (
    SQLITE_DB_PATH, LLM_MODEL, OLLAMA_BASE_URL,
    USE_GROQ, GROQ_API_KEY, GROQ_MODEL
)

# Ensure data directory exists
os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

# 1. Define Agent State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    memory_context: str
    current_tool_calls: list

# 2. Initialize LLM based on the USE_GROQ configuration toggle
if USE_GROQ:
    from langchain_groq import ChatGroq
    print(f"[Agent] Inicializando ChatGroq ({GROQ_MODEL}) com nuvem de ultra-baixa latência...")
    llm = ChatGroq(model=GROQ_MODEL, temperature=0.1, groq_api_key=GROQ_API_KEY)
else:
    print(f"[Agent] Inicializando ChatOllama ({LLM_MODEL}) local...")
    llm = ChatOllama(model=LLM_MODEL, temperature=0.1, base_url=OLLAMA_BASE_URL)

tools = [search_web, get_weather, set_reminder, get_time]
llm_with_tools = llm.bind_tools(tools)

# 3. Define Nodes
def call_model(state: AgentState):
    """
    Invokes the LLM with the user history and system prompt injected with long-term memories.
    """
    memory_ctx = state.get("memory_context", "")
    
    # System prompt optimized for audio synthesis (concise, no markdown)
    system_prompt = f"""Você é o Julius, um agente de voz local, amigável e inteligente em português brasileiro (pt-BR).
Responda de forma concisa e natural, ideal para conversas de áudio (limite suas respostas a no máximo 2 ou 3 frases curtas).

REGRAS DE USO DE FERRAMENTAS:
1. Se o usuário perguntar as horas, que horas são, a data, que dia é hoje ou o dia da semana, chame a ferramenta `get_time`. NUNCA use a pesquisa na web para isso.
2. Responda diretamente ao usuário usando os dados retornados pelas ferramentas no histórico recente (como a data/hora de `get_time` ou o clima de `get_weather`).
3. Para previsão do tempo, clima ou temperatura de qualquer cidade ou localidade, chame a ferramenta `get_weather`.
4. Para pesquisar notícias, eventos recentes, fatos históricos ou dúvidas gerais na internet, chame a ferramenta `search_web`.
5. Para agendar, criar ou salvar lembretes ou compromissos, chame a ferramenta `set_reminder`.
6. IMPORTANTE: Não use nenhuma formatação markdown (como listas com bullet points, negrito, itálico ou hashtags) nas suas respostas, pois elas serão faladas diretamente por voz. Se precisar citar itens, fale-os de forma corrida em uma frase contínua.

Fatos sobre o usuário da memória de longo prazo (use somente se forem relevantes para a resposta):
{memory_ctx if memory_ctx else "Nenhum fato relevante conhecido."}
"""
    
    recent_messages = state["messages"][-20:]
    messages = [SystemMessage(content=system_prompt)] + recent_messages
    
    last_msg = messages[-1] if messages else None
    if last_msg and (isinstance(last_msg, ToolMessage) or getattr(last_msg, "type", "") == "tool"):
        system_prompt_synthesis = f"""Você é o Julius, um assistente de voz amigável e inteligente em português brasileiro (pt-BR).
Responda sempre de forma concisa e natural (máximo 2 a 3 frases curtas), ideal para voz. Nunca use formatação markdown (como hashtags, listas ou negrito).
Sua tarefa é responder diretamente à pergunta do usuário usando as informações fornecidas pelas ferramentas no histórico recente de mensagens.

Fatos sobre o usuário da memória de longo prazo (use somente se forem relevantes para a resposta):
{memory_ctx if memory_ctx else "Nenhum fato relevante conhecido."}
"""
        synthesis_messages = []
        for m in messages:
            if isinstance(m, SystemMessage):
                synthesis_messages.append(SystemMessage(content=system_prompt_synthesis))
            elif isinstance(m, HumanMessage) or getattr(m, "type", "") == "human":
                synthesis_messages.append(m)
            elif isinstance(m, AIMessage) or getattr(m, "type", "") == "ai":
                if getattr(m, "tool_calls", []):
                    calls_str = ", ".join([f"{c['name']}({c['args']})" for c in m.tool_calls])
                    synthesis_messages.append(AIMessage(content=f"[Executando: {calls_str}]"))
                else:
                    synthesis_messages.append(m)
            elif isinstance(m, ToolMessage) or getattr(m, "type", "") == "tool":
                synthesis_messages.append(HumanMessage(content=f"[Resultado da ferramenta: {m.content}]"))
            else:
                synthesis_messages.append(m)
                
        response = llm.invoke(synthesis_messages)
    else:
        response = llm_with_tools.invoke(messages)
        
    tool_calls = getattr(response, "tool_calls", [])
    
    # Se o modelo gerou um JSON bruto no content descrevendo uma chamada de ferramenta, mas o LangChain não o parseou
    if not tool_calls and response.content:
        import json
        content_stripped = response.content.strip()
        if content_stripped.startswith("```json"):
            content_stripped = content_stripped[7:]
        if content_stripped.endswith("```"):
            content_stripped = content_stripped[:-3]
        content_stripped = content_stripped.strip()
        
        if content_stripped.startswith("{") and content_stripped.endswith("}"):
            try:
                # Corrige caracteres de escape inválidos que quebram o parser JSON standard
                cleaned_content = content_stripped.replace("\\|", "|")
                data = json.loads(cleaned_content)
                if "name" in data:
                    tool_calls = [{
                        "name": data["name"],
                        "args": data.get("parameters") or data.get("arguments") or {},
                        "id": f"call_{data['name']}",
                        "type": "tool_call"
                    }]
                    response.tool_calls = tool_calls
            except Exception:
                pass
                
    return {
        "messages": [response],
        "current_tool_calls": tool_calls
    }

# 4. Define Router Edge
def should_continue(state: AgentState):
    """
    Decides whether to route to the tool executor node or to end the execution.
    """
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])
    if tool_calls:
        return "tools"
    return "__end__"

# 5. Assemble Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Set entry point
workflow.set_entry_point("agent")

# Add conditional edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "__end__": "__end__"
    }
)

# Link tools back to agent
workflow.add_edge("tools", "agent")

# 6. Configure short-term SQLite persistence
db_conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(db_conn)

# Compile Graph
print("[Agent] Compilando grafo LangGraph com persistência SQLite local...")
agent_graph = workflow.compile(checkpointer=checkpointer)
print("[Agent] Grafo de diálogo compilado com sucesso!")
