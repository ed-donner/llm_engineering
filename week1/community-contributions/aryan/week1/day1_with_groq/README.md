# Day 1 - Groq API Migration & Adaptation
This folder contains a fully adapted and migrated version of the **Day 1: Connection to LLMs** course notebook. 
## Why Groq?
Originally, the course notebook utilized the OpenAI API (which is fully paid) and was later adapted for the Gemini API (which can be unreliable or restricted on the free tier). To solve this, this version completely refactors the notebook to use the **Groq API**, providing an incredibly fast, highly stable, and generous free-tier alternative.
## What is in this folder?
* **`day1.ipynb`**: A fully modified Jupyter notebook optimized for Groq utilizing the **`llama-3.1-8b-instant`** model.
* **`README.md`**: This guide.
## Key Changes & Enhancements
* **Full Groq SDK Integration:** Replaced all legacy API clients with the official `groq` Python client.
* **Comprehensive Revision Notes:** Added detailed `# HOW THIS CODE WORKS:` blocks and clean inline comments to explain exactly how the Groq SDK handles system/user roles and chat completions.
* **PR Ready:** All outputs have been cleared for a clean git diff.