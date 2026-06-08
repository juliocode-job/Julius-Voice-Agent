from datetime import datetime
from langchain_core.tools import tool

@tool
def get_time(**kwargs) -> str:
    """
    Retorna o dia da semana, a data e o horário atual formatados em português (pt-BR).
    Use sempre que o usuário perguntar as horas, que horas são, a data, que dia é hoje, o dia da semana ou qualquer dúvida relacionada ao horário atual.
    """
    now = datetime.now()
    dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    dia_semana = dias[now.weekday()]
    dia = now.day
    mes = meses[now.month - 1]
    ano = now.year
    hora = now.strftime("%H:%M")
    return f"{dia_semana}, {dia} de {mes} de {ano} às {hora}"
