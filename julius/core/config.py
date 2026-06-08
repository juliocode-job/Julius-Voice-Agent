import os
from dotenv import load_dotenv

# Compute the root absolute path of the workspace
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

DATA_DIR = os.path.join(BASE_DIR, "data")

# Specific data paths
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")
TTS_MODELS_DIR = os.path.join(DATA_DIR, "tts_models")
SQLITE_DB_PATH = os.path.join(DATA_DIR, "memory.db")
REMINDERS_DB_PATH = os.path.join(DATA_DIR, "reminders.db")

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# Groq settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
USE_GROQ = os.getenv("USE_GROQ", "True").lower() in ("true", "1", "t", "y", "yes")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # High capability, extremely fast Llama 3.3 model on Groq with native tool-calling support

if USE_GROQ and not GROQ_API_KEY:
    import warnings
    warnings.warn(
        "USE_GROQ is configured as True, but GROQ_API_KEY is not set or empty in the environment.",
        UserWarning
    )

