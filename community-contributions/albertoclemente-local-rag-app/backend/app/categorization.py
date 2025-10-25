"""
AI-powered document categorization service.

Uses LLM to analyze document content and automatically assign categories.
Supports multi-language detection, confidence scoring, and category hierarchy.
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache

from app.llm import get_llm_service
from app.diagnostics import get_logger

logger = get_logger(__name__)


# Predefined category hierarchy with descriptions and icons
# Optimized for AI/ML/GenAI content
# Optimized for AI/ML/GenAI content
CATEGORY_HIERARCHY = {
    "Machine Learning & Deep Learning": {
        "icon": "🤖",
        "description": "Machine learning algorithms, deep learning, neural networks, training",
        "subcategories": ["Neural Networks", "Training", "Computer Vision", "NLP", "Reinforcement Learning"],
        "keywords": ["machine learning", "deep learning", "neural network", "training", "model", "backpropagation", "gradient", "optimization", "supervised", "unsupervised", "cnn", "rnn", "lstm", "transformer"]
    },
    "Generative AI & LLMs": {
        "icon": "✨",
        "description": "Large language models, generative AI, prompt engineering, chatbots",
        "subcategories": ["LLMs", "Prompt Engineering", "Text Generation", "Chatbots", "GPT"],
        "keywords": ["llm", "large language model", "generative", "gpt", "chatgpt", "prompt", "generation", "chatbot", "assistant", "completion", "fine-tuning", "rlhf", "instruct", "claude", "gemini"]
    },
    "Computer Vision & Image AI": {
        "icon": "�️",
        "description": "Image recognition, object detection, segmentation, visual AI",
        "subcategories": ["Object Detection", "Image Classification", "Segmentation", "OCR", "GANs"],
        "keywords": ["computer vision", "image", "vision", "detection", "recognition", "segmentation", "ocr", "gan", "diffusion", "stable diffusion", "dalle", "midjourney", "object detection", "yolo"]
    },
    "Natural Language Processing": {
        "icon": "�",
        "description": "NLP techniques, text analysis, sentiment, embeddings, tokenization",
        "subcategories": ["Text Analysis", "Sentiment Analysis", "Embeddings", "Translation", "Named Entity Recognition"],
        "keywords": ["nlp", "natural language", "text", "tokenization", "embedding", "sentiment", "translation", "ner", "named entity", "parsing", "pos tagging", "word2vec", "bert", "t5"]
    },
    "AI Research & Papers": {
        "icon": "📚",
        "description": "Research papers, academic studies, novel AI techniques, experiments",
        "subcategories": ["Academic Papers", "ArXiv", "Experiments", "Novel Architectures", "Benchmarks"],
        "keywords": ["research", "paper", "arxiv", "abstract", "methodology", "experiment", "benchmark", "sota", "state-of-the-art", "novel", "proposed", "evaluation", "dataset", "accuracy", "f1"]
    },
    "MLOps & AI Infrastructure": {
        "icon": "⚙️",
        "description": "Model deployment, MLOps, monitoring, serving, infrastructure",
        "subcategories": ["Deployment", "Monitoring", "Serving", "Pipelines", "Scaling"],
        "keywords": ["mlops", "deployment", "serving", "infrastructure", "pipeline", "kubernetes", "docker", "monitoring", "production", "scaling", "ci/cd", "model registry", "feature store", "a/b testing"]
    },
    "AI Ethics & Safety": {
        "icon": "🛡️",
        "description": "AI ethics, bias, fairness, safety, alignment, responsible AI",
        "subcategories": ["Ethics", "Bias & Fairness", "Safety", "Alignment", "Regulations"],
        "keywords": ["ethics", "bias", "fairness", "safety", "alignment", "responsible", "trustworthy", "explainability", "interpretability", "privacy", "gdpr", "regulation", "governance"]
    },
    "AI Tools & Frameworks": {
        "icon": "�",
        "description": "AI frameworks, libraries, tools, platforms, development",
        "subcategories": ["TensorFlow", "PyTorch", "Hugging Face", "LangChain", "APIs"],
        "keywords": ["pytorch", "tensorflow", "keras", "scikit-learn", "hugging face", "transformers", "langchain", "openai", "api", "sdk", "framework", "library", "tool"]
    },
    "Data & Training": {
        "icon": "�",
        "description": "Datasets, data preparation, labeling, augmentation, training data",
        "subcategories": ["Datasets", "Data Prep", "Labeling", "Augmentation", "Synthetic Data"],
        "keywords": ["dataset", "data", "training data", "labeling", "annotation", "augmentation", "preprocessing", "cleaning", "synthetic", "imagenet", "coco", "glue", "squad"]
    },
    "AI Applications & Use Cases": {
        "icon": "�",
        "description": "Real-world AI applications, case studies, industry solutions",
        "subcategories": ["Healthcare AI", "Finance AI", "Autonomous Systems", "Recommendations", "Search"],
        "keywords": ["application", "use case", "solution", "case study", "industry", "healthcare", "finance", "autonomous", "recommendation", "search", "personalization", "automation"]
    },
    "AI Business & Strategy": {
        "icon": "�",
        "description": "AI strategy, ROI, adoption, market trends, AI companies",
        "subcategories": ["Strategy", "ROI", "Market Analysis", "Adoption", "Startups"],
        "keywords": ["business", "strategy", "roi", "adoption", "market", "trend", "investment", "startup", "enterprise", "ai strategy", "digital transformation", "competitive advantage"]
    },
    "Tutorials & Education": {
        "icon": "🎓",
        "description": "AI tutorials, courses, learning materials, how-to guides",
        "subcategories": ["Tutorials", "Courses", "Guides", "Best Practices", "Examples"],
        "keywords": ["tutorial", "guide", "how-to", "learn", "course", "education", "example", "walkthrough", "getting started", "introduction", "beginner", "advanced", "best practices"]
    },
    "AI Agents & MCP": {
        "icon": "🤝",
        "description": "AI agents, autonomous systems, Model Context Protocol, multi-agent systems, agentic workflows",
        "subcategories": ["Autonomous Agents", "Model Context Protocol", "Multi-Agent Systems", "Agent Frameworks", "Tool Use", "Agentic RAG"],
        "keywords": ["agent", "agents", "mcp", "model context protocol", "autonomous", "agentic", "multi-agent", "agent framework", "tool use", "function calling", "langchain agent", "autogen", "crewai", "agent orchestration", "reasoning", "planning", "reflection", "tool calling", "mcp server", "mcp client", "context protocol"]
    }
}


# Keyword hints to infer subcategories when LLM doesn't return them
# Format: {category: {subcategory: [keywords...]}}
SUBCATEGORY_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "Machine Learning & Deep Learning": {
        "Neural Networks": ["neural", "backprop", "activation", "layer", "weights", "cnn", "rnn", "lstm", "transformer"],
        "Training": ["training", "epoch", "optimizer", "learning rate", "gradient", "loss", "batch", "overfitting", "regularization"],
        "Computer Vision": ["vision", "image", "object detection", "yolo", "rcnn", "mask r-cnn", "segmentation", "imagenet"],
        "NLP": ["nlp", "text", "token", "embedding", "bert", "gpt", "ner", "pos", "translation"],
        "Reinforcement Learning": ["reinforcement", "rl", "policy", "q-learning", "reward", "agent", "environment"]
    },
    "Generative AI & LLMs": {
        "LLMs": ["llm", "large language model", "gpt", "claude", "llama", "mistral", "qwen"],
        "Prompt Engineering": ["prompt", "few-shot", "cot", "chain-of-thought", "system message", "template"],
        "Text Generation": ["generate", "completion", "story", "summarize", "paraphrase"],
        "Chatbots": ["chatbot", "assistant", "chat", "dialog", "conversation"],
        "GPT": ["gpt", "chatgpt", "gpt-4", "gpt-3.5"]
    },
    "Computer Vision & Image AI": {
        "Object Detection": ["yolo", "rcnn", "faster r-cnn", "ssd", "detect", "bounding box"],
        "Image Classification": ["classify", "classification", "imagenet", "top-1", "top-5"],
        "Segmentation": ["segmentation", "mask", "semantic", "instance"],
        "OCR": ["ocr", "text recognition", "tesseract"],
        "GANs": ["gan", "generative adversarial", "stylegan", "diffusion", "stable diffusion", "dalle", "midjourney"]
    },
    "Natural Language Processing": {
        "Text Analysis": ["tokenize", "lemmatize", "parse", "n-gram", "tf-idf"],
        "Sentiment Analysis": ["sentiment", "positive", "negative", "polarity"],
        "Embeddings": ["embedding", "word2vec", "glove", "bert", "vector", "similarity"],
        "Translation": ["translate", "mt", "machine translation", "bleu"],
        "Named Entity Recognition": ["ner", "entity", "person", "organization", "location"]
    },
    "AI Research & Papers": {
        "Academic Papers": ["abstract", "introduction", "related work", "conclusion"],
        "ArXiv": ["arxiv", "preprint"],
        "Experiments": ["experiment", "hyperparameters", "results", "dataset"],
        "Novel Architectures": ["architecture", "novel", "proposed", "method"],
        "Benchmarks": ["sota", "state-of-the-art", "benchmark", "accuracy", "f1", "roc"]
    },
    "MLOps & AI Infrastructure": {
        "Deployment": ["deploy", "deployment", "kubernetes", "docker", "container", "helm"],
        "Monitoring": ["monitor", "prometheus", "grafana", "drift", "latency", "metrics"],
        "Serving": ["serve", "inference", "triton", "torchserve", "fastapi", "rest"],
        "Pipelines": ["pipeline", "airflow", "kubeflow", "mlflow", "dvc", "orchestrate"],
        "Scaling": ["scale", "autoscale", "throughput", "load", "horizontal", "vertical"]
    },
    "AI Ethics & Safety": {
        "Ethics": ["ethic", "responsible", "trustworthy"],
        "Bias & Fairness": ["bias", "fair", "parity", "disparity"],
        "Safety": ["safety", "guardrail", "jailbreak", "harm"],
        "Alignment": ["alignment", "rlhf", "constitutional", "dpo"],
        "Regulations": ["gdpr", "regulation", "policy", "law", "compliance"]
    },
    "AI Tools & Frameworks": {
        "TensorFlow": ["tensorflow", "tf"],
        "PyTorch": ["pytorch", "torch"],
        "Hugging Face": ["hugging face", "transformers", "datasets", "tokenizers"],
        "LangChain": ["langchain", "agent", "chain"],
        "APIs": ["api", "sdk", "endpoint", "key"]
    },
    "Data & Training": {
        "Datasets": ["dataset", "corpus", "imagenet", "coco", "glue", "squad"],
        "Data Prep": ["clean", "preprocess", "normalize", "split"],
        "Labeling": ["label", "annotate", "annotation", "labeling"],
        "Augmentation": ["augment", "augmentation", "flip", "crop", "noise"],
        "Synthetic Data": ["synthetic", "generate data", "data synthesis"]
    },
    "AI Applications & Use Cases": {
        "Healthcare AI": ["health", "medical", "patient", "radiology", "diagnosis"],
        "Finance AI": ["finance", "trading", "risk", "fraud"],
        "Autonomous Systems": ["autonomous", "robot", "driving", "drone"],
        "Recommendations": ["recommend", "recsys", "collaborative filtering"],
        "Search": ["search", "retrieval", "ranking"]
    },
    "AI Business & Strategy": {
        "Strategy": ["strategy", "roadmap", "initiative"],
        "ROI": ["roi", "return", "investment", "cost"],
        "Market Analysis": ["market", "trend", "analysis"],
        "Adoption": ["adoption", "rollout", "change management"],
        "Startups": ["startup", "funding", "valuation"]
    },
    "Tutorials & Education": {
        "Tutorials": ["tutorial", "walkthrough", "step-by-step"],
        "Courses": ["course", "curriculum", "lesson"],
        "Guides": ["guide", "how-to", "introduction", "getting started"],
        "Best Practices": ["best practice", "recommendation", "pitfall"],
        "Examples": ["example", "sample", "demo"]
    },
    "AI Agents & MCP": {
        "Autonomous Agents": ["autonomous agent", "self-directed", "autonomous system", "goal-oriented", "reactive agent"],
        "Model Context Protocol": ["mcp", "model context protocol", "mcp server", "mcp client", "context protocol", "mcp tool"],
        "Multi-Agent Systems": ["multi-agent", "agent collaboration", "agent communication", "agent coordination", "swarm"],
        "Agent Frameworks": ["langchain agent", "autogen", "crewai", "agent framework", "agent library", "agent sdk"],
        "Tool Use": ["tool use", "tool calling", "function calling", "external tool", "api integration", "tool execution"],
        "Agentic RAG": ["agentic rag", "agent retrieval", "rag agent", "retrieval agent", "agentic workflow"]
    }
}


def get_category_list() -> List[str]:
    """Get list of all available categories."""
    return list(CATEGORY_HIERARCHY.keys())


def get_category_icon(category: str) -> str:
    """Get icon for a category."""
    return CATEGORY_HIERARCHY.get(category, {}).get("icon", "📄")


def get_category_info(category: str) -> Dict[str, Any]:
    """Get full information for a category."""
    return CATEGORY_HIERARCHY.get(category, {})


def detect_language(text: str) -> str:
    """
    Detect the primary language of the text.
    Simple heuristic-based detection.
    """
    # Common words in different languages
    language_patterns = {
        "english": ["the", "and", "is", "in", "to", "of", "a", "for", "on", "with"],
        "spanish": ["el", "la", "de", "que", "y", "en", "un", "por", "los", "para"],
        "french": ["le", "de", "un", "être", "et", "à", "il", "avoir", "ne", "dans"],
        "german": ["der", "die", "und", "in", "den", "von", "zu", "das", "mit", "ist"],
        "italian": ["il", "di", "e", "la", "che", "per", "un", "in", "da", "non"],
        "portuguese": ["o", "a", "de", "que", "e", "do", "da", "em", "um", "para"]
    }
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    if not words:
        return "english"  # default
    
    # Count matches for each language
    language_scores = {}
    for lang, patterns in language_patterns.items():
        score = sum(1 for word in words[:200] if word in patterns)
        language_scores[lang] = score
    
    # Return language with highest score
    detected_lang = max(language_scores.items(), key=lambda x: x[1])
    
    # If score is too low, default to English
    if detected_lang[1] < 3:
        return "english"
    
    return detected_lang[0]


def extract_representative_text(
    parsed_content: Dict[str, Any],
    max_tokens: int = 2000
) -> str:
    """
    Extract representative text from parsed document.
    Prioritizes beginning of document for categorization.
    
    Args:
        parsed_content: Parsed document content (from Docling)
        max_tokens: Maximum number of tokens to extract
        
    Returns:
        Representative text sample
    """
    text = ""

    # Prefer rich markdown/plain text fields first
    preferred_fields = [
        "markdown_content",
        "content",
        "plain_text",
        "full_text",
        "text",
        "raw_text",
        "document_text"
    ]
    for field in preferred_fields:
        value = parsed_content.get(field)
        if isinstance(value, str) and value.strip():
            text = value
            break

    if not text:
        # Fallback to chunks if standard text fields are missing
        chunks = parsed_content.get("chunks", [])
        if chunks:
            text = "\n\n".join(chunk.get("text", "") for chunk in chunks[:3])

    if not text:
        # Fallback to joined section contents if available
        sections = parsed_content.get("sections")
        if isinstance(sections, list):
            collected = []
            for section in sections:
                if isinstance(section, dict):
                    section_text = section.get("text") or section.get("content")
                    if isinstance(section_text, str) and section_text.strip():
                        collected.append(section_text.strip())
            text = "\n\n".join(collected)
    
    # Rough token estimation (1 token ≈ 4 characters)
    char_limit = max_tokens * 4
    
    if len(text) > char_limit:
        text = text[:char_limit] + "..."
    
    return text


def keyword_based_categorization(text: str) -> Dict[str, float]:
    """
    Fallback categorization using keyword matching.
    Returns category scores based on keyword presence.
    """
    text_lower = text.lower()
    category_scores = {}
    
    for category, info in CATEGORY_HIERARCHY.items():
        keywords = info.get("keywords", [])
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        
        # Normalize score (0-1)
        if keywords:
            category_scores[category] = matches / len(keywords)
        else:
            category_scores[category] = 0.0
    
    return category_scores


async def categorize_with_llm(
    text: str,
    language: str = "english",
    max_categories: int = 3
) -> Tuple[List[str], float, Dict[str, List[str]]]:
    """
    Use LLM to categorize document content.
    
    Args:
        text: Document text to categorize
        language: Detected language
        max_categories: Maximum number of categories to assign
        
    Returns:
        Tuple of (categories list, confidence score)
    """
    llm_service = await get_llm_service()
    
    # Build category list for prompt
    categories_list = "\n".join(
        f"- {cat}: {info['description']} | Subcategories: {', '.join(info.get('subcategories', []))}"
        for cat, info in CATEGORY_HIERARCHY.items()
    )
    
    # Language-aware prompt
    lang_note = f"\nNote: This document appears to be in {language}." if language != "english" else ""
    
    prompt = f"""Analyze the following document excerpt and assign the most relevant categories and subcategories.

Document excerpt:
{text[:1500]}

Available categories:
{categories_list}
{lang_note}

Instructions:
1. Assign {max_categories} most relevant categories (minimum 1, maximum {max_categories})
2. For each selected category, also pick up to 3 relevant subcategories from the allowed list
3. Return ONLY a JSON object in one of these formats:
   A) {{"categories": ["Category 1", "Category 2"], "subcategories": {{"Category 1": ["Sub1", "Sub2"], "Category 2": ["SubA"]}}, "confidence": 0.9}}
   B) {{"categories": [{{"name": "Category 1", "subcategories": ["Sub1", "Sub2"]}}, {{"name": "Category 2", "subcategories": ["SubA"]}}], "confidence": 0.9}}

The confidence should be a number between 0 and 1 indicating how certain you are about the categorization.

Response:"""

    try:
        # Call LLM
        response = await llm_service.generate(prompt, max_tokens=200, temperature=0.3)

        # Parse response - handle GenerationResult object
        if hasattr(response, "text"):
            response_text = response.text.strip()
        elif hasattr(response, "content"):
            response_text = response.content.strip()
        else:
            response_text = str(response).strip()
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())

            subcats_map: Dict[str, List[str]] = {}

            # Format A: categories is list[str]
            if isinstance(result.get("categories"), list) and all(isinstance(c, str) for c in result["categories"]):
                categories = result.get("categories", [])
                # Extract subcategories map if provided
                if isinstance(result.get("subcategories"), dict):
                    for cat, subs in result["subcategories"].items():
                        if isinstance(subs, list):
                            subcats_map[cat] = [s for s in subs if isinstance(s, str)]
            # Format B: categories is list[ {name, subcategories} ]
            elif isinstance(result.get("categories"), list) and any(isinstance(c, dict) for c in result["categories"]):
                categories = []
                for item in result["categories"]:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name") or item.get("category")
                    if isinstance(name, str):
                        categories.append(name)
                        subs = item.get("subcategories") or []
                        if isinstance(subs, list):
                            subcats_map[name] = [s for s in subs if isinstance(s, str)]
            else:
                categories = []

            confidence = float(result.get("confidence", 0.7))

            # Validate categories
            valid_categories = [cat for cat in categories if cat in CATEGORY_HIERARCHY]

            if not valid_categories:
                logger.warning(f"LLM returned invalid categories: {categories}")
                return await fallback_categorization(text)

            # Post-process subcategories: keep only allowed subs
            cleaned_subs: Dict[str, List[str]] = {}
            for cat in valid_categories:
                allowed = set(CATEGORY_HIERARCHY[cat].get("subcategories", []))
                provided = [s for s in subcats_map.get(cat, []) if s in allowed]
                cleaned_subs[cat] = provided[:3]

            # If LLM didn't provide subs for some cats, infer via keywords
            for cat in valid_categories:
                if not cleaned_subs.get(cat):
                    cleaned_subs[cat] = []
            inferred = infer_subcategories(valid_categories, text)
            for cat, subs in inferred.items():
                if not cleaned_subs.get(cat):
                    cleaned_subs[cat] = subs

            return valid_categories[:max_categories], confidence, cleaned_subs
        else:
            logger.warning(f"Could not parse JSON from LLM response: {response_text[:200]}")
            return await fallback_categorization(text)
            
    except Exception as e:
        logger.error(f"Error in LLM categorization: {e}")
        return await fallback_categorization(text)


def select_subcategories_for_category(category: str, text: str, max_subcats: int = 3) -> List[str]:
    """
    Infer likely subcategories for a given category using keyword matches.
    """
    text_lower = text.lower()
    allowed = CATEGORY_HIERARCHY.get(category, {}).get("subcategories", [])
    if not allowed:
        return []

    kw_map = SUBCATEGORY_KEYWORDS.get(category, {})
    scored: List[Tuple[str, int]] = []
    for sub in allowed:
        keywords = kw_map.get(sub, [])
        if not keywords:
            # fallback: match subcategory name tokens
            tokens = re.findall(r"\w+", sub.lower())
            score = sum(1 for t in tokens if t and t in text_lower)
        else:
            score = sum(1 for k in keywords if k in text_lower)
        scored.append((sub, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = [sub for sub, score in scored if score > 0][:max_subcats]
    return top


def infer_subcategories(categories: List[str], text: str) -> Dict[str, List[str]]:
    """Infer subcategories for a list of categories from text."""
    return {cat: select_subcategories_for_category(cat, text) for cat in categories}


async def fallback_categorization(text: str) -> Tuple[List[str], float, Dict[str, List[str]]]:
    """
    Fallback categorization using keyword matching when LLM fails.
    """
    logger.info("Using fallback keyword-based categorization")
    
    scores = keyword_based_categorization(text)
    
    # Get top 2 categories
    sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Filter categories with score > 0
    valid_categories = [(cat, score) for cat, score in sorted_categories if score > 0]
    
    if not valid_categories:
        # If no matches, return General Knowledge
        return ["General Knowledge"], 0.5, {}
    
    # Return top 1-2 categories
    top_categories = [cat for cat, _ in valid_categories[:2]]
    avg_confidence = sum(score for _, score in valid_categories[:2]) / len(valid_categories[:2])
    subs = infer_subcategories(top_categories, text)

    return top_categories, min(avg_confidence, 0.7), subs  # Cap confidence at 0.7 for keyword-based


async def categorize_document(
    parsed_content: Dict[str, Any],
    doc_name: str = "",
    force_recategorize: bool = False
) -> Dict[str, Any]:
    """
    Main categorization function.
    
    Args:
        parsed_content: Parsed document content
        doc_name: Document filename (optional, for logging)
        force_recategorize: Force re-categorization even if already categorized
        
    Returns:
        Dictionary with categorization results:
        {
            "categories": ["Category 1", "Category 2"],
            "confidence": 0.85,
            "language": "english",
            "method": "llm" or "keyword",
            "generated_at": "2025-10-11T10:30:00"
        }
    """
    logger.info(f"Categorizing document: {doc_name}")
    
    # Extract representative text
    text = extract_representative_text(parsed_content)
    
    if not text or len(text.strip()) < 50:
        logger.warning(f"Insufficient text for categorization: {doc_name}")
        generated_at = datetime.utcnow()
        return {
            "categories": ["AI Research & Papers"],
            "confidence": 0.3,
            "language": "unknown",
            "method": "insufficient_content",
            "subcategories": {"AI Research & Papers": ["Academic Papers"]},
            "generated_at": generated_at
        }
    
    # Detect language
    language = detect_language(text)
    logger.info(f"Detected language: {language}")
    
    # Categorize with LLM
    categories, confidence, subcategories = await categorize_with_llm(text, language, max_categories=3)
    
    # Determine method (llm if confidence > 0.7, otherwise keyword)
    method = "llm" if confidence > 0.7 else "keyword"
    
    generated_at = datetime.utcnow()
    result = {
        "categories": categories,
        "confidence": round(confidence, 2),
        "language": language,
        "method": method,
        "subcategories": subcategories,
        "generated_at": generated_at
    }
    
    logger.info(f"Categorization result for {doc_name}: {result}")
    
    return result


def get_category_statistics(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about categories across documents.
    
    Args:
        documents: List of document objects with categories
        
    Returns:
        Statistics dictionary
    """
    stats = {
        "total_documents": len(documents),
        "categorized_documents": 0,
        "category_counts": {},
        "avg_categories_per_doc": 0.0,
        "avg_confidence": 0.0,
        "language_distribution": {},
        "method_distribution": {}
    }
    
    total_categories = 0
    total_confidence = 0.0
    
    for doc in documents:
        categories = doc.get("categories", [])
        
        if categories:
            stats["categorized_documents"] += 1
            total_categories += len(categories)
            
            for category in categories:
                stats["category_counts"][category] = stats["category_counts"].get(category, 0) + 1
        
        # Track confidence
        confidence = doc.get("category_confidence", 0)
        if confidence:
            total_confidence += confidence
        
    # Track language (coerce None/empty to 'unknown')
    lang = doc.get("category_language") or "unknown"
    stats["language_distribution"][str(lang)] = stats["language_distribution"].get(str(lang), 0) + 1
        
    # Track method (coerce None/empty to 'unknown')
    method = doc.get("category_method") or "unknown"
    stats["method_distribution"][str(method)] = stats["method_distribution"].get(str(method), 0) + 1
    
    # Calculate averages
    if stats["categorized_documents"] > 0:
        stats["avg_categories_per_doc"] = round(total_categories / stats["categorized_documents"], 2)
        stats["avg_confidence"] = round(total_confidence / stats["categorized_documents"], 2)
    
    # Sort categories by count
    stats["category_counts"] = dict(
        sorted(stats["category_counts"].items(), key=lambda x: x[1], reverse=True)
    )
    
    return stats


def suggest_similar_categories(category: str, documents: List[Dict[str, Any]]) -> List[str]:
    """
    Suggest categories that often appear together with the given category.
    Useful for smart search and recommendations.
    """
    co_occurrence = {}
    
    for doc in documents:
        categories = doc.get("categories", [])
        
        if category in categories:
            for other_cat in categories:
                if other_cat != category:
                    co_occurrence[other_cat] = co_occurrence.get(other_cat, 0) + 1
    
    # Sort by frequency
    sorted_suggestions = sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)
    
    return [cat for cat, _ in sorted_suggestions[:5]]
