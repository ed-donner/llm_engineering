from .agent import Agent

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


class SummaryAgent(Agent):
    """
    Takes the raw text retrieved by the DataRetrievalAgent and uses the LLM
    to construct a clean, professional summary tailored for a call center agent.
    """
    name = "Summary Agent"
    color = Agent.MAGENTA
    MODEL = "gpt-4o-mini" # You can swap this with another OpenRouter/OpenAI model

    def __init__(self, use_llm: bool = True, client=None):
        self.use_llm = use_llm and _OPENAI_AVAILABLE
        self._client = client
        self.log("Initialized Summary Agent.")

    def summarize(self, raw_data: str) -> str:
        """Synthesize a call center response from raw RAG context."""
        self.log("Synthesizing patient data...")
        
        if "No records found" in raw_data:
            self.log("No data to summarize.")
            return raw_data

        if self.use_llm and self._client:
            prompt = (
                "You are an AI assistant helping a call center agent handling medical inquiries.\n"
                "You are provided with raw data retrieved from the patient database.\n"
                "Task: Construct a brief, strictly factual summary of the patient's demographics, "
                "insurance status, chronic illnesses, recent hospital visits and stays, and claims.\n"
                "Format this clearly with bullet points so the call center agent can read it quickly while on the phone.\n"
                "Do NOT include any information not present in the raw data.\n\n"
                f"--- RAW DATA ---\n{raw_data}\n--- END DATA ---\n"
            )
            
            try:
                response = self._client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful and concise medical call center assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=600,
                )
                content = response.choices[0].message.content or ""
                self.log("Synthesis complete (LLM).")
                return content.strip()
            except Exception as e:
                self.log(f"LLM fallback error: {e}")

        # Fallback Mock summary
        self.log("Synthesis complete (Mock/Fallback).")
        return f"--- System Summary (MOCK MODE) ---\n\n{raw_data}\n\n(Note: LLM not enabled or API disconnected)"
