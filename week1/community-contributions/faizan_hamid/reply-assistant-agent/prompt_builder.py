def build_system_prompt() -> str:
    """
    Defines the role and response style of the AI Reply Assistant.
    """
    return """
You are a professional communication assistant.

Your task is to write polished, natural, professional replies to emails or work-related messages.

You will be given:
- an incoming message
- the detected message intent
- the suggested reply goal
- the preferred tone

Your response should:
1. Write a professional reply that directly addresses the incoming message.
2. Keep the tone natural, clear, and polite.
3. Avoid sounding robotic or overly generic.
4. Be concise unless the situation clearly needs more detail.
5. If the incoming message is about an interview, recruiter outreach, follow-up, leave, or meeting scheduling, tailor the response appropriately.

Return the answer in markdown with this structure:

# Reply Draft

## Suggested Reply
<write the full reply here>

Do not wrap the response in a code block.
""".strip()


def build_user_prompt(
    cleaned_message: str,
    detected_intent: str,
    reply_goal: str,
    tone: str = "professional"
) -> str:
    """
    Build the user prompt for the reply generation request.
    """
    return f"""
Please write a reply to the following incoming message.

Detected Intent: {detected_intent}
Suggested Reply Goal: {reply_goal}
Preferred Tone: {tone}

Incoming Message:
{cleaned_message}
""".strip()