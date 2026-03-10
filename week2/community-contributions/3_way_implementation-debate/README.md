# 3-Way LLM Debate System

## Overview

This implementation creates an automated debate simulation between two Large Language Models (LLMs) - **DeepSeek** and **Sarvam AI** - on the topic: **"Is genetic modification of food or embryos ethical?"**

The debate features three distinct personas:
- **Dr. Rosaline Tah** (Moderator) - Powered by Sarvam AI
- **Felix Nji** (Pro-GM) - Powered by DeepSeek
- **James Fru** (Anti-GM) - Powered by DeepSeek

## Purpose

This implementation demonstrates:
- Multi-agent LLM interaction with distinct personas and viewpoints
- Structured debate flow management with predefined stages
- Integration of multiple LLM providers (DeepSeek and Sarvam AI)
- Context-aware conversation using debate history
- Role-based prompt engineering for consistent character behavior

Unlike simple chatbot interactions, this creates a formal, structured debate with opening statements, rebuttals, Q&A, and closing arguments.

## Features

✅ **Structured Debate Format**: 11-stage debate flow including introduction, opening statements, rebuttals, Q&A, and closing arguments  
✅ **Multi-LLM Integration**: Combines DeepSeek and Sarvam AI with different roles  
✅ **Persona-Based Prompting**: Each participant has a distinct personality and argumentation style  
✅ **Context Awareness**: Maintains conversation history (last 6 exchanges) for coherent responses  
✅ **Formatted Output**: Clean, readable debate transcript with stage separators  
✅ **Bioethics Focus**: Tackles a complex, real-world ethical dilemma

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- API keys for DeepSeek and Sarvam AI

### Dependencies

This project uses the dependencies defined in the root `pyproject.toml`:

```toml
openai>=2.15.0
sarvamai>=0.1.22
rich>=14.3.1
dotenv>=0.9.9
```

### Installation

1. **Install dependencies** (from the project root):
   ```bash
   pip install -e .
   ```
   or with uv:
   ```bash
   uv pip install -e .
   ```

2. **Set up environment variables**:
   Create a `.env` file in the project root with:
   ```env
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   SARVAM_API_KEY=your_sarvam_api_key_here
   ```

   - Get DeepSeek API key from: https://platform.deepseek.com/
   - Get Sarvam API key from: https://www.sarvam.ai/

## Usage

### Running the Debate

Navigate to the directory and run:

```bash
cd week2/3_way_implementation-debate
python llm_debate.py
```

### Expected Output

The script will execute an 11-stage debate and print:
1. Real-time output for each stage as it completes
2. A full transcript at the end with all exchanges

Example output structure:
```
=== Debate Simulation (DeepSeek + Sarvam) ===

--- Introduction / MODERATOR ---
[Dr. Rosaline Tah introduces the debate topic and participants...]
------------------------------------------------------------

--- Opening Pro / FELIX ---
[Felix Nji presents arguments in favor of genetic modification...]
------------------------------------------------------------

...

=== FULL TRANSCRIPT ===
[Complete debate transcript]
```

## Architecture

### Debate Structure

The debate follows a formal 11-stage structure:

1. **Introduction** (Moderator) - Topic and rules introduction
2. **Opening Pro** (Felix) - Pro-GM opening statement
3. **Opening Against** (James) - Anti-GM opening statement
4. **Rebuttal 1 Against** (James) - Rebuttal to Pro's opening
5. **Rebuttal 1 Pro** (Felix) - Rebuttal to Against's opening
6. **Q&A Moderator Q1** (Moderator) - Poses question about benefits vs. risks
7. **Q&A Pro Response** (Felix) - Responds to moderator's question
8. **Q&A Against Response** (James) - Responds to moderator's question
9. **Closing Pro** (Felix) - Final pro-GM argument
10. **Closing Against** (James) - Final anti-GM argument
11. **Moderator Close** (Moderator) - Neutral recap and conclusion

### LLM Role Assignment

| Persona | LLM Provider | Role | Characteristics |
|---------|-------------|------|-----------------|
| **Dr. Rosaline Tah** | Sarvam AI | Moderator | Neutral, impartial bioethics expert |
| **Felix Nji** | DeepSeek | Pro-GM Debater | Enthusiastic, optimistic, data-driven |
| **James Fru** | DeepSeek | Anti-GM Debater | Cautious, skeptical, risk-focused |

### Technical Implementation

- **`call_deepseek()`**: Handles DeepSeek API calls with system prompts, history, and instructions
- **`call_sarvam()`**: Handles Sarvam AI API calls with embedded prompts and history
- **History Management**: Maintains last 6 exchanges for context (prevents token overflow)
- **Temperature**: Set to 0.7 for balanced creativity and consistency
- **Max Tokens**: Limited to 400 per response for concise arguments

## Example Output Snippet

```
--- Opening Pro / FELIX ---
Good evening, everyone. I stand before you today to champion genetic modification—a 
revolutionary tool that can end malnutrition, cure genetic diseases, and secure our 
food supply. Consider Golden Rice: engineered to produce beta-carotene, it has the 
potential to prevent blindness in millions of children suffering from Vitamin A 
deficiency. CRISPR technology offers hope for families battling conditions like 
sickle cell anemia...
------------------------------------------------------------

--- Opening Against / JAMES ---
Thank you, Dr. Tah. While my opponent paints an optimistic picture, we must proceed 
with extreme caution. Genetic modification introduces irreversible changes to our 
ecosystem and human genome. We've witnessed unintended consequences before—GMO crops 
leading to herbicide-resistant superweeds, potential allergenicity concerns...
------------------------------------------------------------
```

## Notes

- The debate topic is hardcoded but can be modified by changing the persona prompts
- Each LLM call is independent; responses are generated based on system prompt + recent history + current instruction
- The moderator role uses Sarvam AI, while both debaters use DeepSeek (demonstrating how one LLM can play multiple roles)
- Rich console formatting is imported but not currently utilized in the output

## Future Enhancements

Potential improvements:
- Make debate topic configurable via command-line arguments
- Add Rich console formatting for better visual output
- Implement actual timing enforcement (currently only mentioned in moderator prompt)
- Save transcript to file automatically
- Add audience participation simulation
- Support for more than 2 debaters
- Real-time streaming of responses instead of batch processing

