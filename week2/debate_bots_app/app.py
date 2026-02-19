import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import Markdown, display
import gradio as gr


load_dotenv(override=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
GPT = "gpt-5-nano"
CLAUDE = "claude-haiku-4-5"
GROK = "grok-4-fast-reasoning"

openai = OpenAI()
anthropic = OpenAI(base_url="https://api.anthropic.com/v1", api_key=anthropic_api_key)
grok = OpenAI(base_url="https://api.x.ai/v1", api_key=grok_api_key)

# Debate configuration
affirmative_system = "You are a debater in your soul, determine to win every debate, always taking the affirmative side."
negative_system = "You are a debater in your soul, determine to win every debate, always taking the negative side."
turns = ["affirmative", "negative", "affirmative", "negative", "affirmative", "negative"]
speeches = ["constructive speech", "constructive speech", "rebuttal", "rebuttal", "closing speech", "closing speech"]

def get_client(model_name):
    """Get the appropriate client for the model"""
    if model_name == GPT:
        return openai
    elif model_name == CLAUDE:
        return anthropic
    else:
        return grok

def call_affirmative_stream(model, affirmative_message, negative_message):
    """Stream affirmative response chunk by chunk"""
    messages = [{"role": "system", "content": affirmative_system}]
    for aff, neg in zip(affirmative_message, negative_message):
        messages.append({"role": "assistant", "content": aff})
        messages.append({"role": "user", "content": neg})
    
    client = get_client(model)
    stream = client.chat.completions.create(model=model, messages=messages, stream=True)
    
    result = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            result += chunk.choices[0].delta.content
            time.sleep(0.05)  # Add delay to slow down streaming (50ms per chunk)
            yield result


def call_negative_stream(model, affirmative_message, negative_message):
    """Stream negative response chunk by chunk"""
    messages = [{"role": "system", "content": negative_system}]
    for aff, neg in zip(affirmative_message, negative_message):
        messages.append({"role": "user", "content": aff})
        messages.append({"role": "assistant", "content": neg})
    messages.append({"role": "user", "content": affirmative_message[-1]})
    
    client = get_client(model)
    stream = client.chat.completions.create(model=model, messages=messages, stream=True)
    
    result = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            result += chunk.choices[0].delta.content
            time.sleep(0.05)  # Add delay to slow down streaming (50ms per chunk)
            yield result

def call_judge(model, full_debate, affirmative_model, negative_model):
    judge_system = f"You are a debate judge presented with a full debate by teams affirmative (played by {affirmative_model}) and negative (played by {negative_model}). \
    The turns in the debate are {turns} and the speeches are {speeches}. \
    Please rate the performance of each team on five categories (please choose integer values between 1 and 4): \
        1. Organization and Clarity (1-4)\
        2. Use of arguments (1-4)\
        3. Use of examples and facts (1-4)\
        4. Use of rebuttal (1-4)\
        5. Presentation style (1-4)\
    Present the scoring in a table where the rows are the categories and the columns are the models, then on a new line with large font state 'the winner is ...' with the name of the model (gpt/claude/grok).\
        return your answer between <center> and </center>"
    
    messages = [{"role": "system", "content": judge_system},
                {"role": "user", "content": full_debate}]
    client = get_client(model)
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content

def debate(topic, affirmative_model, negative_model, judge_model, turn, last_aff, last_neg, aff_msg, neg_msg, debate_data):
    """Run a debate with the given topic and models"""
    # Ensure turn is an integer
    turn = int(turn) if turn is not None else 1
    
    # Initialize message history only on first turn
    if turn == 1:
        affirmative_message = [f"let's debate about {topic}, in the turns {turns} and the speeches {speeches}"]
        negative_message = [f"ok. start with your {speeches[0]}."]
        debate_info = []
    else:
        # Use stored message history from previous turns
        affirmative_message = list(aff_msg) if aff_msg else [f"let's debate about {topic}, in the turns {turns} and the speeches {speeches}"]
        negative_message = list(neg_msg) if neg_msg else [f"ok. start with your {speeches[0]}."]
        debate_info = list(debate_data) if debate_data else []
    
    # Check if all turns are complete (turn exceeds number of turns)
    if turn > len(turns):
        full_debate = "\n\n".join(debate_info)
        judge_response = call_judge(judge_model, full_debate, affirmative_model, negative_model)
        judge_output = f"## JUDGE'S VERDICT\n\n{judge_response}"
        # Return the last responses - remove purple borders from both textboxes
        # Need 10 values total (including button)
        yield (
            gr.update(value=last_aff, elem_classes=[]),
            gr.update(value=last_neg, elem_classes=[]),
            gr.update(visible=True, value=judge_output),
            turn,
            last_aff,
            last_neg,
            affirmative_message,
            negative_message,
            debate_info,
            gr.update(value="Next Turn", interactive=False)
        )
        return
    
    # Get the role and speech for the current turn (turn is 1-indexed, arrays are 0-indexed)
    role, speech = turns[turn-1], speeches[turn-1]
    if role == "affirmative":
        negative_message.append(f"\nNow for your {speech}.")
        # Stream the affirmative response
        for partial_response in call_affirmative_stream(affirmative_model, affirmative_message, negative_message):
            # Yield partial updates with streaming response
            yield (
                gr.update(value=partial_response, elem_classes=["purple-border"]),
                gr.update(value=last_neg if last_neg else "", elem_classes=[]),
                gr.update(visible=False),
                turn,  # Don't update turn until complete
                partial_response,  # Current response
                last_neg,
                affirmative_message,
                negative_message,
                debate_info,
                gr.update(value="Next Turn")
            )
        
        # After streaming is complete, save the full response and increment turn
        affirmative_next = partial_response
        affirmative_message.append(affirmative_next)
        debate_info.append(f"AFFIRMATIVE ({speech}): {affirmative_next}")
        next_turn = turn + 1
        # Final return with updated state
        yield (
            gr.update(value=affirmative_next, elem_classes=["purple-border"]),
            gr.update(value=last_neg if last_neg else "", elem_classes=[]),
            gr.update(visible=False),
            next_turn,
            affirmative_next,
            last_neg,
            affirmative_message,
            negative_message,
            debate_info,
            gr.update(value="Next Turn")
        )
    
    else:
        affirmative_message.append(f"\nNow for your {speech}.")
        # Stream the negative response
        for partial_response in call_negative_stream(negative_model, affirmative_message, negative_message):
            # Yield partial updates with streaming response
            yield (
                gr.update(value=last_aff if last_aff else "", elem_classes=[]),
                gr.update(value=partial_response, elem_classes=["purple-border"]),
                gr.update(visible=False),
                turn,  # Don't update turn until complete
                last_aff,
                partial_response,  # Current response
                affirmative_message,
                negative_message,
                debate_info,
                gr.update(value="Next Turn")
            )
        
        # After streaming is complete, save the full response and increment turn
        negative_next = partial_response
        negative_message.append(negative_next)
        debate_info.append(f"NEGATIVE ({speech}): {negative_next}")
        next_turn = turn + 1
        # Final return with updated state
        yield (
            gr.update(value=last_aff if last_aff else "", elem_classes=[]),
            gr.update(value=negative_next, elem_classes=["purple-border"]),
            gr.update(visible=False),
            next_turn,
            last_aff,
            negative_next,
            affirmative_message,
            negative_message,
            debate_info,
            gr.update(value="Next Turn")
        )