import numpy as np
from faster_whisper import WhisperModel

class STTTranscriber:
    def __init__(self, model_size="small", device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        
        print(f"[STT] Carregando modelo Whisper '{self.model_size}' no {self.device} ({self.compute_type})...")
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        print("[STT] Modelo Whisper carregado com sucesso!")
        
    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribes a float32 numpy array of audio (16kHz sample rate).
        Forces Brazilian Portuguese language.
        Returns the transcription text.
        """
        if len(audio_data) == 0:
            return ""
            
        segments, info = self.model.transcribe(
            audio_data, 
            language="pt", 
            beam_size=1,
            temperature=0.0
        )
        
        text = ""
        for segment in segments:
            text += segment.text
            
        return text.strip()
