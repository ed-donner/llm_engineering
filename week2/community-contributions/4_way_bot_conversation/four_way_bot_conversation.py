import os
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI


def build_discussion_prompt(bot_name: str, role_description: str, transcript: str) -> str:
    return f"""
You are {bot_name}.
Role:
{role_description}

Topic:
Global fuel crisis risk and the Strait of Hormuz tensions.

Conversation so far:
{transcript}

Instructions:
- Respond in 3-5 sentences.
- Keep the tone casual and conversational.
- Be specific and practical.
- Avoid extreme claims and avoid presenting uncertain details as facts.
- Build on what another bot said, then add your own view.
- End with one action or recommendation.
""".strip()


def build_agreement_prompt(
    bot_name: str, role_description: str, transcript: str, peer_names: List[str]
) -> str:
    peers_text = ", ".join(peer_names)
    return f"""
You are {bot_name}.
Role:
{role_description}

Conversation transcript:
{transcript}

Now write a short final agreement statement.
Rules:
- Pick exactly ONE peer from this list: {peers_text}
- Start with: "I agree most with <peer name> because ..."
- Mention 2 valid points from that peer.
- Keep it to 2-3 sentences and keep a casual tone.
""".strip()


def build_announcer_prompt(transcript: str, bot_names: List[str]) -> str:
    participants = ", ".join(bot_names)
    return f"""
You are an announcer judging a 4-LLM discussion.
Participants: {participants}

Full transcript:
{transcript}

Task:
- Pick one winner.
- Explain clearly why this LLM won.
- List the most valid points raised in the conversation.
- Mention whether all LLMs successfully agreed with one peer at the end.

Output format:
Winner: <name>
Why winner: <2-4 sentences>
Valid points:
- <point 1>
- <point 2>
- <point 3>
Agreement check: <1-2 sentences>
""".strip()


def format_transcript(history: List[Dict[str, str]]) -> str:
    if not history:
        return "(No discussion yet)"
    return "\n".join(f"{turn['speaker']}: {turn['message']}" for turn in history)


def call_model(
    client: OpenAI,
    model: str,
    bot_name: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def run_conversation() -> None:
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    bots = [
        {
            "name": "Asha (Energy Economist)",
            "role": (
                "Focus on oil supply, pricing, inflation pass-through, and macroeconomic impact."
            ),
        },
        {
            "name": "Reza (Geopolitical Risk Analyst)",
            "role": (
                "Focus on regional tensions, maritime chokepoints, and probability-based risk framing."
            ),
        },
        {
            "name": "Mina (Shipping & Logistics Expert)",
            "role": (
                "Focus on tanker routes, insurance costs, rerouting constraints, and delivery timelines."
            ),
        },
        {
            "name": "Omar (Public Policy Advisor)",
            "role": (
                "Focus on policy responses: reserves, subsidies, demand management, and communication."
            ),
        },
    ]

    history: List[Dict[str, str]] = [
        {
            "speaker": "Moderator",
            "message": (
                "Welcome everyone. Discuss the current fuel-crisis risk linked to Strait of Hormuz "
                "tensions. Keep it factual, practical, and avoid sensationalism."
            ),
        }
    ]

    print("\n=== 4-Way LLM Conversation ===")
    print("Topic: Fuel crisis risk and Strait of Hormuz tensions\n")
    print(f"Moderator: {history[0]['message']}\n")

    # Casual discussion phase (single flowing conversation, no rounds).
    speaking_order = [
        bots[0],
        bots[1],
        bots[2],
        bots[3],
        bots[0],
        bots[2],
        bots[1],
        bots[3],
    ]

    for bot in speaking_order:
        transcript = format_transcript(history)
        system_prompt = (
            f"You are {bot['name']}. Stay in character and keep your tone consistent."
        )
        user_prompt = build_discussion_prompt(bot["name"], bot["role"], transcript)
        reply = call_model(client, model, bot["name"], system_prompt, user_prompt)
        history.append({"speaker": bot["name"], "message": reply})
        print(f"{bot['name']}: {reply}\n")

    print("--- Final Agreement Statements ---")
    bot_names = [b["name"] for b in bots]

    for bot in bots:
        transcript = format_transcript(history)
        peer_names = [name for name in bot_names if name != bot["name"]]
        system_prompt = (
            f"You are {bot['name']}. Be concise and follow the required sentence starter exactly."
        )
        user_prompt = build_agreement_prompt(
            bot["name"], bot["role"], transcript, peer_names
        )
        agreement = call_model(client, model, bot["name"], system_prompt, user_prompt)
        history.append({"speaker": f"{bot['name']} (Agreement)", "message": agreement})
        print(f"{bot['name']} (Agreement): {agreement}\n")

    print("--- Announcer Verdict ---")
    transcript = format_transcript(history)
    announcer_system = "You are a neutral and concise announcer."
    announcer_user = build_announcer_prompt(transcript, bot_names)
    verdict = call_model(client, model, "Announcer", announcer_system, announcer_user)
    history.append({"speaker": "Announcer", "message": verdict})
    print(f"Announcer:\n{verdict}\n")

    print("=== End of Conversation ===")


if __name__ == "__main__":
    run_conversation()
