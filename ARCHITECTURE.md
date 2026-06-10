# Julius Voice Agent — System Architecture

This document describes the end-to-end architecture, user journey, data flow, and core technical features of the **Julius Voice Agent**, a low-latency, modular voice assistant designed in English.

---

## 🔮 Core Technical Features

Julius is built with a hybrid edge-cloud stack designed for **zero cost, low latency, offline autonomy, and long-term memory recollection**:

- **Voice Activity Detection (VAD)**: Powering seamless hands-free conversational triggers using *Silero VAD* (running locally on CPU). It tracks sound blocks, saves pre-speech buffer context, and fires after a configured 3-second silence threshold.
- **Speech-To-Text (STT)**: Offline local transcription using `faster-whisper` (`small` model quantized to `int8` CPU execution) optimized for low latency and high accuracy in English.
- **Cognitive Reasoning (LangGraph & Groq)**: 
  - Dialog flow managed by `LangGraph` with localized `SQLite` checkpointer state persistence.
  - Hybrid model routing: Uses **Groq Cloud** with `llama-3.3-70b-versatile` (latencies ~600ms) for high-intelligence tool calling and synthesis, with a fallback toggle to local **Ollama** (`llama3.2:3b`).
  - Separated execution prompts: *Routing System Prompt* (first pass for tool routing) and *Synthesis System Prompt* (second pass for natural conversation formatting, ignoring markdown and tools).
  - Role conversion layer: Restructures message schemas sent to Groq during the synthesis pass, mapping tool responses into human-structured messages to prevent API errors.
- **Long-term Memory (Mem0 + ChromaDB)**: Dynamic facts extraction and retrieval via local `Mem0` vector storage, utilizing local `nomic-embed-text` embeddings through Ollama.
- **Text-To-Speech (TTS)**: Hybrid architecture featuring `Kokoro-ONNX` (high-fidelity neural voice) with a subprocess fallback to `Piper` (high-speed local voice generation in English).
- **Extensible Agent Tools**:
  - `get_time`: Direct local system datetime query (avoids web search hallucination).
  - `get_weather`: Open-source weather metrics fetching.
  - `search_web`: DuckDuckGo search API fallback for recent queries.
  - `set_reminder`: SQLite-backed scheduler recording reminders.

---

## 🔄 End-to-End Data Flow

The following diagram illustrates how user audio inputs flow through the local stack, cognitive layers, and back to audio playback.

```mermaid
graph TD
    %% Audio Capture & VAD
    A["Microphone Input (sounddevice)"] --> B["Silero VAD (vad/detector.py)"]
    B -- "Speech Detected (3s Silence Ends)" --> C["Audio Utterance Array"]
    
    %% Transcription
    C --> D["STT (stt/transcriber.py - Whisper small int8)"]
    D --> E["Text Transcription"]
    
    %% Memory Query
    E --> F["Memory Retrieval (memory/manager.py - Mem0)"]
    F --> G["Semantic Memory Context"]
    
    %% LangGraph Routing Pass
    E & G --> H["LangGraph Dialog State (agent/graph.py)"]
    H --> I["Call Model Node (First Pass: Routing)"]
    
    %% Tool execution branch
    I -- "Requires Tool Call" --> J["Tool Node (set_reminder / get_time / get_weather / search_web)"]
    J --> K["Tool Results"]
    K --> L["Call Model Node (Second Pass: Synthesis)"]
    
    %% Direct reply branch
    I -- "Direct Response" --> M["Final Answer Text"]
    L --> M
    
    %% TTS & Playback
    M --> N["TTS Player (tts/player.py - Kokoro / Piper)"]
    N --> O["Speaker Output (sounddevice / soundfile)"]
    
    %% Async Memory Save
    M & E -- "Trigger Async Thread" --> P["Memory Consolidation (Mem0 / ChromaDB)"]
    P --> Q["Saved User Facts database"]
```

### 📱 WhatsApp Webhook Architecture & Data Flow

For the WhatsApp channel, the physical VAD, microphone, and speaker audio layers are bypassed. The flow operates as follows:

```mermaid
graph TD
    UserPhone["User WhatsApp Voice Note (.ogg)"] --> Webhook["FastAPI Server (whatsapp_webhook.py)"]
    Webhook -- "Download Request" --> MetaAPI["Meta Graph API"]
    MetaAPI -- "Audio Binary" --> Webhook
    Webhook --> STT["stt/transcriber.py (Whisper small int8)"]
    STT -- "English Transcription" --> MemorySearch["Memory Retrieval (Mem0)"]
    MemorySearch --> LangGraph["LangGraph Dialog State (agent/graph.py)"]
    LangGraph ◄───► Tools["Agent Tools"]
    LangGraph -- "Synthesized Text Reply" --> MetaSend["Meta Send API"]
    MetaSend --> UserPhone
```

---

## 🗺️ User Journey Map

Here is the step-by-step lifecycle of a single interaction turn inside Julius:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant VAD as "VAD (Silero)"
    participant STT as "STT (Whisper)"
    participant Mem as "Memory (Mem0)"
    participant Graph as "LangGraph Agent"
    participant Tools as "Agent Tools"
    participant TTS as "TTS (Kokoro/Piper)"


    User->>VAD: Speak: "What time is it?"
    Note over VAD: Capturing audio buffer...
    Note over VAD: Silence threshold reached (3s)
    VAD->>STT: Send raw audio utterance
    STT->>STT: Transcribe audio to text
    STT->>Mem: Query memory for transcription context
    Mem-->>STT: Return relevant memories ("User resides in New York", etc.)
    STT->>Graph: Send Transcription + Memory Context
    
    rect rgb(240, 248, 255)
        Note over Graph: Routing Phase
        Graph->>Graph: Evaluate prompts & conversation history
        Graph-->>Tools: Trigger tool call: get_time()
        Tools-->>Graph: Return payload: "Thursday, June 4, 2026 at 13:41"
        Note over Graph: Role-Conversion & Synthesis Phase
        Note over Graph: Remove markdown, format text for voice
    end
    
    Graph->>TTS: Send synthesized response: "It is 1:41 PM..."
    Note over TTS: Stop microphone listener stream (prevent feedback echo)
    TTS->>User: Play synthesized voice audio
    Note over TTS: Restart microphone listener stream
    
    opt Background Process
        Graph->>Mem: Save conversation turn facts in background thread
    end
```

---

## 🔒 Configuration & Environment Variables

All critical credentials and execution toggles are isolated into a `.env` file at the project root. Refer to `.env.example` to set up your environment:

- `USE_GROQ`: Toggle between `True` (cloud LLM) and `False` (fully offline Ollama).
- `GROQ_API_KEY`: API Key for low-latency reasoning on Groq Cloud.
- `GROQ_MODEL`: Model name (default: `llama-3.3-70b-versatile`).
- `OLLAMA_BASE_URL`: Local URL for Ollama instances (default: `http://localhost:11434`).
- `LLM_MODEL`: Local Ollama fallback LLM (default: `llama3.2:3b`).
- `EMBEDDING_MODEL`: Local model for memory vector embeddings (default: `nomic-embed-text`).
