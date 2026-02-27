# ⚡ AI Interview Simulator

A multi-agent AI-powered interview simulator built with OpenAI and Gradio. Practice technical and behavioral interviews with real-time evaluation, adaptive difficulty, and personalized coaching — all in a sleek dark-mode UI.

---

## 🧠 Architecture — Three-Agent System

| Agent | Role |
|---|---|
| 🤖 **Interviewer** | Asks one question at a time and adapts difficulty based on your score |
| 📋 **Evaluator** | Scores every answer on clarity, technical depth, and overall quality (0–5) |
| 💡 **Coach** | Delivers what went well, what to improve, and a model answer after each response |

Each agent runs as an independent LLM call with its own system prompt, enabling genuine multi-agent coordination within a single conversation loop.

---

## 🚀 Features

- **Adaptive difficulty** — scores ≥ 4 push harder questions; scores ≤ 1 simplify the next one
- **Structured evaluation** — JSON-based scoring rubric returned by the Evaluator agent
- **Live coaching** — the Coach agent generates a model answer after every question
- **Role presets** — Backend, Frontend, Full-Stack, AI/ML, Data Science, DevOps, System Design, PM, or any custom role
- **Configurable session** — choose 3–10 questions per session
- **Final Score Card** — session summary with averaged scores and a performance verdict
- **Clean terminal-style UI** — dark theme with monospace chat, built with Gradio Blocks

---

## 📁 Project Structure

```
interview_simulator.py   # Main application — all agents, logic, and UI
requirements.txt         # Python dependencies
.env                     # Your API keys (not committed to git)
README.md                # This file
```

---

## ⚙️ Setup

### 1. Clone or download the project

```bash
git clone <your-repo-url>
cd ai-interview-simulator
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...your-key-here...
```

### 5. Run the app

```bash
python interview_simulator.py
```

The app will open automatically in your browser at `http://localhost:7860`.

---

## 🎮 How to Use

1. **Select a role** from the dropdown (or type a custom one)
2. **Choose a difficulty** — Junior, Mid-level, Senior, or Staff/Principal
3. **Set the number of questions** (3–10)
4. Click **▶ Start Interview**
5. Read the question carefully, type your answer, then click **Submit →**
6. Review your evaluation scores and the coach's model answer
7. Continue until the session ends and your **Score Card** appears

---

## 🏗️ Agent Flow

```
User selects role & difficulty
         │
         ▼
  ┌─────────────────┐
  │  INTERVIEWER    │  ◄─── adjusts difficulty based on last score
  │  asks question  │
  └────────┬────────┘
           │
     user answers
           │
           ▼
  ┌─────────────────┐
  │   EVALUATOR     │  ◄─── returns JSON: clarity, technical, overall scores
  │   scores answer │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │     COACH       │  ◄─── what went well · what to improve · model answer
  │  gives feedback │
  └────────┬────────┘
           │
     repeat until N questions done
           │
           ▼
     📊 Final Score Card
```

---

## 🧪 Example Session

```
Role: AI / ML Engineer    Difficulty: Senior    Questions: 5

Q1: Explain the difference between bagging and boosting.
    → Clarity: 4/5  Technical: 3/5  Overall: 3/5
    → Coach: "You covered the core idea well. Missing: variance vs bias trade-off..."
    → Model Answer: [provided]

Q2 (same difficulty): What is gradient vanishing and how do you address it?
    ...

Q5 (adjusted harder): Design a real-time feature store for a recommendation system.
    ...

📊 Score Card
  Clarity:   3.8 / 5  ████░
  Technical: 3.4 / 5  ███░░
  Overall:   3.6 / 5  ████░
  → "Solid performance. A bit more practice and you'll shine."
```

---

## 🔧 Customization

| What | Where |
|---|---|
| Change the LLM model | `MODEL = "gpt-4.1-mini"` at the top of the file |
| Edit agent behavior | Modify `INTERVIEWER_SYSTEM`, `EVALUATOR_SYSTEM`, or `COACH_SYSTEM` |
| Add more roles | Extend the `choices` list in the `role_input` dropdown |
| Add speech input | Integrate `openai.audio.transcriptions.create()` on the answer field |
| Persist session history | Add a SQLite or JSON export step after the Score Card |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `openai` | GPT model calls for all three agents |
| `gradio` | Web UI with chat interface and Blocks layout |
| `python-dotenv` | Load API keys from `.env` |

---

## 📄 License

MIT — free to use, modify, and share.

---

## 🙌 Credits

Built on the multi-agent pattern inspired by the FlightAI tool-calling architecture.
Designed for AI engineers who want to practise interviews and showcase advanced orchestration skills.
