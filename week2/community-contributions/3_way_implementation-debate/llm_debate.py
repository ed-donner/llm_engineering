'''
This will be a debate between two llms. One will be Sarvam and the other will be DeepSeek.
(Sarvan is a free indian model I found.)
Deepseek will double as the moderator and will ask the questions.
The topic will be "Is genetic modification of food or embryos ethical?"
'''
import os
from dotenv import load_dotenv
from openai import OpenAI
from sarvamai import SarvamAI
from rich.console import Console
from rich.markdown import Markdown

load_dotenv(override=True)

console = Console()
sarvam_api_key = os.getenv("SARVAM_API_KEY")
sarvam_base_url = "https://api.sarvam.ai/v1"
api_key = os.getenv('DEEPSEEK_API_KEY')
deepseek = OpenAI(base_url="https://api.deepseek.com/v1", api_key=api_key)
sarvam = SarvamAI(
    api_subscription_key=sarvam_api_key,
)

# let's define their roles

# Deepseek is Moderationm(Dr Rosaline Tah)
PROMPT_MODERATOR = "You are Dr. Rosaline Tah, a neutral bioethics expert moderating this debate. \
    Stay impartial, composed, and highly intelligent—clarify science, enforce timing \
    (warn at 30s, cut off after), and pose balanced questions. Structure: Introduce topic/teams, \
    manage turns (Opening 3min equiv., Rebuttals 2min, Q&A, Closings), invite audience input if any. \
    Never take sides. Respond only to direct cues like 'Moderator: Start debate'."

# Sarvam is Felix Nji (for)
PROMPT_FELIX = "You are Felix Nji, arguing FOR genetic modification of food/embryos. \
    Attitude: Enthusiastic, optimistic. Intelligence: Sharp analytical—use data on benefits \
    (e.g., Golden Rice for malnutrition, CRISPR for diseases). Stay in character: \
    Passionate defenses, rebut skeptics logically. Speak only on your turn (e.g., 'Felix: Opening'). \
    No ad hominem."

# Deepseek is James Fru (against)
PROMPT_JAMES = "You are James Fru, arguing AGAINST genetic modification of food/embryos. \
    Attitude: Cautious, skeptical. Intelligence: Rigorous logical—highlight risks \
    (ecological harm, ethical slippery slopes like eugenics). Stay in character: \
    Methodical critiques, probe long-term impacts. Speak only on your turn (e.g., 'James: Rebuttal'). \
    No ad hominem."


def call_deepseek(system_prompt: str, history: list[str], instruction: str,
                  model: str = "deepseek-chat", max_tokens: int = 400) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "History:\n" + "\n".join(history[-6:]) + f"\n\nInstruction: {instruction}"},
    ]
    response = deepseek.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def call_sarvam( history: list[str], instruction: str,
                max_tokens: int = 400) -> str:
    prompt = PROMPT_FELIX + "\n\nHistory:\n" + "\n".join(history[-6:]) + f"\n\nInstruction: {instruction}"
    messages = [
        {"role": "system", "content": PROMPT_FELIX},
        {"role": "user", "content": prompt},
    ]
    
    response = sarvam.chat.completions(messages = messages, max_tokens=int(max_tokens))
    # `resp` is usually a string-like object, depending on wrapper
    return response.choices[0].message.content

# Debate structure stages
stages = [
    ("Introduction", "Introduce topic, teams, and rules.", "MODERATOR"),
    ("Opening Pro", "Present opening argument FOR.", "FELIX"),
    ("Opening Against", "Present opening argument AGAINST.", "JAMES"),
    ("Rebuttal 1 Against", "Rebut Pro's opening.", "JAMES"),
    ("Rebuttal 1 Pro", "Rebut Against's opening.", "FELIX"),
    ("Q&A Moderator Q1", "Pose Q1: How do benefits outweigh risks? Then teams respond.", "MODERATOR"),
    ("Q&A Pro Response", "Respond to Q1.", "FELIX"),
    ("Q&A Against Response", "Respond to Q1.", "JAMES"),
    ("Closing Pro", "Closing: Why Pro wins.", "FELIX"),
    ("Closing Against", "Closing: Why Against wins.", "JAMES"),
    ("Moderator Close", "Neutral recap and end.", "MODERATOR")
]

def run_debate():
    history: list[str] = []
    transcript: list[str] = []

    print("=== Debate Simulation (DeepSeek + Sarvam) ===\n")

    for stage_name, instruction, speaker in stages:
        if speaker == "MODERATOR":
            system_prompt = PROMPT_MODERATOR
            text = call_sarvam( history, f"{stage_name}: {instruction}", max_tokens=400)
        elif speaker == "FELIX":
            system_prompt = PROMPT_FELIX
            text = call_deepseek(system_prompt, history, f"{stage_name}: {instruction}")
        else:  # JAMES
            system_prompt = PROMPT_JAMES
            text = call_deepseek(system_prompt, history, f"{stage_name}: {instruction}")

        history.append(text)
        transcript.append(f"\n--- {stage_name} / {speaker} ---\n{text}\n")
        print(text)
        print("-" * 60)

    print("\n=== FULL TRANSCRIPT ===")
    print("".join(transcript))

if __name__ == "__main__":
    run_debate()


