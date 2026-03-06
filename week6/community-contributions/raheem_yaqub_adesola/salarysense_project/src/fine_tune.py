from openai import OpenAI
from src.config import MODEL_NAME

client = OpenAI()

def start_fine_tuning(train_file, val_file=None):
    job = client.fine_tuning.jobs.create(
        training_file=train_file,
        validation_file=val_file,
        model=MODEL_NAME
    )
    return job
