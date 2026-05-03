MODEL_OPTIONS = {
    "qwen_72b": {
        "label": "Qwen 2.5 72B Instruct",
        "provider": "huggingface",
        "model_name": "Qwen/Qwen2.5-72B-Instruct",
    },
    "gpt_4_1_mini": {
        "label": "GPT-4.1 mini",
        "provider": "openai",
        "model_name": "gpt-4.1-mini",
    },
}

DEFAULT_MODEL_KEY = "qwen_72b"


def get_model_option(model_key):
    try:
        return MODEL_OPTIONS[model_key]
    except KeyError as exc:
        allowed = ", ".join(MODEL_OPTIONS)
        raise ValueError(
            f"Unknown model '{model_key}'. Allowed values: {allowed}"
        ) from exc


def get_model_labels():
    return {config["label"]: key for key, config in MODEL_OPTIONS.items()}
