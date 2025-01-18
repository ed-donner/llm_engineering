from .open_ai import OpenAISummarize

SUPPORTED_MODELS = {
    "openai": {
        "summarize": "OpenAISummarize",
    },
    "ollama": {
        "summarize": "OllamaSummarize"
    },
}


def llm_builder(model_type: str, model_name: str, crawl_type: str):
    if model_type not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model type: {model_type}")

    if crawl_type not in SUPPORTED_MODELS[model_type]:
        raise ValueError(f"Crawl type '{crawl_type}' not supported for model type '{model_type}'")

    class_name = SUPPORTED_MODELS[model_type][crawl_type]

    service_class = globals()[class_name]

    return service_class(model_name)
