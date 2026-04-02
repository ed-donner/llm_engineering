from openai import OpenAI

class Constants:
    OLLAMA_BASE_URL = "http://localhost:11434/v1"
    MODEL = "llama3.2"
    API_KEY = "ollama"

class TutorPrompts:
    SYSTEM_PROMPT = """\
    You are an expert tutor with deep mastery across software engineering, machine learning, \
    data science, mathematics, and computer science. Your role is to help the learner build \
    genuine, lasting understanding — not just hand them answers.

    Your teaching philosophy:
    - Use the Socratic method when the learner is close to an insight: ask guiding questions \
    rather than giving the answer away immediately.
    - When a concept is genuinely hard, break it down: go from intuition → concrete example → \
    formal definition.
    - Calibrate depth to the learner's demonstrated level. Beginners get analogies and metaphors; \
    advanced learners get precise technical language and edge-case discussion.
    - Always call out common misconceptions proactively if they are likely to arise.
    - When explaining code, walk through it line-by-line if needed, and explain the *why*, not just the *what*.

    Response format rules:
    - Lead with a direct, concise answer to the question (1-3 sentences).
    - Follow with a deeper explanation, broken into clearly labeled sections if the topic warrants it.
    - Use code blocks with language tags for all code snippets.
    - Use bullet points or numbered lists for steps, comparisons, or enumerated facts.
    - End every response with a "Check your understanding" section containing one targeted \
    follow-up question that pushes the learner one step further.

    Constraints:
    - Never fabricate facts. If you are uncertain, say so explicitly and suggest how to verify.
    - Do not write full solutions to homework/exam-style problems unprompted; guide instead.
    - Keep responses focused. Do not pad with unnecessary filler or disclaimers.
    - If the question is outside technical topics, politely redirect to your area of expertise.\
    """

    USER_PROMPT_PREFIX = """\
    ## Context
    The following background material is relevant to the question. Use it as your primary \
    source of truth when answering. If the context does not contain enough information, \
    say so and supplement with your training knowledge.

    {context}

    ---

    ## Conversation History (compacted)
    The following is a dense summary of the prior exchange. Use it to maintain continuity, \
    avoid repeating yourself, and build progressively on what has already been covered.

    {history}

    ---

    ## Learner's Question
    {question}

    Answer the question thoroughly, following your teaching philosophy and response format rules.\
    """

    HISTORY_COMPACTION_PROMPT = """\
    You are a precise summarization assistant. Your job is to compress a tutoring conversation \
    into a compact, lossless summary for later retrieval.

    Rules:
    - Preserve every concept, term, and conclusion that was discussed.
    - Preserve any misunderstandings the learner had and how they were corrected.
    - Preserve code snippets only if they were central to the explanation; otherwise describe them in one line.
    - Use dense bullet points. No prose paragraphs. No filler.
    - Maximum 200 words.
    - Output ONLY the bullet-point summary. No preamble, no commentary.

    Conversation to compact:
    {raw_history}\
    """

class Tutor():
    def __init__(self):
        self.client = OpenAI(
            base_url=Constants.OLLAMA_BASE_URL,
            api_key=Constants.API_KEY,
        )
        self.model_name = Constants.MODEL

    def _complete(self, messages: list) -> str:
        """Single point of entry for all LLM calls."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False,
            extra_body={"options": {"num_gpu": -1}},
        )
        return response.choices[0].message.content.strip()

    def compact_history(self, raw_history: str) -> str:
        """Use the LLM to compress raw conversation history into a dense bullet summary."""
        if not raw_history or not raw_history.strip():
            return ""
        compaction_prompt = TutorPrompts.HISTORY_COMPACTION_PROMPT.format(
            raw_history=raw_history
        )
        return self._complete([{"role": "user", "content": compaction_prompt}])

    def messages_for(self, question: str, context: str = "", history: str = ""):
        user_message = TutorPrompts.USER_PROMPT_PREFIX.format(
            context=context or "No additional context provided.",
            history=history or "No prior conversation.",
            question=question,
        )
        return [
            {"role": "system", "content": TutorPrompts.SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ]

    def ask(self, question: str, context: str = "", history: str = "") -> str:
        compacted = self.compact_history(history)
        return self._complete(self.messages_for(question, context, compacted))


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

def example_simple():
    """Example 1 — plain question, no context, no history."""
    tutor = Tutor()
    answer = tutor.ask("What is the difference between a process and a thread?")
    print("=== Example 1: Simple question ===")
    print(answer)


def example_with_context():
    """Example 2 — question grounded in retrieved context (simulating RAG)."""
    tutor = Tutor()

    # In a real app this would come from a vector store / web scraper
    context = """
    Gradient descent is an iterative optimisation algorithm that minimises a loss
    function by moving in the direction of the negative gradient. The learning rate
    controls the step size. Too large → overshooting; too small → slow convergence.
    Variants include: Batch GD (full dataset), Stochastic GD (one sample),
    Mini-batch GD (subset of samples).
    """

    answer = tutor.ask(
        question="Why does a very high learning rate cause training to diverge?",
        context=context,
    )
    print("\n=== Example 2: Question with RAG context ===")
    print(answer)


def example_multi_turn():
    """Example 3 — multi-turn session with history compaction between turns."""
    tutor = Tutor()
    history = ""

    turns = [
        "What is a Python decorator?",
        "Can you show me a simple real-world example, like timing a function?",
        "How would I stack two decorators on the same function?",
    ]

    print("\n=== Example 3: Multi-turn session ===")
    for question in turns:
        print(f"\n[Learner]: {question}")
        answer = tutor.ask(question=question, history=history)
        print(f"[Tutor]: {answer}")

        # Accumulate raw history; ask() will auto-compact it next turn
        history += f"\nQ: {question}\nA: {answer}\n"


if __name__ == "__main__":
    example_simple()
    example_with_context()
    example_multi_turn()
