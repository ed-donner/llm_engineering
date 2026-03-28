# LinkedIn Post Draft: Open Source AI Tutor

*Note: You can use this draft as-is or tweak it based on my follow-up questions below.*

---

🚀 **We talk a lot about "Agentic AI," but how many of us actually understand the foundational plumbing that makes it work?** 

Most tutorials focus on chaining massive pre-built libraries together. But when things break—or when you need custom behavior—relying purely on abstractions leaves you stuck.

To help bridge this gap, I’ve open-sourced a new project: **A local, terminal-based AI Tutor**. 🎓

Yes, at its core, it’s a chat application. But the real value lies under the hood. I built this to demonstrate exactly what most content *fails* to cover when explaining Agentic solutions:

**1️⃣ Context Injection done right:** 
How do you dynamically load local codebase files or inline text into an LLM's context window without drowning it? This app shows you exactly how context state is managed and fed to the model turn-by-turn.

**2️⃣ The anatomy of an Agentic call:**
It’s not magic—it's structured prompting. Look at the backend code to see how System prompts, conversational history arrays, and RAG context blocks are concatenated into a single, cohesive payload to invoke Local LLMs (via Ollama). 

**3️⃣ Non-blocking UI & Asynchronous state:**
A crucial lesson in agentic workflows is yielding control. This app demonstrates how to offload heavy LLM inference to background worker threads, keeping the TUI (Textual) fully responsive while streaming or generating responses.

If you’re a learner trying to move past the "Hello World" of AI APIs, or a builder who wants to see the raw moving parts of a context-aware AI loop, this repo is for you. 

Dive into the code, rip it apart, and learn how the foundational pieces of LLM tooling actually fit together. 

🔗 **Link to the Repo:** [Insert GitHub Link Here]
💡 **Tech Stack:** Python, Textual (TUI), Ollama (Local LLMs)

Let me know what you think in the comments! Are you building with local LLMs yet? 👇

#AgenticAI #OpenSource #LocalLLM #Python #Ollama #MachineLearning #BuildInPublic #SoftwareEngineering #AI #DeveloperTools
