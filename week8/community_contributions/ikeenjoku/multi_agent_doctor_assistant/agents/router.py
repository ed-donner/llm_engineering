"""
Simple Query Router - Routes to 1 of 3 agents
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class QueryRouter:
    """Routes queries to appropriate agent: clinical, drug_info, or interaction"""

    VALID_AGENTS = ["clinical", "drug_info", "interaction"]

    def __init__(self, openai_api_key: str):
        """Initialize router with OpenAI LLM"""
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o-mini",
            temperature=0
        )

    def route(self, query: str) -> str:
        """
        Route query to one of 3 agents

        Returns:
            "clinical" - general medical questions
            "drug_info" - questions about specific medications
            "interaction" - questions about drug interactions
        """

        system_prompt = """You are a medical query classifier.

Classify the user's medical question into ONE of these categories:

1. "clinical" - General medical questions about:
   - Diseases, conditions, symptoms
   - Diagnoses and treatments
   - Medical procedures
   - General health information
   Examples: "What causes diabetes?", "What are symptoms of heart failure?"

2. "drug_info" - Questions about specific medications:
   - What a drug is used for
   - Side effects of a medication
   - Drug composition
   - Single drug inquiries
   Examples: "What is Augmentin used for?", "Side effects of aspirin"

3. "interaction" - Questions about drug interactions:
   - Can I take drug X with drug Y?
   - Drug combination safety
   - Multiple drugs mentioned together
   Examples: "Can I take aspirin with warfarin?", "Is it safe to combine..."

IMPORTANT:
- Answer with ONLY the category name: clinical, drug_info, or interaction
- No explanations, just the category
- Default to "clinical" if unclear"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        try:
            response = self.llm.invoke(messages)
            agent_type = response.content.strip().lower()

            # Validate response
            if agent_type not in self.VALID_AGENTS:
                return "clinical"  # Default fallback

            return agent_type

        except Exception as e:
            print(f"Router error: {e}")
            return "clinical"


# Test function
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv(override=True)
    router = QueryRouter(os.getenv("OPENAI_API_KEY"))

    test_queries = [
        "What causes diabetes?",
        "What is Augmentin 625 used for?",
        "Can I take aspirin with warfarin?",
        "What are symptoms of heart failure?",
        "Side effects of metformin",
        "Is it safe to take ibuprofen and aspirin together?"
    ]

    print("Testing Router:")
    print("=" * 60)
    for query in test_queries:
        agent = router.route(query)
        print(f"Query: {query}")
        print(f"Agent: {agent}\n")
