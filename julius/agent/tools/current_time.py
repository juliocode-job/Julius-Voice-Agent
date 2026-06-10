from datetime import datetime
from langchain_core.tools import tool

@tool
def get_time(**kwargs) -> str:
    """
    Returns the current day of the week, date, and time formatted in English.
    Always use this when the user asks for the time, date, day of the week, or current time.
    """
    now = datetime.now()
    dia_semana = now.strftime("%A")
    dia = now.day
    mes = now.strftime("%B")
    ano = now.year
    hora = now.strftime("%H:%M")
    return f"{dia_semana}, {mes} {dia}, {ano} at {hora}"
