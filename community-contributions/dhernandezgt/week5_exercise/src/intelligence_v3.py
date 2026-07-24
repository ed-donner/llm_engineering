from typing import Literal, Protocol
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import os
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv
import ollama

# Loads variables from a .env file at the repo root into the process
# environment (GOOGLE_API_KEY, OPENAI_API_KEY, OLLAMA_HOST, ...). This runs
# once at import time, so it works the same whether intelligence_v3 is
# imported from a Jupyter kernel, a plain script, or another module.
load_dotenv()

##--- 1. Schema (Message Models) ---##

Role = Literal[
    "system",
    "user",
    "assistant",
    "tool",
]

class Message(BaseModel):
    role: Role
    content: str = Field(min_length=1)


##--- 2. Conversation class (single definition, with helpers) ---##

class Conversation(BaseModel):
    messages: list[Message] = Field(default_factory=list)

    def add(self, message: Message):
        self.messages.append(message)

    def system(self, text: str):
        self.add(system(text))

    def user(self, text: str):
        self.add(user(text))

    def assistant(self, text: str):
        self.add(assistant(text))


class GenerationRequest(BaseModel):
    model: str
    temperature: float = 0.2
    max_tokens: int | None = None
    conversation: Conversation


class GenerationResponse(BaseModel):
    text: str
    model: str
    finish_reason: str | None = None
    usage: dict | None = None


##--- 2.5 RAG support (retrieval-augmented generation) ---##

class RetrievedChunk(BaseModel):
    """A single piece of context pulled back from a vectorstore."""
    content: str
    source: str = "unknown"
    score: float | None = None


class Retriever(Protocol):
    """
    Anything with this shape can be plugged in — a Chroma wrapper,
    a BM25 keyword search, a hybrid retriever, a mock for tests, etc.
    Intelligence doesn't care about the storage/search implementation.
    """
    def retrieve(self, query: str, k: int) -> list[RetrievedChunk]:
        ...


class ChromaRetriever:
    """Wraps a langchain_chroma.Chroma vectorstore to satisfy the Retriever protocol."""

    def __init__(self, vectorstore, default_k: int = 4):
        self.vectorstore = vectorstore
        self.default_k = default_k

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        results = self.vectorstore.similarity_search_with_score(query, k=k or self.default_k)
        return [
            RetrievedChunk(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                score=score,
            )
            for doc, score in results
        ]


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Turns retrieved chunks into a numbered, source-labeled block for the prompt."""
    blocks = [
        f"[{i}] (source: {c.source})\n{c.content}"
        for i, c in enumerate(chunks, start=1)
    ]
    return "\n\n".join(blocks)


RAG_PROMPT_TEMPLATE = """Answer the question using ONLY the context below.
If the context doesn't contain enough information to answer, say so plainly \
instead of guessing. Cite sources by their [number] where relevant.

Context:
{context}

Question: {question}"""


##--- 3. Helper constructors ---##

def system(content: str) -> Message:
    return Message(role="system", content=content)


def user(content: str) -> Message:
    return Message(role="user", content=content)


def assistant(content: str) -> Message:
    return Message(role="assistant", content=content)


def tool(content: str) -> Message:
    return Message(role="tool", content=content)


##--- 4. Provider interface ---##

class LLMProvider(ABC):

    @abstractmethod
    def generate(self, messages: list[Message]) -> str:
        ...


# 4.1 OpenAI

class OpenAIProvider(LLMProvider):

    def __init__(self, model: str):
        self.client = OpenAI()
        self.model = model

    def generate(self, messages: list[Message]) -> str:

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": m.role,
                    "content": m.content
                }
                for m in messages
            ]
        )

        return response.output_text


# 4.2 Gemma / Gemini

class GemmaProvider(LLMProvider):

    def __init__(self, model: str):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.model = model

    def generate(self, messages: list[Message]) -> str:
        # Gemini only knows "user" and "model" turn roles.
        # System messages don't go in `contents` — they go in system_instruction.
        role_map = {"user": "user", "assistant": "model"}

        system_texts = [m.content for m in messages if m.role == "system"]
        turn_messages = [m for m in messages if m.role in role_map]

        contents = [
            {
                "role": role_map[m.role],
                "parts": [{"text": m.content}]
            }
            for m in turn_messages
        ]

        config = None
        if system_texts:
            config = types.GenerateContentConfig(
                system_instruction="\n".join(system_texts)
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        return response.text


# 4.3 Ollama (local models)

class OllamaProvider(LLMProvider):

    def __init__(self, model: str, host: str | None = None):
        # host defaults to http://localhost:11434 if not provided
        self.client = ollama.Client(host=host or os.getenv("OLLAMA_HOST"))
        self.model = model

    def generate(self, messages: list[Message]) -> str:
        # Ollama's chat API speaks the same role vocabulary you already use
        # (system / user / assistant / tool) — no remapping needed.
        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": m.role,
                    "content": m.content
                }
                for m in messages
            ]
        )

        return response["message"]["content"]


##--- 5. Provider factory (matches roadmap.md fan-out) ---##

def create_provider(model: str) -> LLMProvider:
    """
    Picks the right LLMProvider based on the model name.
    """
    if model.startswith("gpt") or model.startswith("o1") or model.startswith("o3"):
        return OpenAIProvider(model)
    elif model.startswith("gemma") or model.startswith("gemini"):
        return GemmaProvider(model)
    elif model.startswith("llama") or model.startswith("mistral") or model.startswith("qwen") or model.startswith("phi"):
        return OllamaProvider(model)
    raise ValueError(f"No provider registered for model: {model}")


##--- 6. Intelligence class ---##

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."


class Intelligence:

    def __init__(
        self,
        provider: LLMProvider,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        retriever: Retriever | None = None,
        default_k: int = 4,
    ):
        self.provider = provider
        self.system_prompt = system_prompt
        self.retriever = retriever      # default retriever, optional
        self.default_k = default_k

    def ask(
        self,
        prompt: str,
        conversation: Conversation | None = None,
        retriever: Retriever | None = None,
        k: int | None = None,
        use_rag: bool = True,
    ) -> str:
        """
        Ask a question using an existing Conversation if one is given,
        otherwise start a fresh one with the default system prompt.
        Mutates `conversation` in place so the caller keeps full history.

        If a retriever is available (passed here, or set on __init__) and
        use_rag=True, relevant chunks are fetched and injected into the
        prompt sent to the model — but the *stored* conversation only ever
        keeps the clean original question and answer, not the raw context.
        This keeps multi-turn history from ballooning with repeated chunks.
        """
        if conversation is None:
            conversation = Conversation()
            conversation.system(self.system_prompt)

        active_retriever = retriever or self.retriever
        final_prompt = prompt

        if use_rag and active_retriever is not None:
            chunks = active_retriever.retrieve(prompt, k or self.default_k)
            if chunks:
                context_block = format_context(chunks)
                final_prompt = RAG_PROMPT_TEMPLATE.format(
                    context=context_block, question=prompt
                )

        # Build the message list sent to the provider without mutating
        # `conversation` yet — so history stores the clean question only.
        outgoing_messages = conversation.messages + [user(final_prompt)]
        response_text = self.provider.generate(outgoing_messages)

        conversation.user(prompt)
        conversation.assistant(response_text)

        return response_text


##--- Usage ---##

if __name__ == "__main__":
    # --- Plain chat (unchanged) ---
    prompt = "hi, there how explained blue to somebody is not able to see"

    conversacion = Conversation()
    conversacion.system("You are a kind person but not talkative")

    provider = create_provider("gpt-5.4-nano")
    llm = Intelligence(provider)

    response = llm.ask(prompt, conversation=conversacion)
    print(response)

    follow_up = llm.ask("Can you give a one-sentence analogy instead?", conversation=conversacion)
    print(follow_up)

    # --- RAG chat, using the Chroma collection built earlier ---
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings

    CHROMA_PATH = "chroma_db"
    COLLECTION_NAME = "gemma_local"

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=OllamaEmbeddings(model="nomic-embed-text"),
        persist_directory=CHROMA_PATH,
    )
    retriever = ChromaRetriever(vectorstore, default_k=4)

    rag_provider = create_provider("gemma3:12b")
    rag_llm = Intelligence(
        rag_provider,
        system_prompt="Answer questions using only the provided context.",
        retriever=retriever,
    )

    rag_conversation = Conversation()
    rag_conversation.system(rag_llm.system_prompt)

    answer = rag_llm.ask(
        "What does the source material say about termination clauses?",
        conversation=rag_conversation,
    )
    print(answer)

    # Follow-up: retrieval runs again on this new question, but the
    # conversation history stays clean (no duplicated context blocks)
    follow_up_rag = rag_llm.ask(
        "And what about the notice period?",
        conversation=rag_conversation,
    )
    print(follow_up_rag)
