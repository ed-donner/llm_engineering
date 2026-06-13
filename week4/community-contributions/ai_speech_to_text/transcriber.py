from transformers import pipeline
import torch
from config import sampling_rate, model


pipe = pipeline(
    task='automatic-speech-recognition',
    model=model,
    device="cuda",
    dtype=torch.float16,
    generate_kwargs={"language": "english"}
)

def convert_audio_to_text(recording):
    print('converting audio to text')

    input_dict = {
        "sampling_rate": sampling_rate,
        "raw": recording
    }
    result = pipe(input_dict)
    text = result['text']

    print('Conversion done.')

    return text