
def talker(message, config):
    response = config.SDK.audio.speech.create(
      model=config.VOICE_MODEL,
      voice=config.VOICE,    # Also, try replacing onyx with alloy or coral
      input=message
    )
    return response.content

def call_openai_api_with_messages(messages_list, config):
    try:
        response = config.SDK.chat.completions.create(
            model=config.MODEL,
            messages=messages_list,
            temperature=config.TEMPERATURE
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ OpenAI API Error: {str(e)}"

def call_openai_api(system_prompt, user_prompt, config, max_tokens=1000):
    try:
        response = config.SDK.chat.completions.create(
            model=config.MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=config.TEMPERATURE
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ OpenAI API Error: {str(e)}"

def generate_user_guess_prompt(proposed_guess):
    return f"**PROPOSED GUESS:**\n[{', '.join(proposed_guess)}]\n"

def generate_game_history_prompt(game):
    if game.guesses:
        out = "**GUESS HISTORY:**\n"
        for idx, (guess, feedback) in enumerate(zip(game.guesses, game.feedback)):
            out += f"\nGuess #{idx + 1}: [{', '.join(guess)}]\n"
            out += f"  → Feedback: {feedback['black']} black pegs, {feedback['white']} white pegs\n"
            total_correct = feedback['black'] + feedback['white']
            if total_correct == 0:
                out += "  → Interpretation: None of these colors are in the secret code\n"
            elif feedback['black'] == 4:
                out += "  → Interpretation: Perfect match! Code was cracked.\n"
            else:
                out += f"  → Interpretation: {total_correct} colors from this guess are in the code\n"
    else:
        out = "**GUESS HISTORY:**\n(No previous guesses - this will be the first guess)\n"
    return out

def generate_game_state_prompt(game):
    attempt = len(game.guesses) + 1
    if game.won:
        status = "Won"
    elif game.game_over:
        status = "Lost"
    else:
        status = "In progress"
    return f"""**CURRENT STATE: **
- Attempt: {attempt} of {game.max_guesses}
- Game status: {status}
"""

def analyze_guess_with_llm(game, proposed_guess, system_prompt, user_prompt, config):

    # Validation
    if None in proposed_guess or "" in proposed_guess:
        return "⚠️ Please select all 4 colors before requesting analysis.", "⚠️ Incomplete guess"
    
    if game.game_over:
        return "🎮 Game is over! Start a new game.", "🎮 Game over"

    analysis = call_openai_api(system_prompt, user_prompt, config)

    if analysis.startswith("❌"):
        return analysis, "❌ API call failed"
    
    detailed = f"""🔍 **AI ANALYSIS** (via {config.SDK})

**Your Proposed Guess:** {' → '.join(proposed_guess)}

---

{analysis}
"""
    
    # Extract summary
    summary = extract_summary_from_analysis(analysis)
    
    return detailed, summary


def extract_summary_from_analysis(analysis_text):
    """Extract the summary section from LLM response"""
    
    summary_markers = ["SUMMARY:", "SUMMARY", "RECOMMENDATION:", "BOTTOM LINE:"]
    
    for marker in summary_markers:
        if marker in analysis_text.upper():
            idx = analysis_text.upper().index(marker)
            summary_section = analysis_text[idx + len(marker):].strip()
            
            # Take first 2-3 sentences
            sentences = []
            for sent in summary_section.split('.'):
                if sent.strip():
                    sentences.append(sent.strip())
                if len(sentences) >= 3:
                    break
            
            if sentences:
                summary = '. '.join(sentences)
                if not summary.endswith('.'):
                    summary += '.'
                return f"💡 {summary}"
    
    # Summary: take last paragraph
    paragraphs = [p.strip() for p in analysis_text.split('\n\n') if p.strip()]
    if paragraphs:
        last = paragraphs[-1]
        if len(last) < 400:
            return f"💡 {last}"
    
    return "💡 Analysis complete. See detailed breakdown above."
