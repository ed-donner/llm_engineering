from openai import OpenAI
from agents.base_agent import BaseAgent

TRIAGE_LEVELS = ["Immediate", "Urgent", "Semi-urgent", "Non-urgent"]

SYSTEM_MSG = """You are a senior emergency medicine consultant.
Classify the patient presentation into exactly one triage level: Immediate, Urgent, Semi-urgent, or Non-urgent.
Respond with one word only."""


class FrontierAgent(BaseAgent):
    """GPT-4.1-mini zero-shot triage classification. Fast and capable, but requires internet."""

    color = BaseAgent.BLUE

    def __init__(self):
        self.client = OpenAI()
        self.log("FrontierAgent ready (GPT-4.1-mini)")

    def classify(self, presentation: str) -> str:
        self.log(f"Classifying: {presentation[:60]}...")
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user", "content": f"Triage this patient:\n{presentation}"},
            ],
            max_tokens=10,
            temperature=0,
        )
        result = response.choices[0].message.content.strip()
        for level in TRIAGE_LEVELS:
            if level.lower() in result.lower():
                self.log(f"Result: {level}")
                return level
        self.log(f"Unknown result: {result}")
        return "Unknown"
