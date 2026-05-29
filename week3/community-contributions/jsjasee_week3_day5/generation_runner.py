from generation_messages import build_generation_messages
from model_options import get_model_option


def generate_raw_json(
    dataset_type,
    prompt,
    temperature,
    max_tokens,
    preset,
    model_key,
    hf_client,
    openai_client,
):
    messages = build_generation_messages(model_key, preset, prompt)
    model_option = get_model_option(model_key)

    if model_option["provider"] == "huggingface":
        completion = hf_client.chat.completions.create(
            model=model_option["model_name"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content.strip()

    if model_option["provider"] == "openai":
        response = openai_client.responses.create(
            model=model_option["model_name"],
            input=messages,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        return response.output_text.strip()

    raise ValueError(f"Unsupported provider: {model_option['provider']}")
