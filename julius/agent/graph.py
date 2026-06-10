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
    USE_GROQ, GROQ_API_KEY, GROQ_MODEL,
    AGENT_SYSTEM_PROMPT, AGENT_LANGUAGE
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
    
    if AGENT_SYSTEM_PROMPT:
        system_prompt = AGENT_SYSTEM_PROMPT
        if "{memory_context}" in system_prompt:
            system_prompt = system_prompt.replace("{memory_context}", memory_ctx or "None.")
        else:
            if memory_ctx:
                system_prompt += f"\n\nKnown user facts (use only if relevant):\n{memory_ctx}"
    else:
        # System prompt optimized for audio synthesis (concise, no markdown)
        system_prompt = f"""You are Julius, a friendly, intelligent local voice assistant speaking in English.
Respond concisely and naturally, ideal for audio conversations (limit your responses to at most 2 or 3 short sentences).

TOOL USAGE RULES:
1. If the user asks for the time, date, or day of the week, call the `get_time` tool. NEVER search the web for this.
2. Answer the user directly using data returned by the tools in the recent history (like time/date from `get_time` or weather from `get_weather`).
3. For weather/temperature queries, call the `get_weather` tool.
4. For searching news, recent events, historical facts, or general web queries, call the `search_web` tool.
5. To schedule, create, or save reminders, call the `set_reminder` tool.
6. IMPORTANT: Do not use any markdown formatting (like lists, bullet points, bold, italic, or hashtags) in your responses, as they will be spoken directly. Speak sequentially in a single sentence if listing items.

Known user facts from long-term memory (use only if relevant):
{memory_ctx if memory_ctx else "None."}
"""
    
    recent_messages = state["messages"][-20:]
    messages = [SystemMessage(content=system_prompt)] + recent_messages
    
    last_msg = messages[-1] if messages else None
    if last_msg and (isinstance(last_msg, ToolMessage) or getattr(last_msg, "type", "") == "tool"):
        if AGENT_SYSTEM_PROMPT:
            system_prompt_synthesis = AGENT_SYSTEM_PROMPT
            if "{memory_context}" in system_prompt_synthesis:
                system_prompt_synthesis = system_prompt_synthesis.replace("{memory_context}", memory_ctx or "None.")
            else:
                if memory_ctx:
                    system_prompt_synthesis += f"\n\nKnown user facts (use only if relevant):\n{memory_ctx}"
            
            if AGENT_LANGUAGE == "pt":
                system_prompt_synthesis += "\n\nSua tarefa é responder diretamente à pergunta do usuário usando as informações fornecidas pelas ferramentas no histórico recente de mensagens. Não use nenhuma formatação markdown na sua resposta."
            else:
                system_prompt_synthesis += "\n\nYour task is to answer the user's question directly using the information provided by the tools in the recent message history. Do not use any markdown formatting in your response."
        else:
            system_prompt_synthesis = f"""You are Julius, a friendly and intelligent voice assistant speaking in English.
Respond concisely and naturally (maximum 2 to 3 short sentences), ideal for voice. Never use markdown formatting.
Your task is to answer the user's question directly using the information provided by the tools in the recent message history.

Known user facts from long-term memory (use only if relevant):
{memory_ctx if memory_ctx else "None."}
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
