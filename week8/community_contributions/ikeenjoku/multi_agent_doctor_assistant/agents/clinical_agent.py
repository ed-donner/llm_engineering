"""
Clinical Knowledge Agent - Answers general medical questions
"""

from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from .base_agent import BaseAgent


class ClinicalAgent(BaseAgent):
    """Agent that answers general clinical medical questions"""

    def __init__(self, vectorstore, llm):
        """
        Initialize clinical agent

        Args:
            vectorstore: Chroma vector database
            llm: Language model for generation
        """
        super().__init__(vectorstore, llm)

    def process(self, query: str, history: list = None, **kwargs) -> dict:
        """
        Answer general medical questions using clinical knowledge

        Args:
            query: Medical question
            history: Conversation history
            **kwargs: Additional arguments

        Returns:
            dict with keys: answer, sources
        """
        if history is None:
            history = []

        # Combine history for better retrieval
        combined = self._combined_question(query, history)

        # Retrieve relevant documents (limit to 5 for speed)
        docs = self.vectorstore.similarity_search(combined, k=5)

        # Truncate docs for performance
        for doc in docs:
            doc.page_content = doc.page_content[:1000]

        # Build context
        context = "\n\n".join(doc.page_content for doc in docs)

        # Simple clinical prompt
        system_prompt = f"""You are a clinical medical assistant.

Use the following medical knowledge to answer the question:

{context}

Guidelines:
- Provide clear, accurate medical information
- Cite the context when possible
- If the context doesn't contain the answer, say so
- Always include medical disclaimers"""

        # Build messages
        messages = [SystemMessage(content=system_prompt)]

        # Only keep last 3 messages from history for performance
        if history:
            messages.extend(convert_to_messages(history[-3:]))

        messages.append(HumanMessage(content=query))

        # Generate response
        response = self.llm.invoke(messages)

        return {
            "answer": response.content,
            "sources": docs
        }

    def _combined_question(self, question: str, history: list) -> str:
        """Combine prior conversation with current question"""
        if not history:
            return question

        # Only use last 2 user messages
        prior = "\n".join(
            m["content"] for m in history[-2:]
            if m.get("role") == "user"
        )
        return prior + "\n" + question if prior else question
