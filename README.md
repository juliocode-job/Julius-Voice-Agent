# 🔮 Julius Voice Agent — Local Stack

O **Julius Voice Agent** é um assistente de voz conversacional inteligente, rodando de forma 100% local, offline e com custo zero. O projeto utiliza modelos abertos de inteligência artificial para detecção de fala, transcrição, raciocínio cognitivo, persistência de memórias de longo prazo e síntese de voz em tempo real.

Desenvolvedor: **Júlio Emanoel**  
Idioma do Agente: **Português Brasileiro (pt-BR)**

---

## ⚙️ Arquitetura End-to-End

O pipeline de execução de áudio opera de forma sequencial no terminal, com baixa latência e streaming de voz frase por frase:

```
[ Microfone ] 
      │ (Captura contínua de áudio via sounddevice a 16kHz mono)
      ▼
┌──────────────┐
│  Silero VAD  │ (Captura chunks de 512 amostras com pré-buffer de 0.5s)
└──────┬───────┘
       │ (Dispara após 3 segundos contínuos de silêncio do usuário)
       ▼
┌──────────────┐
│ Whisper STT  │ (Transcreve o áudio offline usando faster-whisper base int8)
└──────┬───────┘
       │ (Texto transcrito em pt-BR)
       ▼
┌──────────────┐
│  Mem0 Search │ (Consulta ChromaDB local usando embeddings nomic-embed-text)
└──────┬───────┘
       │ (Injeta memórias e fatos do usuário no prompt)
       ▼
┌──────────────┐
│  LangGraph   │ (Orquestra o diálogo do LLM usando llama3.2:3b local)
│  (Ollama)    │ ◄───► [ Ferramentas Locais (Clima, Lembretes SQLite, Hora) ]
└──────┬───────┘
       │ (Gera resposta natural sem formatação markdown)
       ▼
┌──────────────┐
│ TTS Player   │ (Sintetiza áudio via Kokoro-ONNX principal ou fallback Piper)
└──────┬───────┘
       │ (Stream de áudio reproduzido frase a frase enquanto gera o texto)
       ▼
[ Alto-falante ]
```

---

## 📁 Estrutura do Repositório (Monolito Modular)

O projeto foi reestruturado de um layout plano para um padrão de **Monolito Modular**, agrupando responsabilidades em pacotes de alta coesão e expondo uma interface limpa:

```
Julius Voice Agent/
├── main.py                    # Script de entrada (loop contínuo e interface visual)
├── requirements.txt           # Dependências do ecossistema local
├── julius/                    # Pacote principal do agente
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Configurações globais (caminhos de dados e portas do Ollama)
│   ├── vad/
│   │   ├── __init__.py
│   │   └── detector.py        # Detector de atividade de voz (Silero VAD)
│   ├── stt/
│   │   ├── __init__.py
│   │   └── transcriber.py     # Transcritor local (faster-whisper)
│   ├── memory/
│   │   ├── __init__.py
│   │   └── manager.py         # Memória persistente (Mem0 + ChromaDB)
│   ├── tts/
│   │   ├── __init__.py
│   │   └── player.py          # Sintetizador híbrido de fala (Kokoro/Piper)
│   └── agent/
│       ├── __init__.py
│       ├── graph.py           # Grafo de agentes (LangGraph)
│       └── tools/             # Ferramentas acopladas ao LLM
│           ├── __init__.py
│           ├── search.py      # Busca web gratuita (DuckDuckGo)
│           ├── weather.py     # Previsão climática (Open-Meteo)
│           ├── reminder.py    # Lembretes locais (SQLite)
│           └── current_time.py# Data e hora formatadas em pt-BR
├── tests/                     # Suite de testes unitários do monolito
│   ├── __init__.py
│   ├── test_vad.py
│   ├── test_stt.py
│   ├── test_memory.py
│   ├── test_tts.py
│   ├── test_agent.py
│   └── test_tools.py
└── data/                      # Diretório de persistência de dados (gerado automaticamente)
    ├── memory.db              # SQLite para checkpoint do LangGraph
    ├── reminders.db           # SQLite de lembretes do usuário
    ├── chroma_db/             # Banco vetorial local para Mem0
    └── tts_models/            # Binários e modelos baixados para Kokoro/Piper
```

---

## 🛠️ Pré-requisitos & Instalação

### 1. Modelos Locais no Ollama
Certifique-se de que o **Ollama** está rodando no seu computador e faça o download dos modelos necessários:
```powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 2. Configurar o Ambiente Virtual (Python 3.11)
Crie e ative um ambiente virtual e, em seguida, instale as dependências listadas no `requirements.txt`:
```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows PowerShell)
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

---

## 🚀 Como Executar o Julius

1. Ative o ambiente virtual:
   ```powershell
   .\venv\Scripts\activate
   ```
2. Inicie o loop principal do assistente de voz:
   ```powershell
   python main.py
   ```

*Nota: Na primeira execução, o módulo de TTS fará o download automático dos modelos do Kokoro (`kokoro-v1.0.onnx` e `voices-v1.0.bin`) e do Piper no diretório `./data/tts_models/`.*

### Comandos e Interação:
- **Fale com o Agente**: Diga algo como *"Olá Julius, meu nome é Júlio"*. Espere 3 segundos de silêncio para processamento.
- **Teste de Lembrete**: Peça *"Me lembre de comprar café amanhã às 9 horas"*.
- **Previsão Climática**: Pergunte *"Como está o clima atual em São Paulo?"*.
- **Memória de Longo Prazo**: Feche o programa, reabra e pergunte: *"Qual é o meu nome?"* para verificar a recuperação vetorial de fatos.
- **Sair**: Aperte `Ctrl + C` no terminal.
