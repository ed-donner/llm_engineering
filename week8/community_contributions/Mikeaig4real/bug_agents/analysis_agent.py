"""
BugAnalysisAgent — uses RAG (Chroma with built-in embedding) with OpenRouter
frontier models to analyze buggy code snippets.
Inspired by Week 5 Day 5 RAG approach.

Uses the OpenAI SDK pointed at OpenRouter (same pattern as Week 8 ScannerAgent).
"""

import os
import json
from typing import List, Optional
from openai import OpenAI
from chromadb import PersistentClient

from bug_agents.agent import Agent
from bug_agents.models import ScrapedBug, BugAnalysis


class BugAnalysisAgent(Agent):
    """Analyzes buggy code using RAG context from existing dataset + frontier model."""

    name = "Bug Analysis Agent"
    color = Agent.GREEN

    MODEL = "openai/gpt-4o"
    COLLECTION_NAME = "bug_examples"
    RETRIEVAL_K = 3

    SYSTEM_PROMPT = """You are an expert Python code reviewer and bug analyst.
You will be given a Python code snippet that contains bugs.
Your job is to analyze the code snippet and identify all bugs present in it.

For each bug you find, specify:
- The line number where it occurs
- The type of bug (e.g., NameError, SyntaxError, LogicError, IndexError, TypeError, IndentationError)
- A clear description of the bug

Also determine for the snippet:
- A brief description of what the code is trying to do (a short phrase like "calculates the average of a list")
- The difficulty level (easy, medium, or hard)
- Relevant topic tags (e.g., string, array, math, sorting, recursion)"""

    def __init__(self, db_path: str = "bugs_vectorstore"):
        self.log("Bug Analysis Agent is initializing")
        self.db_path = db_path

        # OpenAI SDK pointed at OpenRouter
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            self.log("⚠ WARNING: OPENROUTER_API_KEY not set in environment")
        self.openai = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        # Initialize Chroma (uses built-in default embedding function)
        self.log("Initializing Chroma with built-in embedding...")
        self.chroma = PersistentClient(path=db_path)
        self.collection = self.chroma.get_or_create_collection(self.COLLECTION_NAME)
        self.log(f"Chroma vectorstore ready ({self.collection.count()} entries)")
        self.log("Bug Analysis Agent is ready")

    def build_vectorstore(self, dataset_path: str):
        """
        Ingest existing buggy_dataset_nl.jsonl into Chroma.
        Each entry's buggy_code + description becomes a searchable document.
        """
        self.log(f"Building vectorstore from {dataset_path}...")

        # Clear existing collection
        if self.COLLECTION_NAME in [c.name for c in self.chroma.list_collections()]:
            self.chroma.delete_collection(self.COLLECTION_NAME)
        self.collection = self.chroma.get_or_create_collection(self.COLLECTION_NAME)

        entries = []
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

        if not entries:
            self.log("⚠ No entries found in dataset")
            return

        # Build documents: combine description + buggy_code for embedding
        documents = []
        metadatas = []
        ids = []
        for entry in entries:
            doc_text = f"Description: {entry.get('description', '')}\n\nCode:\n{entry.get('buggy_code', '')}"
            documents.append(doc_text)
            metadatas.append(
                {
                    "level": entry.get("level", "unknown"),
                    "num_bugs": entry.get("num_bugs", 0),
                    "bug_types": json.dumps(entry.get("bug_types", [])),
                    "bugs_detail": json.dumps(entry.get("bugs_detail", [])),
                    "description": entry.get("description", ""),
                }
            )
            ids.append(str(entry.get("id", len(ids))))

        # Store (Chroma handles embedding internally)
        self.log(f"Adding {len(documents)} entries to vectorstore...")
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        self.log(f"Vectorstore built with {self.collection.count()} entries")

    def _query_similar(self, code: str) -> List[dict]:
        """Query Chroma for similar bugs from the existing dataset."""
        if self.collection.count() == 0:
            return []

        query_text = f"Code:\n{code}"
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(self.RETRIEVAL_K, self.collection.count()),
        )

        similar = []
        if results and results["documents"] and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                similar.append(
                    {
                        "document": doc,
                        "level": meta.get("level", ""),
                        "num_bugs": meta.get("num_bugs", 0),
                        "bug_types": meta.get("bug_types", "[]"),
                        "bugs_detail": meta.get("bugs_detail", "[]"),
                    }
                )
        return similar

    def _build_rag_prompt(self, code: str) -> str:
        """Build a batch prompt with RAG context."""
        prompt = ""
        similar = self._query_similar(code)

        if similar:
            prompt += "Here are some similar buggy code examples from our knowledge base for reference on how to format your analysis:\n\n"
            for i, s in enumerate(similar[:2], 1):
                prompt += f"--- Reference Example {i} ---\n"
                prompt += f"Level: {s['level']}\n"
                prompt += f"Bug types: {s['bug_types']}\n"
                prompt += f"Details: {s['bugs_detail']}\n"
                prompt += f"{s['document']}\n\n"

        prompt += "Now analyze the following NEW code snippet and identify ALL bugs in it:\n\n"
        prompt += f"```python\n{code}\n```\n\n"

        return prompt

    def analyze(self, bug: ScrapedBug) -> Optional[BugAnalysis]:
        """
        Analyze a single scraped bug.
        Uses OpenAI SDK with structured outputs (response_format -> BugAnalysis).
        """
        self.log(f"Analyzing bug: {bug.title[:50]}...")

        user_prompt = self._build_rag_prompt(bug.code)

        self.log(f"  Calling {self.MODEL} for analysis...")
        try:
            result = self.openai.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=BugAnalysis,
            )
            analysis = result.choices[0].message.parsed

            if analysis:
                self.log("  ✓ Successfully analyzed bug")
                return analysis
            else:
                self.log("  ✗ Model returned empty parsed result")
                return None

        except Exception as e:
            self.log(f"  ✗ Analysis failed: {e}")
            # Fallback for the batch
            return self._analyze_fallback(bug, user_prompt)

    def _analyze_fallback(
        self, bug: ScrapedBug, user_prompt: str
    ) -> Optional[BugAnalysis]:
        """Fallback analysis without structured output parsing."""
        try:
            self.log("  Trying fallback analysis (unstructured)...")
            result = self.openai.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                        + "\nRespond with a JSON object matching the BugAnalysis schema.",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            text = result.choices[0].message.content.strip()

            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            if text.startswith("json"):
                text = text[4:].strip()

            data = json.loads(text)

            # The model is supposed to return a single BugAnalysis object
            # Provide an empty list for missing details
            if "bugs_detail" not in data:
                data["bugs_detail"] = []

            analysis = BugAnalysis(**data)

            self.log("  ✓ Fallback success")
            return analysis

        except Exception as e:
            self.log(f"  ✗ Fallback also failed: {e}")
            return None
