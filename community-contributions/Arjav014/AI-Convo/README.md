# AI-Convo (3-Way AI Conversation)

An interactive, multi-agent conversational simulation featuring three distinct AI models, each playing a character with a unique personality. The models converse in turns while referencing the complete history of the chat.

## Personas

1. **Alex** (Angry and Frustrated): Impatient, easily annoyed, uses all-caps and passive-aggressive sighs.
2. **Blake** (Calm and Shy): Soft-spoken, quiet, uses hesitation markers (`um...`, `uh...`), and avoids conflict.
3. **Charlie** (Funny and Talkative): High-energy, joke-cracking, uses puns and pop-culture references.

## Tech Stack & Models

*   **Runtime:** Jupyter Notebook (`main.ipynb`)
*   **API Client:** `openai` Python SDK (configured for Groq API endpoint)
*   **Models Configured:**
    *   Alex: `openai/gpt-oss-120b`
    *   Blake: `llama-3.3-70b-versatile`
    *   Charlie: `groq/compound-mini`

## Setup & Execution

1.  **Clone / Navigate** to the project directory:
    ```bash
    cd community-contributions/Arjav014/AI-Convo
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**:
    Create a `.env` file in this directory and populate your API keys:
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    ```

4.  **Run the Notebook**:
    Open [main.ipynb](main.ipynb) in VS Code or Jupyter and execute the cells sequentially to watch the 3-way conversation unfold in markdown display format.
