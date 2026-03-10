# English Accent & Conversation Tutor

English Accent & Conversation Tutor is an **English pronunciation and conversation learning system** similar to **Elsa Speak or Speak AI**.

The system combines **speech recognition, phoneme analysis, accent similarity scoring, reinforcement learning curriculum, and RAG-based lesson retrieval** to provide personalized English learning in an agentic architecture.

- This architecture implements a lightweight streaming RAG pipeline where documents are sampled dynamically, embedded with OpenAI embeddings (text-embedding-3-small), indexed with FAISS, and searched for similarity.

- The LessonAgent uses `gpt-4.1-mini` to create an English pronunciation exercise for the difficulty level and category. 

- The GrammarAgent uses `groq/openai/gpt-oss-20b` to evaluate the user's grammar and provide recommendations

---

# Features

## Accent Similarity Scoring

Uses **phoneme analysis** to Highlights phoneme mistakes and generate learning tips.
Accent similarity scoring using Wav2Vec2 embeddings is achieved by Comparing user's pronunciation with reference pronunciation to estimate accent similarity.  The reference pronunciation is a pretrained model `facebook/wav2vec2-base` accessed through Wav2Vec2Processor.


Outputs an **accent similarity score (0–100)**.

---

## Phoneme-Level Pronunciation Feedback

The system detects phoneme errors and provides corrective guidance.

Example:

```
Expected: /θ/
Spoken: /t/

Tip:
Place tongue between teeth to pronounce "th".
```

---

## Pronunciation Heatmap

Words are highlighted based on pronunciation accuracy.

---

## Mouth Articulation Guidance

The system shows how to position the tongue and mouth for difficult phonemes.

Example:

```
TH sound

Place tongue between teeth
Blow air gently
```

---

## Reinforcement Learning Curriculum

Difficulty automatically adjusts based on performance.

Levels:

- Beginner
- Intermediate
- Advanced
- Native

---

## Progress Tracking

The system tracks:

- completed exercises
- average pronunciation score
- average accent score

for each level.

---

## Conversation Practice

Real-world speaking scenarios:
- Accent Practice
- Tech Workplace
- CEO / board discussions
- Customer interactions
- Sales presentations
- Conversation
- Business Communication
---

## RAG Lesson Retrieval

Exercises are retrieved from curated English datasets:

- LibriSpeech
- DailyDialog
- Books

---

# Architecture

``` 
Exercise Generation using RAG
     ↓
User Speech
     ↓
Whisper Speech Recognition
     ↓
Phoneme Alignment
     ↓
Accent Similarity Scoring
     ↓
Grammar Evaluation
     ↓
RL Curriculum Optimization
     ↓
Feedback + Next Lesson
     ↓
Track Progress
     
```

---

# Tech Stack

### Tools & AI Models

- Whisper
- Transformers
- Wav2Vec2M
- GPT OSS 20B
- GPT 4.1 mini 

### NLP

- SentenceTransformers
- FAISS
- Phonemizer

### Backend

- Python
- Gradio UI
- HuggingFace datasets
- Sqlite3

---

# Installation

## 1. Clone repository

```
git clone  https://github.com/nsikanikpoh/llm_engineering
cd week8/community_contributions/english_learning_tutor_ns_sly
```

---

## 2. Create virtual environment

```
python -m venv venv
source venv/bin/activate
```

---

## 4. Install system dependencies

### Ubuntu

```
sudo apt install ffmpeg espeak-ng
```

### Mac

```
brew install ffmpeg espeak
```

---

## 5. Set OpenAI API key

```
export OPENAI_API_KEY=your_api_key
```

---

## 6. Build dataset vector store

```
python rag/dataset_ingestion.py
```

---

## 7. Run the application

```
python app/main.py
```

Open browser:

```
http://localhost:7860
```

---

# Example Output

```
Sentence:
The quick brown fox

Pronunciation Score:
82 / 100

Accent Similarity:
74 %

Heatmap:
🔴 the 🟢 quick 🟢 brown 🟢 fox

Tip:
Place tongue between teeth for TH sound.

Recommended Level:
Intermediate
```

---

# Future Enhancements

- real-time phoneme heatmaps
- AI mouth animation visualization
- multiplayer speaking practice
- mobile app version
- WebRTC live conversation

---

# License

MIT License