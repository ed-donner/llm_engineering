import numpy 
import sounddevice as sd
import threading
from config import sampling_rate, dtype, channels, device


speech = []
is_recording = False

def call_back(indata, frames, time, status): 
    if is_recording:
        chunk = numpy.frombuffer(indata, dtype='float32').copy()
        speech.append(chunk)

def record_audio():
    with sd.RawInputStream(samplerate=sampling_rate, dtype=dtype, callback=call_back, channels=channels, device=device):
        while is_recording:
            pass

def start_audio_process():
    thread1 = threading.Thread(target=record_audio)
    thread1.start()


def get_audio():
    return numpy.concatenate(speech)

def start_recording():
    global is_recording
    speech.clear()
    is_recording = True

def stop_recording():
    global is_recording
    is_recording = False

def is_currently_recording():
    return is_recording

def is_speech_empty():
    return len(speech) == 0