from ddgs import DDGS
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """
    Pesquisa na web por informações atualizadas. Use apenas para fatos recentes, notícias ou dúvidas gerais.
    ATENÇÃO: NUNCA chame esta ferramenta para perguntas sobre horário, horas, data atual, dia da semana ou previsão do tempo.
    Para horas e data de hoje use sempre 'get_time', e para previsão do tempo use 'get_weather'.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return f"Nenhum resultado encontrado para a pesquisa: '{query}'."
            
            output = []
            for r in results:
                title = r.get("title", "")
                link = r.get("href", "")
                snippet = r.get("body", "")
                output.append(f"Título: {title}\nLink: {link}\nSnippet: {snippet}")
                
            return "\n\n".join(output)
    except Exception as e:
        return f"Erro ao realizar pesquisa na web: {e}"
