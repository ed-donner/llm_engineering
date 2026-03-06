import os
import gradio as gr
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def validate_audio(filepath: str) -> tuple[bool, str]:
    """Validate audio before sending to STT model."""
    
    if not filepath:
        return False, "No audio recorded"

    # 1. File exists and has content
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return False, "Audio file is empty"

    # 2. File size limits
    size_mb = file_size / (1024 * 1024)
    if size_mb > 25:
        return False, f"File too large ({size_mb:.1f}MB). Max 25MB for Whisper."

    # 3. Load and check duration
    try:
        audio = AudioSegment.from_file(filepath)
    except Exception as e:
        return False, f"Invalid audio format: {e}"

    duration_sec = len(audio) / 1000

    if duration_sec < 0.5:
        return False, "Recording too short (< 0.5s)"

    if duration_sec > 600:
        return False, "Recording too long (> 10 min). Consider splitting."

    # 4. Check if it's mostly silence
    nonsilent = detect_nonsilent(
        audio,
        min_silence_len=500,   # 500ms silence threshold
        silence_thresh=-40      # dBFS threshold
    )
    
    if not nonsilent:
        return False, "Recording is silent — no speech detected"

    speech_duration = sum(end - start for start, end in nonsilent) / 1000
    speech_ratio = speech_duration / duration_sec

    if speech_ratio < 0.1:
        return False, f"Only {speech_ratio:.0%} speech detected. Mostly silence."

    # 5. Check audio level (too quiet?)
    if audio.dBFS < -50:
        return False, f"Audio too quiet ({audio.dBFS:.1f} dBFS). Speak closer to mic."

    # 6. Check sample rate (optional but good to know)
    if audio.frame_rate < 8000:
        return False, f"Sample rate too low ({audio.frame_rate}Hz). Min 8kHz recommended."

    return True, f"Valid — {duration_sec:.1f}s, {speech_ratio:.0%} speech, {audio.dBFS:.1f} dBFS"

