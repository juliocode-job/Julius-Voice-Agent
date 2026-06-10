# Julius Voice Agent — Contexto de Desenvolvimento

Este arquivo serve como memória compartilhada das sessões de desenvolvimento do **Julius Voice Agent** com o **Antigravity**. Ele deve ser mantido atualizado a cada nova conversa.

---

## 🔮 Visão Geral do Projeto
Simulador de entrevista de System Design por mensagens de áudio (Audio-to-Text), 100% integrado ao WhatsApp.
- **STT**: faster-whisper (`small` model, `int8` CPU).
- **Memória**: Mem0 OSS + ChromaDB local com embeddings `nomic-embed-text`.
- **Raciocínio cognitivo**: LangGraph + Groq Cloud `llama-3.3-70b-versatile` (com fallback local para Ollama `llama3.2:3b`).
- **Canal de Comunicação**: WhatsApp Cloud API (asynchronous voice-to-text integration).
- **Ferramentas**: Cenários de System Design (`get_system_design_scenario`), salvamento de avaliações (`save_evaluation`), tempo local (`get_time`) e pesquisa web (`search_web`).

---

## 📅 Sessão: Refatoração Modular (03 de Junho de 2026)

### 1. Reestruturação para Monolito Modular
Migramos o repositório do padrão de arquivos planos na raiz para um formato de **Monolito Modular** limpo e legível.

### 2. Suite de Testes do Repositório (`tests/`)
Criamos uma pasta de testes oficial no repositório utilizando a biblioteca padrão `unittest` do Python para validar cada subsistema separadamente.

---

## 📅 Sessão: Otimização de Latência e Estabilidade (04 de Junho de 2026)

Nesta sessão, focamos em migrar o raciocínio cognitivo para a nuvem de ultra-baixa latência do **Groq Cloud**, resolvendo loops de recursão e erros de validação da API ao invocar ferramentas.

---

## 📅 Sessão: Segurança e Documentação da Arquitetura (08 de Junho de 2026)

### 1. Migração de Configurações para Variáveis de Ambiente (`.env`)
Adicionamos a biblioteca `python-dotenv` ao projeto e removemos credenciais sensíveis codificadas diretamente.

### 2. Controle de Versão e Exclusões do Git
Criamos o arquivo `.gitignore` excluindo pastas geradas localmente (`data/`, `venv/`, `.env`).

---

## 📅 Sessão: Integração com WhatsApp e Pivô para Inglês (09 de Junho de 2026)

### 1. Canal de Comunicação do WhatsApp (FastAPI + Webhook)
Criamos a estrutura de pacotes `julius/whatsapp/` e implementamos o adaptador `adapter.py` para coordenar o download de mensagens de voz e transcrição local, com um servidor FastAPI webhook exposto por túnel seguro.

### 2. Pivô Completo do Idioma para Inglês (English Language Pivot)
Atualizamos o idioma de transcrição e prompts de raciocínio no LangGraph para inglês, permitindo a prática fluida de simulação de entrevistas de design em inglês.

---

## 📅 Sessão: Transição para 100% WhatsApp-Native e Ferramentas de System Design (10 de Junho de 2026)

### 1. Remoção de Módulos Locais Obsoletos
*   **Problema**: O projeto possuía redundância de canais (CLI de áudio contínuo e WhatsApp webhook), e bibliotecas pesadas de áudio local (`sounddevice`, `silero-vad`, `kokoro-onnx`) causavam dependências complexas de drivers e modelos.
*   **Resolução**:
    - Deletamos `main.py` (CLI), `julius/vad/` (Silero VAD) e `julius/tts/` (Kokoro/Piper TTS).
    - Removemos as dependências desnecessárias do arquivo `requirements.txt`.
    - Excluímos as ferramentas genéricas antigas (`weather.py` e `reminder.py`).

### 2. Criação de Ferramentas Especializadas em System Design
*   **Problema**: O agente necessitava de ferramentas específicas para conduzir e persistir o processo de entrevistas de design.
*   **Resolução**:
    - Implementamos `julius/agent/tools/system_design.py` contendo:
      1. `get_system_design_scenario(topic)`: Carrega cenários pré-definidos (Rate Limiter, Chat Service, Ride Hailing, TinyURL, etc.).
      2. `save_evaluation(feedback_notes)`: Salva notas detalhadas sobre o desempenho do candidato em `data/evaluations.txt`.
    - Refatoramos e registramos essas novas ferramentas no grafo do LangGraph (`graph.py`).

### 3. Suite de Testes em Inglês
*   **Problema**: Os testes antigos continham asserções em português e referências a pacotes de VAD e TTS removidos.
*   **Resolução**:
    - Deletamos `tests/test_vad.py` e `tests/test_tts.py`.
    - Reescrevemos todos os testes restantes (`test_agent.py`, `test_memory.py`, `test_stt.py`, `test_tools.py`) em inglês.
    - Todos os testes passaram com sucesso no console do Windows.

---

## 📌 Ponto de Parada Atual (Onde Paramos)

- **Canais**: Julius é agora **100% headless e nativo do WhatsApp**.
- **Idioma**: Todas as operações de transcrição, diálogo e logs são 100% nativas em inglês.
- **Como Executar o Servidor de Webhook**:
  ```powershell
  .\venv\Scripts\activate
  uvicorn whatsapp_webhook:app --reload --port 8000
  ```
- **Túnel Webhook (ngrok)**:
  ```bash
  ngrok http 8000
  ```
