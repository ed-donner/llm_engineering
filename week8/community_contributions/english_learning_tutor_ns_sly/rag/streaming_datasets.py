from datasets import load_dataset
import random


class StreamingDatasetLoader:
    """
    Streams English sentences from HuggingFace datasets
    without downloading locally.
    """

    def __init__(self):
        self.cache = {}

    def load_dataset(self, dataset_name):

        if dataset_name in self.cache:
            return self.cache[dataset_name]

        if dataset_name == "librispeech":
            ds = load_dataset(
                "librispeech_asr",
                "clean",
                split="train.100",
                streaming=True
            )

        elif dataset_name == "daily_dialog":
            ds = load_dataset(
                "daily_dialog",
                split="train",
                streaming=True
            )

        elif dataset_name == "books":
            ds = load_dataset(
                "opus_books",
                "en-fr",
                split="train",
                streaming=True
            )

        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")

        self.cache[dataset_name] = ds
        return ds

    def sample_sentences(self, dataset_name, n=20):

        dataset = self.load_dataset(dataset_name)

        sentences = []

        for example in dataset:

            if dataset_name == "librispeech":
                text = example.get("text", "")
                if text:
                    sentences.append(text)

            elif dataset_name == "daily_dialog":
                dialog = example.get("dialog", [])
                sentences.extend(dialog)

            elif dataset_name == "books":
                text = example.get("translation", {}).get("en", "")
                if text:
                    sentences.append(text)

            if len(sentences) >= n * 3:
                break

        random.shuffle(sentences)

        return sentences[:n]