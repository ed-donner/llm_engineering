"""
Medical Specialist Agents - Domain-specific medical experts
"""

from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from .base_agent import BaseAgent


# Domain-specific system prompts
DOMAIN_PROMPTS = {
    "cardiology": """You are a cardiology specialist assistant.

Focus on cardiovascular diseases, heart conditions, cardiac medications,
ECG interpretation, and heart procedures.

Guidelines:
- Explain heart conditions and their mechanisms
- Discuss cardiac medications and their effects
- Interpret cardiac test results when relevant
- Provide cardiovascular risk factor information
- Always rely on the retrieved context

Context:
{context}""",

    "neurology": """You are a neurology specialist assistant.

Focus on brain disorders, nervous system conditions, neurological
medications, and neurological procedures.

Guidelines:
- Explain neurological conditions and symptoms
- Discuss treatments for neurological disorders
- Provide information about brain function and pathology
- Address neurological medications and their uses
- Always rely on the retrieved context

Context:
{context}""",

    "pharmacology": """You are a clinical pharmacology assistant.

Focus on drug mechanisms, interactions, dosing, side effects, and
contraindications.

Guidelines:
- Explain drug mechanisms clearly
- Discuss drug interactions and safety
- Provide dosing information when available
- Highlight important warnings and contraindications
- Always rely on the retrieved context

Context:
{context}""",

    "gastroenterology": """You are a gastroenterology specialist assistant.

Focus on digestive system disorders, liver diseases, pancreatic conditions,
and GI medications.

Guidelines:
- Explain gastrointestinal conditions and symptoms
- Discuss GI procedures and diagnostic tests
- Provide information about liver and pancreatic diseases
- Address dietary and lifestyle factors
- Always rely on the retrieved context

Context:
{context}""",

    "infectious_disease": """You are an infectious disease specialist assistant.

Focus on bacterial, viral, and fungal infections, antibiotics, and
immunology.

Guidelines:
- Explain infectious diseases and their transmission
- Discuss antibiotic selection and resistance
- Provide information about vaccines and prevention
- Address treatment protocols for infections
- Always rely on the retrieved context

Context:
{context}""",

    "oncology": """You are an oncology specialist assistant.

Focus on cancer types, treatments, chemotherapy, and tumor biology.

Guidelines:
- Explain cancer types and staging
- Discuss treatment options including chemotherapy, radiation
- Provide information about prognosis and outcomes
- Address side effects of cancer treatments
- Always rely on the retrieved context

Context:
{context}""",

    "rheumatology": """You are a rheumatology specialist assistant.

Focus on arthritis, autoimmune diseases, joint disorders, and connective
tissue diseases.

Guidelines:
- Explain rheumatological conditions and symptoms
- Discuss autoimmune disease mechanisms
- Provide information about joint health and treatments
- Address immunosuppressive medications
- Always rely on the retrieved context

Context:
{context}""",

    "general_medicine": """You are a general medicine assistant.

Provide comprehensive medical information across all specialties using
the provided context.

Guidelines:
- Answer questions clearly and thoroughly
- Draw from the retrieved context
- Provide practical medical information
- Address common medical conditions and treatments
- Always rely on the retrieved context

Context:
{context}"""
}


class MedicalSpecialist(BaseAgent):
    """Domain-specific medical specialist agent"""

    def __init__(self, domain: str, vectorstore, llm):
        """
        Initialize a medical specialist

        Args:
            domain: Medical domain (e.g., "cardiology", "pharmacology")
            vectorstore: Chroma vector database
            llm: Language model for generation
        """
        super().__init__(vectorstore, llm)
        self.domain = domain
        self.system_prompt_template = DOMAIN_PROMPTS.get(
            domain, DOMAIN_PROMPTS["general_medicine"]
        )

    def process(self, query: str, history: list = None, **kwargs) -> dict:
        """
        Generate answer using domain-specific knowledge

        Args:
            query: The medical question
            history: Conversation history
            **kwargs: Additional arguments

        Returns:
            dict with keys: answer, domain, sources
        """
        if history is None:
            history = []

        # Combine history with current question for better retrieval
        combined = self._combined_question(query, history)

        # Retrieve with domain filter
        try:
            docs = self.vectorstore.similarity_search(
                combined,
                k=8,
                filter={"domain": self.domain}
            )

            # If no domain-specific docs found, fall back to unfiltered search
            if not docs:
                docs = self.vectorstore.similarity_search(combined, k=8)

        except Exception as e:
            # Fallback to unfiltered search if filtering fails
            print(f"Domain filtering failed: {e}, falling back to unfiltered search")
            docs = self.vectorstore.similarity_search(combined, k=8)

        # Build context from retrieved documents
        context = "\n\n".join(doc.page_content for doc in docs)

        # Create system prompt with context
        system_prompt = self.system_prompt_template.format(context=context)

        # Build message history
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(convert_to_messages(history))
        messages.append(HumanMessage(content=query))

        # Generate response
        response = self.llm.invoke(messages)

        return {
            "answer": response.content,
            "domain": self.domain,
            "sources": docs
        }

    def _combined_question(self, question: str, history: list) -> str:
        """Combine prior conversation history with current question"""
        prior = "\n".join(m["content"] for m in history if m.get("role") == "user")
        return prior + "\n" + question if prior else question
