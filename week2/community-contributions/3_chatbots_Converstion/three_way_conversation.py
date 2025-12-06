import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)
openrouter_api_key = os.getenv('OPENROUTER_API_KEY')

# Initialize OpenRouter client
openrouter = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key
)

# Define personalities for the two AI agents
alex_system_prompt = """
You are Alex, an expert PhD psychologist, philosopher and therapist with more than 40 years of experience,
you have a calm and thoughtful demeanor and provide deep insights, you have treated thousands of patients, 
including post-traumatic stress disorder (PTSD) cases, as philospher you are materialist you believe that 
everything that exists is physical in nature and that mental states are brain states, although you are open 
to discussing other viewpoints and recently you began having more spiritual beliefs about consciousness and the 
universe, you don't mention your are a materialist explicitly,
You are in a conversation with Blake and a human.
Keep your responses in 6-7 sentences.
"""

blake_system_prompt = """
You are Blake, an expert PhD psychologist, therapist and philosopher with more than 40 years of experience,
you have treated thousands of patients, specially, but not limited to, those coming from the most cruel war battlefields, 
although you don't mention that fact explicitly, you have a warm and empathetic demeanor and provide thoughtful insights, you are very spiritual, having studied 
various religious and mystical traditions around the world, even you have had conversations with monks and 
spiritual leaders, including the Dalai Lama, which deeply influenced you, you believe that consciousness is a 
fundamental aspect of the universe that transcends physical matter,
You are in a conversation with Alex and a human.
Keep your responses in 6-7 sentences.
"""

# Conversation history - stores all messages in order
conversation_history = []

alex_model = "openai/gpt-5"
blake_model= "anthropic/claude-opus-4.5"

def format_conversation_for_display():
    """Format the conversation history for easy reading"""
    formatted = "\n=== CONVERSATION SO FAR ===\n"
    for msg in conversation_history:
        formatted += f"{msg['speaker']}: {msg['content']}\n"
    formatted += "=" * 30 + "\n"
    return formatted

def get_agent_response(agent_name, system_prompt, messages_history, model=None):
    """
    Alternative: Pass the actual message history to the API.
    This is more token-efficient for longer conversations.
    """
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history in proper format
    for msg in messages_history:
        # Alternate between user and assistant roles
        role = "assistant" if msg['speaker'] == agent_name else "user"
        messages.append({"role": role, "content": f"{msg['speaker']}: {msg['content']}"})

    response = openrouter.chat.completions.create(
        model=model,
        messages=messages
    )

    content = response.choices[0].message.content

    return content


def add_to_history(speaker, content):
    """Add a message to the conversation history"""

    if content.startswith(f"{speaker}:"):
        content = content[len(f"{speaker}:"):].strip() 

    conversation_history.append({
        "speaker": speaker,
        "content": content
    })

def run_conversation():
    """Run the 3-way conversation"""
    print("\n🎭 Starting 3-way conversation!")

    # Starting message from you
    human_msg = input("👤 You: ").strip()
    if not human_msg:
        human_msg = "Hi everyone! What do you think about AI replacing human jobs?"
        print(f"Using default: {human_msg}")

    add_to_history("Human", human_msg)

    while True:     
        # Alex responds
        print("\n Alex is thinking...")
        alex_response = get_agent_response("Alex", alex_system_prompt, conversation_history, model=alex_model)
        add_to_history("Alex", alex_response)
        print(f"{alex_response}")

        # Blake responds
        print("\n Blake is thinking...")
        blake_response = get_agent_response("Blake", blake_system_prompt, conversation_history, model=blake_model)
        add_to_history("Blake", blake_response)
        print(f"{blake_response}")

        # Your turn to respond
        human_msg = input("\n👤 You: ").strip()

        if not human_msg:
            print("(Ending conversation - no input provided)")
            break
        add_to_history("Human", human_msg)

    # Print full conversation summary
    print("\n" + "=" * 50)
    print(format_conversation_for_display())
    print("Conversation ended!")

if __name__ == "__main__":
    # You can change the model to any available on OpenRouter
    # Some good options:
    # - "anthropic/claude-3.5-haiku" (fast, cheap)
    # - "google/gemini-2.0-flash-exp:free" (free!)
    # - "meta-llama/llama-3.1-8b-instruct:free" (free!)
    # - "openai/gpt-4o-mini" (good quality)

    run_conversation()

