# 🔮 Julius Voice Agent — Hybrid Edge-Cloud Stack

The **Julius Voice Agent** is an intelligent, conversational voice assistant designed for Brazilian Portuguese (pt-BR). Running as a hybrid edge-cloud modular monolith, it integrates state-of-the-art open-source AI models for voice activity detection, speech-to-text transcription, cognitive state orchestration, persistent long-term memory recall, and neural speech synthesis.

Developer: **Júlio Emanoel**  
Agent Language: **Brazilian Portuguese (pt-BR)**

---

## ⚙️ End-to-End Architecture

The audio execution pipeline operates sequentially in the terminal, boasting low-latency streaming and sentence-by-sentence voice playback:

```
[ Microphone ] 
      │ (Continuous 16kHz mono audio capture via sounddevice)
      ▼
┌──────────────┐
│  Silero VAD  │ (Scans 512-sample chunks with a 0.5s pre-speech buffer)
└──────┬───────┘
       │ (Triggers after 3 continuous seconds of user silence)
       ▼
┌──────────────┐
│ Whisper STT  │ (Offline local transcription using faster-whisper small int8)
└──────┬───────┘
       │ (Transcribed pt-BR text output)
       ▼
┌──────────────┐
│  Mem0 Search │ (Queries local ChromaDB using nomic-embed-text embeddings)
└──────┬───────┘
       │ (Injects retrieved user facts into the agent context)
       ▼
┌──────────────┐
│  LangGraph   │ (Orchestrates LLM dialog flow using Groq llama-3.3-70b-versatile)
│   (Brain)    │ ◄───► [ Local Tools (Weather API, SQLite Reminders, Time) ]
└──────┬───────┘
       │ (Generates natural response stripped of markdown/formatting)
       ▼
┌──────────────┐
│ TTS Player   │ (Synthesizes speech via Kokoro-ONNX or fallback Piper voice)
└──────┬───────┘
       │ (Audio playback streams sentence-by-sentence)
       ▼
[ Speaker Output ]
```

Detailed details about the inner data flow, routing mechanics, and sequence flows are documented in the [**ARCHITECTURE.md**](file:///c:/Users/lemos/OneDrive/Área de Trabalho/Julius Voice Agent/ARCHITECTURE.md).

---

## 📁 Repository Structure (Modular Monolith)

The codebase follows a **Modular Monolith** structure, separating responsibilities into highly cohesive modules and exposing clean programmatic interfaces:

```
Julius Voice Agent/
├── main.py                    # Entry point (continuous audio loop & Rich CLI)
├── requirements.txt           # Python dependency manifests
├── .gitignore                 # Version control exclusions (ignores .env, data, venv)
├── .env.example               # Configuration template for environment variables
├── .env                       # Local developer secrets (not committed to Git)
├── ARCHITECTURE.md            # In-depth architectural data flows & user journeys
├── julius/                    # Main package folder
│   ├── __init__.py            # Configures global warning suppressions & log levels
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Environment settings loader via python-dotenv
│   ├── vad/
│   │   ├── __init__.py
│   │   └── detector.py        # Voice Activity Detection (Silero VAD wrapper)
│   ├── stt/
│   │   ├── __init__.py
│   │   └── transcriber.py     # Local Speech-to-Text transcriber (faster-whisper)
│   ├── memory/
│   │   ├── __init__.py
│   │   └── manager.py         # Long-term semantic memory manager (Mem0 + ChromaDB)
│   ├── tts/
│   │   ├── __init__.py
│   │   └── player.py          # Hybrid neural speech synthesizer (Kokoro/Piper)
│   └── agent/
│       ├── __init__.py
│       ├── graph.py           # Dialog state machine & Groq/Ollama router (LangGraph)
│       └── tools/             # Bound agent tools
│           ├── __init__.py
│           ├── search.py      # DuckDuckGo web search API
│           ├── weather.py     # Open-Meteo weather API
│           ├── reminder.py    # SQLite-backed reminder scheduler
│           └── current_time.py# Local system datetime query tool
├── tests/                     # Unit testing suite
│   ├── __init__.py
│   ├── test_vad.py
│   ├── test_stt.py
│   ├── test_memory.py
│   ├── test_tts.py
│   ├── test_agent.py
│   └── test_tools.py
└── data/                      # Persistence directory (auto-generated)
    ├── memory.db              # SQLite storage for LangGraph thread checkpointers
    ├── reminders.db           # SQLite database for user reminders
    ├── chroma_db/             # Local Vector database for Mem0 embeddings
    └── tts_models/            # Downloaded Kokoro/Piper neural model assets
```

---

## 🛠️ Prerequisites & Installation

### 1. Setup Local Models in Ollama
Ensure **Ollama** is running locally on your machine, then pull the fallback LLM and embedding models:
```powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials. To leverage the ultra-low latency response times of Julius, set your Groq API key:
```powershell
copy .env.example .env
```
Edit `.env`:
```env
USE_GROQ=True
GROQ_API_KEY=your_actual_groq_api_key
```

### 3. Setup Virtual Environment (Python 3.11)
Initialize and activate your virtual environment, then install dependencies:
```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 How to Run Julius

1. Activate your virtual environment:
   ```powershell
   .\venv\Scripts\activate
   ```
2. Run the main assistant loop:
   ```powershell
   python main.py
   ```

*Note: On the first run, the TTS module will automatically download the required Kokoro ONNX model (`kokoro-v1.0.onnx`, `voices-v1.0.bin`) and Piper bin files to the `./data/tts_models/` folder.*

### Example Commands and Interactions:
- **Conversation & Memory**: Say *"Olá Julius, meu nome é Júlio"*. Wait for 3 seconds of silence. Later, close the app, open it again, and ask: *"Qual é o meu nome?"* to verify persistent memory retrieval.
- **Weather query**: Ask *"Como está o clima atual em São Paulo?"* (triggers `get_weather` tool).
- **Time/Date query**: Ask *"Que dia é hoje?"* (triggers `get_time` tool).
- **Reminders**: Say *"Me lembre de comprar café amanhã às 9 horas"* (triggers `set_reminder` tool).
- **Exit**: Press `Ctrl + C` in the terminal to safely shut down the listener.
