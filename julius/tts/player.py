import os
import zipfile
import requests
import numpy as np
import sounddevice as sd
import subprocess
import shutil
from julius.core.config import TTS_MODELS_DIR

# Ensure models directory exists
os.makedirs(TTS_MODELS_DIR, exist_ok=True)

# Programmatically locate and copy ESPEAK_DATA_PATH for Kokoro TTS to an ASCII-only path
try:
    import espeakng_loader
    loader_dir = os.path.dirname(espeakng_loader.__file__)
    src_data_path = os.path.join(loader_dir, "espeak-ng-data")
    
    # Safe ASCII-only path inside Gemini AppData directory
    safe_data_dir = r"C:\Users\lemos\.gemini\antigravity\espeak-ng-data"
    
    if os.path.exists(src_data_path):
        if not os.path.exists(safe_data_dir):
            print(f"[TTS] Copiando tabelas de fonemas para caminho seguro sem acentos: {safe_data_dir}...")
            shutil.copytree(src_data_path, safe_data_dir)
        os.environ["ESPEAK_DATA_PATH"] = safe_data_dir
        print(f"[TTS] ESPEAK_DATA_PATH configurado com segurança em: {safe_data_dir}")
except Exception as e:
    print(f"[TTS][Aviso] Não foi possível configurar ESPEAK_DATA_PATH via safe copy: {e}")

def download_file(url, dest):
    if os.path.exists(dest):
        return
    print(f"[TTS] Baixando {os.path.basename(dest)} de {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"[TTS] Download de {os.path.basename(dest)} finalizado.")

def setup_piper():
    piper_dir = os.path.join(TTS_MODELS_DIR, "piper")
    piper_exe = os.path.join(piper_dir, "piper.exe")
    
    if not os.path.exists(piper_exe):
        zip_path = os.path.join(TTS_MODELS_DIR, "piper_windows_amd64.zip")
        download_file(
            "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip",
            zip_path
        )
        print("[TTS] Extraindo Piper para Windows...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(TTS_MODELS_DIR)
        print("[TTS] Piper extraído com sucesso.")
        try:
            os.remove(zip_path)
        except Exception:
            pass
            
    # Download Portuguese voice model and config
    download_file(
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
        os.path.join(TTS_MODELS_DIR, "pt_BR-faber-medium.onnx")
    )
    download_file(
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json",
        os.path.join(TTS_MODELS_DIR, "pt_BR-faber-medium.onnx.json")
    )
    
    return piper_exe, os.path.join(TTS_MODELS_DIR, "pt_BR-faber-medium.onnx")

def setup_kokoro():
    onnx_path = os.path.join(TTS_MODELS_DIR, "kokoro-v1.0.onnx")
    voices_path = os.path.join(TTS_MODELS_DIR, "voices-v1.0.bin")
    
    download_file(
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        onnx_path
    )
    download_file(
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
        voices_path
    )
    return onnx_path, voices_path

def play_piper(text: str, piper_exe: str, model_path: str):
    try:
        p = subprocess.Popen(
            [piper_exe, "-m", model_path, "--output_raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        
        p.stdin.write(text.encode('utf-8'))
        p.stdin.close()
        
        raw_data = p.stdout.read()
        p.wait()
        
        if len(raw_data) > 0:
            audio_array = np.frombuffer(raw_data, dtype=np.int16)
            sd.play(audio_array, 22050)
            sd.wait()
    except Exception as e:
        print(f"[TTS][Piper Erro] Falha ao reproduzir áudio com Piper: {e}")

class KokoroPlayer:
    def __init__(self, onnx_path, voices_path, safe_data_path=None):
        from kokoro_onnx import Kokoro
        if safe_data_path:
            from kokoro_onnx.config import EspeakConfig
            espeak_config = EspeakConfig(data_path=safe_data_path)
            self.kokoro = Kokoro(onnx_path, voices_path, espeak_config=espeak_config)
        else:
            self.kokoro = Kokoro(onnx_path, voices_path)
        
    def play(self, text: str):
        samples, sample_rate = self.kokoro.create(
            text,
            voice="pf_dora",
            speed=1.0,
            lang="pt-br"
        )
        sd.play(samples, sample_rate)
        sd.wait()

class TTSPlayer:
    def __init__(self):
        self.kokoro_player = None
        self.piper_exe = None
        self.piper_model = None
        
        print("[TTS] Inicializando sistema de TTS (Kokoro/Piper)...")
        # Try to setup Kokoro TTS
        try:
            onnx_path, voices_path = setup_kokoro()
            safe_dir = globals().get("safe_data_dir")
            self.kokoro_player = KokoroPlayer(onnx_path, voices_path, safe_data_path=safe_dir)
            print("[TTS] Kokoro TTS inicializado (Voz Principal).")
        except Exception as e:
            print(f"[TTS][Aviso] Kokoro TTS falhou ao inicializar: {e}")
            print("[TTS] Configurando Piper TTS como fallback...")
            try:
                self.piper_exe, self.piper_model = setup_piper()
                print("[TTS] Piper TTS inicializado (Voz de Fallback).")
            except Exception as pe:
                print(f"[TTS][Erro] Falha ao inicializar o fallback do Piper TTS: {pe}")
                
    def speak(self, text: str):
        if not text.strip():
            return
            
        # Try Kokoro first
        if self.kokoro_player:
            try:
                self.kokoro_player.play(text)
                return
            except Exception as e:
                print(f"[TTS][Aviso] Falha no Kokoro TTS ao falar: {e}. Alternando para Piper...")
                if not self.piper_exe:
                    try:
                        self.piper_exe, self.piper_model = setup_piper()
                    except Exception as pe:
                        print(f"[TTS][Erro] Não foi possível carregar o Piper: {pe}")
                        return
                        
        # Fallback to Piper
        if self.piper_exe and self.piper_model:
            play_piper(text, self.piper_exe, self.piper_model)
        else:
            print(f"[TTS][Erro] Nenhum serviço de voz disponível para ler: '{text}'")

    def speak_stream(self, text_generator):
        buffer = ""
        for chunk in text_generator:
            if isinstance(chunk, str):
                text_chunk = chunk
            else:
                text_chunk = chunk.content if hasattr(chunk, 'content') else str(chunk)
                
            buffer += text_chunk
            
            while True:
                idx = -1
                for p in ['.', '!', '?', '\n']:
                    p_idx = buffer.find(p)
                    if p_idx != -1 and (idx == -1 or p_idx < idx):
                        idx = p_idx
                        
                if idx == -1:
                    break
                    
                sentence = buffer[:idx+1].strip()
                buffer = buffer[idx+1:]
                
                if sentence:
                    sentence_cleaned = sentence.replace("*", "").replace("#", "").strip()
                    if sentence_cleaned:
                        self.speak(sentence_cleaned)
                        
        if buffer.strip():
            sentence_cleaned = buffer.strip().replace("*", "").replace("#", "").strip()
            if sentence_cleaned:
                self.speak(sentence_cleaned)
