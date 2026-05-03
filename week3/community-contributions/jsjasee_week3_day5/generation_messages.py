from model_options import get_model_option


def build_generation_messages(model_key, preset, prompt):
    model_option = get_model_option(model_key)
    schema_text = ", ".join(preset["fields"])
    rules_text = " ".join(preset["rules"])

    system_message = (
        f"Generate synthetic {preset['label'].lower()} data. "
        f"Required fields: {schema_text}. "
        f"{rules_text} "
        "Check your own output before answering. "
        "Return only valid, parseable JSON as a list of objects. "
        "Do not use markdown, backticks, comments, or explanations. "
        "If any row or field is wrong, fix it before returning the final answer."
    )

    if model_option["provider"] == "openai":
        system_message += " Output must be pure JSON only."

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
