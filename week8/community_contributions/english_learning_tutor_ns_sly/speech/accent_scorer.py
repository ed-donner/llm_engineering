import torch
import librosa
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2Model
from scipy.spatial.distance import cosine


class AccentScorer:
    """
    Accent similarity scoring using Wav2Vec2 embeddings.

    Compares user pronunciation with reference pronunciation
    to estimate accent similarity.
    """

    def __init__(self):

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.processor = Wav2Vec2Processor.from_pretrained(
            "facebook/wav2vec2-base"
        )

        self.model = Wav2Vec2Model.from_pretrained(
            "facebook/wav2vec2-base"
        ).to(self.device)

        self.model.eval()

    def load_audio(self, path):
        """
        Load audio and resample to 16kHz mono
        """

        waveform, sr = librosa.load(path, sr=16000, mono=True)

        return waveform

    def embedding(self, waveform):
        """
        Generate speech embedding using wav2vec2
        """

        inputs = self.processor(
            waveform,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )

        input_values = inputs.input_values.to(self.device)

        with torch.no_grad():
            outputs = self.model(input_values)

        hidden_states = outputs.last_hidden_state

        # Mean pooling across time dimension
        embedding = torch.mean(hidden_states, dim=1)

        return embedding.squeeze().cpu().numpy()

    def score(self, user_audio, reference_audio):
        """
        Compute accent similarity score (0–100)
        """

        user_waveform = self.load_audio(user_audio)
        ref_waveform = self.load_audio(reference_audio)

        user_emb = self.embedding(user_waveform)
        ref_emb = self.embedding(ref_waveform)

        similarity = 1 - cosine(user_emb, ref_emb)

        score = max(0, similarity * 100)

        return float(score)