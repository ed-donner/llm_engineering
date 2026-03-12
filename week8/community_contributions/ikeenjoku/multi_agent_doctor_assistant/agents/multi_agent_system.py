"""
Simple Multi-Agent Medical Assistant System
Uses 3 agents: Clinical, Drug Info, and Interaction
"""

from .router import QueryRouter
from .clinical_agent import ClinicalAgent
from .drug_info_agent import DrugInfoAgent
from .interaction_checker import DrugInteractionChecker


class EnhancedMedicalAssistant:
    """Simple multi-agent system with 3 specialized agents"""

    def __init__(self, vectorstore, llm, openai_api_key):
        """
        Initialize the multi-agent system

        Args:
            vectorstore: Chroma vector database
            llm: Language model for generation
            openai_api_key: OpenAI API key for router
        """
        # Initialize router
        self.router = QueryRouter(openai_api_key)

        # Initialize 3 agents
        self.clinical_agent = ClinicalAgent(vectorstore, llm)
        self.drug_info_agent = DrugInfoAgent(vectorstore, llm)
        self.interaction_checker = DrugInteractionChecker(vectorstore, llm)

    def answer(self, question: str, history: list = None) -> dict:
        """
        Route question to appropriate agent and return answer

        Args:
            question: User question
            history: Conversation history

        Returns:
            dict: Contains answer, agent_type, sources, and additional data
        """
        if history is None:
            history = []

        # Step 1: Route to determine agent type
        agent_type = self.router.route(question)

        # Step 2: Handle based on agent type
        if agent_type == "drug_info":
            # Get drug information
            drug_result = self.drug_info_agent.process(question)

            if drug_result.get("found_drugs", False):
                # Also get clinical context for the drug
                clinical_result = self.clinical_agent.process(question, history)

                return {
                    "answer": clinical_result["answer"],
                    "agent_type": "drug_info",
                    "sources": clinical_result["sources"],
                    "drug_info": drug_result
                }
            else:
                # No drugs found, treat as clinical
                agent_type = "clinical"

        if agent_type == "interaction":
            # Check for interactions
            drug_result = self.drug_info_agent.process(question)
            extracted_drugs = [d['medicine_name'] for d in drug_result.get('drugs', [])]

            interaction_result = self.interaction_checker.process(
                question,
                drugs=extracted_drugs
            )

            # Also get clinical answer
            clinical_result = self.clinical_agent.process(question, history)

            return {
                "answer": clinical_result["answer"],
                "agent_type": "interaction",
                "sources": clinical_result["sources"],
                "drug_info": drug_result,
                "interactions": interaction_result
            }

        # Default: Clinical agent
        clinical_result = self.clinical_agent.process(question, history)

        return {
            "answer": clinical_result["answer"],
            "agent_type": "clinical",
            "sources": clinical_result["sources"],
            "drug_info": {"found_drugs": False, "drugs": []},
            "interactions": {"has_interactions": False, "interactions": []}
        }
