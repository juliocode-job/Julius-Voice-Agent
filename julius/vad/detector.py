import numpy as np
import torch
from collections import deque

class VADDetector:
    def __init__(self, sample_rate=16000, chunk_size=512, silence_threshold_seconds=3.0, pre_buffer_seconds=0.5):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.silence_threshold_seconds = silence_threshold_seconds
        self.pre_buffer_seconds = pre_buffer_seconds
        
        # Configure torch to use single thread for optimal VAD performance
        torch.set_num_threads(1)
        
        # Load silero-vad model (bypass interactive trust prompt with trust_repo=True)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True
            )

        
        # VAD settings
        self.speech_threshold = 0.5
        
        # Pre-buffer to keep the beginning of sentences (0.5s)
        pre_buffer_len = int(np.ceil(pre_buffer_seconds * sample_rate / chunk_size))
        self.pre_buffer = deque(maxlen=pre_buffer_len)
        self.speech_buffer = []
        
        # Silence state tracking
        self.speech_started = False
        self.max_silence_frames = int(np.ceil(silence_threshold_seconds * sample_rate / chunk_size))
        self.silence_frames = 0
        
    def process_chunk(self, chunk: np.ndarray) -> np.ndarray | None:
        """
        Processes a single audio chunk of size 512.
        Returns the full speech array as a 1D float32 numpy array when speech ends, otherwise None.
        """
        if chunk.ndim > 1:
            chunk = chunk.squeeze()
        chunk = chunk.astype(np.float32)
        
        # Ensure we have exactly the chunk_size
        if len(chunk) < self.chunk_size:
            chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)), 'constant')
        
        # Predict speech probability
        tensor_chunk = torch.from_numpy(chunk).unsqueeze(0)
        with torch.no_grad():
            speech_prob = self.model(tensor_chunk, self.sample_rate).item()
            
        if not self.speech_started:
            self.pre_buffer.append(chunk)
            if speech_prob > self.speech_threshold:
                self.speech_started = True
                self.speech_buffer = list(self.pre_buffer)
                self.silence_frames = 0
        else:
            self.speech_buffer.append(chunk)
            
            if speech_prob > self.speech_threshold:
                self.silence_frames = 0
            else:
                self.silence_frames += 1
                
            if self.silence_frames >= self.max_silence_frames:
                utterance = np.concatenate(self.speech_buffer)
                self.reset()
                return utterance
                
        return None
        
    def reset(self):
        self.speech_started = False
        self.speech_buffer = []
        self.pre_buffer.clear()
        self.silence_frames = 0
        self.model.reset_states()
