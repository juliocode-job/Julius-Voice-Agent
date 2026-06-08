# Julius Voice Agent — Contexto de Desenvolvimento

Este arquivo serve como memória compartilhada das sessões de desenvolvimento do **Julius Voice Agent** com o **Antigravity**. Ele deve ser mantido atualizado a cada nova conversa.

---

## 🔮 Visão Geral do Projeto
Agente de voz local, offline e de custo zero para português brasileiro (pt-BR).
- **VAD**: Silero VAD (3s de silêncio para disparar).
- **STT**: faster-whisper (`base` model, `int8` CPU).
- **Memória**: Mem0 OSS + ChromaDB local com embeddings `nomic-embed-text`.
- **Raciocínio cognitivo**: LangGraph + Groq Cloud `llama-3.3-70b-versatile` (com fallback local para Ollama `llama3.2:3b`).
- **TTS**: Kokoro ONNX com fallback automático de subprocesso para Piper.

---

## 📅 Sessão: Refatoração Modular (03 de Junho de 2026)

### 1. Reestruturação para Monolito Modular
Migramos o repositório do padrão de arquivos planos na raiz para um formato de **Monolito Modular** limpo e legível:
- Pacote principal `julius/`:
  - `core/config.py`: Variáveis e constantes de caminhos globais (`data/`) e especificações de modelos locais do Ollama.
  - `vad/detector.py`: Detecção de fala Silero VAD.
  - `stt/transcriber.py`: Transcrição de áudio com `faster-whisper`.
  - `memory/manager.py`: Consolidação e consulta de fatos via `Mem0`.
  - `tts/player.py`: Geração de áudio híbrida (Kokoro/Piper).
  - `agent/graph.py`: Grafo do diálogo executado com LangGraph.
  - `agent/tools/`: Pacote com as ferramentas de busca, tempo, lembrete e hora.

### 2. Suite de Testes do Repositório (`tests/`)
Criamos uma pasta de testes oficial no repositório utilizando a biblioteca padrão `unittest` do Python para validar cada subsistema separadamente (`tests/test_vad.py`, `tests/test_stt.py`, etc.).

---

## 📅 Sessão Atual: Otimização de Latência e Estabilidade (04 de Junho de 2026)

Nesta sessão, focamos em migrar o raciocínio cognitivo para a nuvem de ultra-baixa latência do **Groq Cloud**, resolvendo loops de recursão e erros de validação da API ao invocar ferramentas.

### 1. Correção dos Loops de Recursão no LangGraph
*   **Problema**: O limite padrão de recursão do LangGraph era alcançado (limite 5 ou 10) porque o grafo entrava em loops infinitos, tentando chamar a ferramenta repetidas vezes após ela retornar um resultado.
*   **Resolução**: Refatoramos o nó `call_model` em `julius/agent/graph.py`. Adicionamos uma validação dinâmica da última mensagem do histórico (`last_msg`). Se o último evento for do tipo `ToolMessage`, o grafo desativa a vinculação de ferramentas e invoca o LLM base para sintetizar a resposta final de forma determinística, encerrando o grafo.

### 2. Separação de Prompts em Duas Etapas (Garantia de Foco)
*   **Problema**: O modelo de síntese final ficava confuso com regras de uso de ferramentas no prompt do sistema principal, e mesmo em passagens sem ferramentas associadas, ele tentava alucinar que "iria pesquisar" ou respondia evasivamente ("Qual é a sua pergunta?").
*   **Resolução**: Separamos a lógica de prompting em duas instruções claras:
    1.  **Prompt de Roteamento/Uso de Ferramentas**: Usado na primeira chamada com ferramentas ativas para decidir a execução (Weather, Time, Search, Reminder).
    2.  **Prompt de Síntese (`system_prompt_synthesis`)**: Usado na segunda chamada para formular o texto final. Remove todas as diretrizes de ferramentas e foca unicamente em ler os dados retornados no histórico recente e responder ao usuário diretamente de forma curta, amigável e conversacional.

### 3. Conversão de Papéis (Role-Conversion) no Histórico de Mensagens
*   **Problema**: Durante a fase de síntese final, a API do Groq e o modelo Llama tendiam a **ocultar ou ignorar** mensagens com o papel (`role`) `tool` por não estarem com ferramentas ativas no payload de envio da API. Isso fazia com que o modelo "esquecesse" o dado recém-calculado pela ferramenta (ex: a hora atual ou a temperatura).
*   **Resolução**: Criamos uma função de mapeamento de mensagens antes do envio ao modelo na fase de síntese:
    - Qualquer `AIMessage` contendo `tool_calls` é traduzida em uma resposta simples do assistente: `[Executando: nome_ferramenta(argumentos)]`.
    - Qualquer `ToolMessage` é traduzida em uma entrada de usuário: `[Resultado da ferramenta: conteúdo]`.
    - Isso garante que o histórico use exclusivamente os papéis padrão (`user` e `assistant`), que são 100% suportados e atendidos por qualquer template de chat de LLM.

### 4. Transição para `llama-3.3-70b-versatile` (Estabilidade de Ferramentas)
*   **Problema**: O modelo menor `llama-3.1-8b-instant` gerava as chamadas de ferramentas de forma inconsistente, emitindo tags XML parciais. A API do Groq rejeita essa sintaxe malformatada retornando erro `400`.
*   **Resolução**: Atualizamos a constante `GROQ_MODEL` para utilizar o **`llama-3.3-70b-versatile`**.

### 5. Limpeza de Logs, Warnings e Remoção de Streaming de Console
*   **Problema**: O console ficava poluído com avisos de depreciação (como `opentelemetry` e `torch.jit.load`), avisos de spaCy inexistente da biblioteca `mem0` e prints excessivos de debug interno (`[Agent Debug]`), além de streaming de tokens picado que dificultava a leitura da conversa.
*   **Resolução**:
    - Silenciamos `DeprecationWarning` e `UserWarning` no bootstrap do projeto (`julius/__init__.py` e `main.py`).
    - Configuramos o logger do `mem0` para apenas exibir erros (`logging.ERROR`).
    - Envolvemos inicializações críticas (como o Silero VAD e o Mem0) em blocos `warnings.catch_warnings()` locais para interceptar e esconder warnings de dependências.
    - Removemos todos os prints de depuração internos do agente (`[Agent Debug]`) e desativamos o streaming de console (usando chamada direta `llm.invoke()`), mas **mantivemos** os painéis e logs visuais sobre a consulta e recuperação de memórias de longo prazo (Mem0) para dar clareza de contexto ao usuário.

---

## 📅 Sessão: Segurança e Documentação da Arquitetura (08 de Junho de 2026)

### 1. Migração de Configurações para Variáveis de Ambiente (`.env`)
*   **Problema**: Credenciais sensíveis (como a chave `GROQ_API_KEY`) estavam hardcoded no arquivo de configuração `julius/core/config.py`.
*   **Resolução**:
    - Adicionamos a biblioteca `python-dotenv` ao projeto.
    - Criamos o arquivo local `.env` para armazenar de forma segura as variáveis (`GROQ_API_KEY`, `USE_GROQ`, `GROQ_MODEL`, e as URLs/modelos do Ollama).
    - Criamos o template `.env.example` sem as credenciais sensíveis para guiar novos setups do projeto.
    - Refatoramos `julius/core/config.py` para carregar o arquivo `.env` via `load_dotenv` e consultar os parâmetros usando `os.getenv`.

### 2. Controle de Versão e Exclusões do Git
*   **Problema**: Havia risco de commits acidentais de arquivos temporários, bancos de dados locais, modelos de IA gigantescos e credenciais de ambiente.
*   **Resolução**:
    - Criamos o arquivo `.gitignore` excluindo explicitamente a pasta `data/`, ambientes virtuais `venv/`, arquivos `.env`, além de pastas geradas por IDEs (`.vscode`, `.idea`) e cache do Python (`__pycache__`).

### 3. Documentação Completa da Arquitetura do Sistema
*   **Problema**: Faltava um guia descritivo e visual detalhando como a pilha local-híbrida de áudio e os grafos cognitivos interagem.
*   **Resolução**:
    - Escrevemos o arquivo `ARCHITECTURE.md` em inglês contendo:
        1. A jornada detalhada do usuário em formato de diagrama de sequência Mermaid.
        2. O fluxo de dados ponta a ponta (microfone -> VAD -> STT -> Memória -> LangGraph -> Tools -> TTS -> Alto-falante) em diagrama de fluxo Mermaid.
        3. A lista de recursos e a documentação das variáveis de configuração.

---

## 📌 Ponto de Parada Atual (Onde Paramos)


- **VAD, STT, TTS e Memória**: Todos os subsistemas locais funcionam de forma rápida e silenciosa.
- **Interface da CLI**: Extremamente limpa. Mostra apenas os painéis estilizados de conversa (Você e Julius) e o status temporário de pensamento do agente.
- **Cognitivo (Groq Cloud)**: O grafo do LangGraph executa com `llama-3.3-70b-versatile` e responde de forma limpa e direta.

### Como Rodar no Próximo Chat:
1. Ative o ambiente virtual e execute:
   ```powershell
   .\venv\Scripts\activate
   python main.py
   ```
2. Fale em português. A interação exibirá apenas os balões de conversa no terminal.
