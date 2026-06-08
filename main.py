import os
import sys
import warnings
import logging

# Suppress warnings and noisy logs early on startup
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("mem0").setLevel(logging.ERROR)

import queue
import time
from datetime import datetime
import numpy as np
import sounddevice as sd


# Rich Console imports for terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.status import Status

# Import Julius modular package components
from julius.vad import VADDetector
from julius.stt import STTTranscriber
from julius.memory import search_memory, save_memory
from julius.agent import agent_graph
from julius.tts import TTSPlayer
from julius.core.config import DATA_DIR

# Initialize rich console
console = Console()

# Ensure logging directory exists using config DATA_DIR
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "chat_logs.txt")

def log_interaction(timestamp, user_input, agent_response, memories):
    """
    Logs the conversation turn with context to a local text file.
    """
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- TURN START: {timestamp} ---\n")
            f.write(f"USER: {user_input}\n")
            f.write(f"RETRIEVED MEMORIES: {memories}\n")
            f.write(f"AGENT RESPONSE: {agent_response}\n")
            f.write("--- TURN END ---\n\n")
    except Exception as e:
        console.print(f"[red]Erro ao gravar log: {e}[/red]")

def main():
    console.clear()
    console.print(Panel.fit(
        "[bold purple]🔮 JULIUS VOICE AGENT — LOCAL STACK[/bold purple]\n"
        "[bold white]Desenvolvedor: Júlio Emanoel[/bold white]\n"
        "Status: [green]Inicializando componentes locais...[/green]\n"
        "Stack: VAD (Silero) | STT (Whisper) | LLM (Ollama) | Memory (Mem0) | TTS (Kokoro/Piper)",
        border_style="purple"
    ))

    # Initialize components
    try:
        vad = VADDetector()
        stt = STTTranscriber()
        tts = TTSPlayer()
    except Exception as e:
        console.print(f"[bold red]Erro crítico na inicialização dos componentes: {e}[/bold red]")
        sys.exit(1)

    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time, status):
        # We put incoming chunks of shape (512, 1) directly into the queue
        audio_queue.put(indata.copy())

    # Set up sounddevice InputStream (16000Hz, Mono, float32, blocksize 512)
    stream = sd.InputStream(
        samplerate=16000,
        channels=1,
        blocksize=512,
        callback=audio_callback,
        dtype='float32'
    )

    console.print(Panel(
        "[bold green]Julius está online e pronto para ouvir![/bold green]\n"
        "Fale livremente em português brasileiro (pt-BR).\n"
        "O detector de voz processará sua fala após 3 segundos de silêncio.\n"
        "Pressione [bold red]Ctrl + C[/bold red] para encerrar a sessão.",
        title="[bold green]SISTEMA ONLINE[/bold green]",
        border_style="green"
    ))

    try:
        with stream:
            while True:
                try:
                    # Read chunks from audio queue
                    try:
                        chunk = audio_queue.get(timeout=1.0)
                    except queue.Empty:
                        continue

                    # Process chunk in VAD (using the mono channel)
                    utterance = vad.process_chunk(chunk[:, 0])

                    if utterance is not None:
                        # VAD triggered a complete utterance
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        console.print("\n[bold yellow]🎤 Processando áudio capturado...[/bold yellow]")
                        
                        # 1. Speech-To-Text transcription
                        transcription = stt.transcribe(utterance)
                        if not transcription.strip():
                            console.print("[dim yellow]🔇 Áudio recebido, mas nenhuma fala clara foi compreendida.[/dim yellow]")
                            continue

                        console.print(Panel(
                            f"[bold white]{transcription}[/bold white]",
                            title="[bold cyan]Você[/bold cyan]",
                            border_style="cyan"
                        ))

                        # 2. Long-term Memory Retrieval
                        console.print("[dim]🧠 Consultando memórias de longo prazo (Mem0)...[/dim]")
                        memories = search_memory(transcription)
                        memory_context = "\n".join(memories) if memories else ""
                        if memories:
                            console.print(f"[dim green]📚 Memórias recuperadas: {len(memories)}[/dim green]")
                            for m in memories:
                                console.print(f"  - {m}")
                        else:
                            console.print("[dim]📚 Nenhuma memória relevante encontrada.[/dim]")


                        # 3. Invoke LangGraph Agent workflow
                        with Status("[bold yellow]🧠 Julius está pensando...[/bold yellow]", spinner="dots") as status:
                            config = {
                                "configurable": {"thread_id": "main_session"},
                                "recursion_limit": 5
                            }
                            inputs = {
                                "messages": [("user", transcription)],
                                "memory_context": memory_context
                            }
                            result = agent_graph.invoke(inputs, config=config)
                            
                            # Extract final text output from the graph
                            final_response = result["messages"][-1].content

                        # 4. Stream TTS response sentence-by-sentence
                        console.print("[bold green]🔊 Falando...[/bold green]")
                        # Stop input stream to prevent feedback/echo from the speakers
                        stream.stop()
                        
                        tts.speak_stream([final_response])

                        # Print final output to console
                        console.print(Panel(
                            f"[bold green]{final_response}[/bold green]",
                            title="[bold green]Julius[/bold green]",
                            border_style="green"
                        ))

                        # 5. Save turn facts to long-term memory
                        turn_text = f"User: {transcription}\nAgent: {final_response}"
                        save_memory(turn_text)

                        # 6. Log interaction
                        log_interaction(timestamp, transcription, final_response, memories)
                        
                        # Discard any audio buffered during TTS playback and reset VAD state
                        while not audio_queue.empty():
                            try:
                                audio_queue.get_nowait()
                            except queue.Empty:
                                break
                        vad.reset()
                        
                        # Resume sound input stream
                        stream.start()

                except Exception as e:
                    console.print(f"[bold red]Ocorreu um erro ao processar a resposta: {e}[/bold red]")
                    continue
    except KeyboardInterrupt:
        console.print("\n[bold red]Encerrando o Julius Voice Agent. Até logo![/bold red]")

if __name__ == "__main__":
    main()
