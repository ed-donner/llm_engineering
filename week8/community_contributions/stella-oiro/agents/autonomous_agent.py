import json
from openai import OpenAI
from agents.base_agent import BaseAgent
from agents.ensemble_agent import EnsembleAgent
from agents.messenger_agent import MessengerAgent

TRIAGE_LEVELS = ["Immediate", "Urgent", "Semi-urgent", "Non-urgent"]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "triage_patient",
            "description": "Classify triage urgency for a patient presentation using an ensemble of AI models.",
            "parameters": {
                "type": "object",
                "properties": {
                    "presentation": {
                        "type": "string",
                        "description": "Brief clinical presentation as a triage nurse would record it.",
                    }
                },
                "required": ["presentation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notify_doctor",
            "description": "Send a push notification to the on-call doctor for an Immediate triage case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "presentation": {"type": "string"},
                    "triage_level": {"type": "string"},
                    "votes": {
                        "type": "object",
                        "description": "Agent votes dict.",
                    },
                },
                "required": ["presentation", "triage_level"],
            },
        },
    },
]

SYSTEM_MSG = """You are an autonomous clinical triage coordinator.
When given a patient presentation:
1. Always call triage_patient to get an urgency classification.
2. If the result is Immediate, call notify_doctor.
3. Return a clear triage decision with brief clinical reasoning."""


class AutonomousAgent(BaseAgent):
    """
    GPT-4.1-mini with tool calling orchestrates the full triage pipeline:
    classify → notify if Immediate → return structured decision.
    """

    color = BaseAgent.YELLOW

    def __init__(self, vector_db_path: str = "clinical_vector_db"):
        self.client = OpenAI()
        self.ensemble = EnsembleAgent(vector_db_path)
        self.messenger = MessengerAgent()
        self.log("AutonomousAgent ready.")

    def _triage_patient(self, presentation: str) -> dict:
        decision, votes = self.ensemble.classify(presentation)
        return {"triage_level": decision, "votes": votes}

    def _notify_doctor(self, presentation: str, triage_level: str, votes: dict) -> dict:
        sent = self.messenger.notify(presentation, triage_level, votes)
        return {"notified": sent}

    def run(self, presentation: str) -> dict:
        self.log(f"Autonomous triage for: {presentation[:60]}...")
        messages = [
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": f"Triage this patient: {presentation}"},
        ]

        while True:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg)
                for call in msg.tool_calls:
                    args = json.loads(call.function.arguments)
                    if call.function.name == "triage_patient":
                        result = self._triage_patient(args["presentation"])
                    elif call.function.name == "notify_doctor":
                        result = self._notify_doctor(
                            args["presentation"], args["triage_level"], args.get("votes", {})
                        )
                    else:
                        result = {"error": "Unknown tool"}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result),
                    })
            else:
                # Final response — LLM is done calling tools
                self.log("Autonomous agent complete.")
                # Return the triage result from the last tool call
                for m in reversed(messages):
                    if isinstance(m, dict) and m.get("role") == "tool":
                        tool_result = json.loads(m["content"])
                        if "triage_level" in tool_result:
                            return {
                                "triage_level": tool_result["triage_level"],
                                "votes": tool_result["votes"],
                                "reasoning": msg.content,
                            }
                return {"triage_level": "Unknown", "reasoning": msg.content}
