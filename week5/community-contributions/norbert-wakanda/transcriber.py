from transformers import pipeline
import torch




def transcriber(path_to_file: str) -> str:
    # Initialize the automatic speech recognition pipeline using Whisper
    # This loads the model into memory and prepares it for inference.
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-tiny.en",
        dtype=torch.float32,
        device="cpu",

        # Enable timestamps in the output for word/segment-level alignment.
        return_timestamps=True,
    )

    # Pass the audio file path to the pipeline for transcription.
    result = pipe(path_to_file)

    transcription = result["text"]

    # Return the final transcription string to the caller.
    return transcription

print(transcriber("response.mp3"))