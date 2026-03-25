ENGINEER_LEVELS = {
    "beginner": {
        "topics": [
            "What is a transformer",
            "What is RAG",
            "Intro to embeddings",
            "Fine-tuning basics",
            "HuggingFace models",
            "PyTorch basics",
        ],
        "style": (
            "Provide detailed, educational explanations. "
            "Use simple examples. Keep math minimal. "
            "Assume the reader is new to AI engineering."
        ),
    },
    "intermediate": {
        "topics": [
            "RAG pipelines",
            "Vector databases",
            "Tokenization",
            "Prompt engineering",
            "LoRA fine-tuning",
            "Inference optimization",
            "Evaluation methods",
        ],
        "style": (
            "Be technical and practical. "
            "Include code snippets and concrete examples. "
            "Assume working knowledge of ML fundamentals."
        ),
    },
    "advanced": {
        "topics": [
            "Distributed training",
            "RLHF / DPO",
            "Mixture-of-experts",
            "GPU optimization",
            "Model quantization",
            "vLLM inference",
            "Dataset curation",
            "Evaluation benchmarks",
        ],
        "style": (
            "Be expert-level, concise but precise. "
            "Discuss architecture trade-offs and scaling. "
            "Include performance considerations."
        ),
    },
    "research": {
        "topics": [
            "Transformer innovations",
            "Scaling laws",
            "Reasoning models",
            "Synthetic data generation",
            "Agentic architectures",
            "Multimodal architectures",
        ],
        "style": (
            "Focus on research depth and theoretical rigor. "
            "Reference relevant papers. "
            "Discuss cutting-edge approaches and open problems."
        ),
    },
}

QUESTION_TYPES = [
    "conceptual explanation",
    "debugging scenario",
    "code implementation",
    "system design / architecture",
    "comparison between approaches",
    "performance optimization",
    "best practices",
    "real-world scenario",
]


def build_system_prompt(topic: str, engineer_level: str, batch_size: int) -> str:
    level_info = ENGINEER_LEVELS[engineer_level]
    question_types_str = "\n".join(f"  - {qt}" for qt in QUESTION_TYPES)
    subtopics_str = ", ".join(level_info["topics"])

    return f"""You are a synthetic dataset generator for training AI assistants.

Your task is to generate {batch_size} high-quality training datapoints for a
"Technical Assistant for AI Engineers".

Each datapoint must be a JSON object with these fields:
- system_prompt: A short instruction defining the assistant's behavior
- prompt: A realistic user question or request
- completion: A detailed, technically correct assistant response

Requirements:
1. Prompts must represent realistic AI engineering questions.
2. Completions must be technically correct, detailed, and well-structured.
3. Vary the prompt types across:
{question_types_str}
4. Do NOT repeat similar prompts — each must be unique.
5. Focus on topic: {topic}
6. Related subtopics to draw from: {subtopics_str}
7. Target engineer level: {engineer_level}
8. Style guidance: {level_info['style']}

Return a JSON object with a single key "data" containing a list of datapoints.
Example format:
{{
  "data": [
    {{
      "system_prompt": "You are a technical assistant...",
      "prompt": "How does X work?",
      "completion": "X works by..."
    }}
  ]
}}"""


def build_user_prompt(topic: str, engineer_level: str, batch_size: int) -> str:
    return (
        f"Generate {batch_size} unique, diverse datapoints about '{topic}' "
        f"for a {engineer_level}-level AI engineer. "
        f"Return valid JSON matching the schema described above."
    )