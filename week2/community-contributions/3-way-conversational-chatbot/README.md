# 3-Way Conversational Chatbot

##  Project Overview
This project demonstrates a **multi-agent conversational system** where three distinct AI models interact:
- **GPT‑4o‑mini** → Eternal optimist, concise and uplifting.
- **GPT‑5‑nano** → Thoughtful philosopher, symbolic and existential.
- **Llama 3.2 (via Ollama)** → Witty skeptic, sarcastic and literal.

Together, they engage in a structured dialogue on cultural topics (e.g., Franz Kafka’s relevance to Gen Z), showcasing **multi‑model orchestration, prompt engineering, and conversational dynamics**.

---

##  Features
- Integration of **OpenAI SDK** and **Ollama local inference server**.
- Custom **system prompts** to enforce distinct personalities.
- Automated **turn-taking conversation loop** between models.
- Demonstrates **API usage, environment setup, and model orchestration**.

---

## 🛠️ Installation & Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/3-way-conversational-chatbot.git
   cd 3-way-conversational-chatbot

2. Install dependencies:
    ```bash
    pip install -r requirements.txt

3. Required packages:
- openai
- ollama
- python-dotenv
- requests
- IPython

4. Set up environment variables:
- Create a .env file with your OpenAI API key:
    ```bash
    OPENAI_API_KEY=sk-xxxxxxx

5. Run Ollama locally:
    ```bash
    ollama serve
    ollama pull llama3.2

---

## Usage
### Run the notebook:
    ```bash
    jupyter notebook 3-way-conversational-chatbot.ipynb
    ```
The notebook will:
- Initialize **API clients**.
- Launch a **round-robin conversation** between GPT‑4o‑mini, GPT‑5‑nano, and Llama 3.2.
- **Display dialogue** outputs in Markdown format.

### Example Output
    ```bash
    GPT4: Absolutely! Kafka’s themes resonate with Gen Z’s search for identity.
    Ollama: Or maybe they just like tweeting about absurdity in 280 characters.
    GPT5: Alienation and bureaucracy are timeless struggles, amplified in digital life.
    ```
## Learning Outcomes
- Hands-on experience with **multi-model orchestration**.
- Practice in **prompt engineering** and **persona design**.
- Exposure to **API integration** and **local model serving**.
- Understanding of **AI/ML conversational dynamics**.

## Future Improvements
- Add evaluation metrics (e.g., coherence, diversity).
- Extend to more than three agents.
- Deploy as a web app with Flask/Streamlit.
- Integrate vector databases for contextual memory.

## Acknowledgments
- OpenAI Python SDK
- Ollama
- Inspiration from discussions on multi-agent systems in AI

