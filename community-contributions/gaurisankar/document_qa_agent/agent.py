import transcript_parser
from config import SYSTEM_PROMPT
from llm import create_client, get_response


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def welcome_user():
    """Print a welcome message to the user."""
    print("Welcome to the Document Q&A Agent!")
    print("This Agent can answer questions about text files.")
    print("You can ask questions about the transcript, generate a summary, or generate content using the same.")
    print("Type 'exit' to quit.")
    print()


# ---------------------------------------------------------------------------
# Agent Core
# ---------------------------------------------------------------------------
def run_agent(raw_transcript: str):
    """
    Run the main Q&A loop. Maintains conversation memory across turns.

    Args:
        raw_transcript (str): The full text extracted from the document.
    """
    client = create_client()

    # Conversation history — grows with each turn for multi-turn memory
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + raw_transcript}
    ]

    while True:
        user_query = input("\nAsk anything or type exit to quit:\n> ").strip()

        if user_query.lower() == "exit":
            print("Goodbye!")
            break

        if not user_query:
            continue

        messages.append({"role": "user", "content": user_query})

        try:
            response_text = get_response(messages, client)
            print(f"\nAgent: {response_text}")
            messages.append({"role": "assistant", "content": response_text})

        except Exception as e:
            print(f"\n[Error] - Unable to generate response :(\nDetails: {e}")
            messages.pop()  # Remove failed query so history stays consistent


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
def main():
    welcome_user()

    raw_transcript = transcript_parser()
    run_agent(raw_transcript)


if __name__ == "__main__":
    main()
