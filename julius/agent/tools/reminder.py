import sqlite3
import os
from langchain_core.tools import tool
from julius.core.config import REMINDERS_DB_PATH

def init_db():
    os.makedirs(os.path.dirname(REMINDERS_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(REMINDERS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            when_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Ensure table exists when importing the module
init_db()

@tool
def set_reminder(text: str, when: str) -> str:
    """
    Salva um lembrete no banco de dados local.
    Parâmetros:
      - text: O assunto do lembrete (ex: 'ligar para a Ana', 'comprar pão').
      - when: O momento ou data do lembrete (ex: 'amanhã de manhã', 'hoje às 20:00').
    """
    try:
        conn = sqlite3.connect(REMINDERS_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (text, when_time) VALUES (?, ?)",
            (text, when)
        )
        conn.commit()
        conn.close()
        return f"Lembrete anotado com sucesso: '{text}' para '{when}'."
    except Exception as e:
        return f"Erro ao criar lembrete: {e}"
