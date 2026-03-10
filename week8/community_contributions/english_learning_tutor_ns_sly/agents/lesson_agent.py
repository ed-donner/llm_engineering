from agents.agent import Agent
from rag.streaming_rag import StreamingRAG
from openai import OpenAI


class LessonAgent(Agent):

    MODEL = "gpt-4.1-mini"

    def __init__(self):

        self.name = "LessonAgent"
        self.color = Agent.BLUE

        self.rag = StreamingRAG()
        self.client = OpenAI()

        self.log("LessonAgent initialized")

    def select_dataset(self, category):

        mapping = {
            "Accent Practice": "librispeech",
            "Conversation": "daily_dialog",
            "Business Communication": "books",
            "Tech Workplace": "books",
            "CEO Communication": "books",
            "Sales": "books"
        }

        return mapping.get(category, "tatoeba")

    def retrieve(self, level, category):

        dataset = self.select_dataset(category)

        query = f"{level} English pronunciation practice"

        examples = self.rag.retrieve(query, dataset)

        prompt = f"""
        Create an English pronunciation exercise.

        Level: {level}
        Category: {category}

        Use these example sentences as inspiration:
        {examples}

        Produce ONE sentence suitable for speaking practice only.
        Do not include any other text or comments.
        """

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content.strip()