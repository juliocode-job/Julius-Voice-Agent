# 🔮 Julius Voice Agent — Hybrid Edge-Cloud Stack

The **Julius Voice Agent** is an intelligent, conversational voice assistant designed in English. Operating as a hybrid edge-cloud modular monolith, it integrates state-of-the-art open-source AI models for voice activity detection, speech-to-text transcription, cognitive state orchestration, persistent long-term memory recall, neural speech synthesis, and an asynchronous WhatsApp interface for mock system design interviews.

Developer: **Júlio Emanoel**  
Agent Language: **English (en)**

---

## ⚙️ End-to-End Architecture

Julius operates as a WhatsApp-based System Design mock interviewer. The execution flow is asynchronous:

1. **User Voice Note**: The user sends a voice note (in English) to the whitelisted WhatsApp number.
2. **FastAPI Webhook**: The incoming audio file is downloaded from the Meta Graph API.
3. **Speech-to-Text**: Whisper transcribes the `.ogg` file locally.
4. **Cognitive Reasoning**: LangGraph (running ChatGroq with `llama-3.3-70b-versatile`) evaluates the transcription, checks long-term memory via Mem0/ChromaDB, and executes interview-specific tools (like loading system design scenarios or saving evaluations).
5. **WhatsApp Response**: Julius responds with a text-based follow-up message on WhatsApp.

Detailed details about the inner data flow, routing mechanics, and sequence flows are documented in the [**ARCHITECTURE.md**](file:///c:/Users/lemos/OneDrive/Área de Trabalho/Julius Voice Agent/ARCHITECTURE.md).

---

## 📁 Repository Structure (Modular Monolith)

The codebase follows a **Modular Monolith** structure, separating responsibilities into highly cohesive modules and exposing clean programmatic interfaces:

```
Julius Voice Agent/
├── main.py                    # Entry point (continuous audio loop & Rich CLI)
├── whatsapp_webhook.py        # FastAPI server webhook for WhatsApp Cloud API channel
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
│   ├── whatsapp/
│   │   ├── __init__.py        # WhatsApp sub-package init
│   │   └── adapter.py         # Media downloader, STT transcriber, and agent router
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

## 🚀 How to Run Julius (WhatsApp Webhook Server)

Julius is run as a FastAPI webhook server that handles incoming audio from the Meta WhatsApp Cloud API.

1. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your credentials:
   - `WHATSAPP_TOKEN`: Meta access token.
   - `WHATSAPP_PHONE_ID`: Phone number ID for test messages.
   - `WEBHOOK_VERIFY_TOKEN`: Verification token of your choice.
   - `MY_WHATSAPP_NUMBER`: Whitelisted phone number allowed to interact (with country code, e.g. `5581999990000`).

2. **Start the Webhook Server**:
   ```powershell
   .\venv\Scripts\activate
   uvicorn whatsapp_webhook:app --reload --port 8000
   ```

3. **Expose the Webhook Server to the Internet**:
   Using `ngrok` or similar:
   ```bash
   ngrok http 8000
   ```

4. **Meta Developer Setup**:
   - Save your ngrok URL + `/webhook` as the webhook Callback URL in the Meta Developer Console (under WhatsApp Configuration).
   - Enter your chosen `WEBHOOK_VERIFY_TOKEN`.
   - Subscribe to the `messages` event.
   - Under the Sandbox "API Setup" tab, add your personal whitelisted number.

5. **Start Practicing**:
   Record a WhatsApp voice note in English describing a system design question or answer (e.g., "What scenario should we practice today?") and send it to the sandbox business number. Julius will transcribe the audio locally and respond via text!
