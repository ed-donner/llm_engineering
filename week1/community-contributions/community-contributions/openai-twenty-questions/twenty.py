import openai
import os
import time

# openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_key = "<<Your Open AI Key here>>"

# Models: You can use "gpt-4o", "gpt-4-turbo", or "gpt-3.5-turbo" — but we'll use "gpt-4o" or "gpt-4o-mini" for both players
MODEL = "gpt-4o-mini"

def call_chatgpt(messages):
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message["content"].strip()

# Step 1: Thinker chooses a secret object
thinker_messages = [
    {"role": "system", "content": "You are playing 20 Questions. Think of an object or thing and just one word. Keep it secret and reply only with: 'I have thought of something. Let's begin.'"},
]
thinker_reply = call_chatgpt(thinker_messages)
print("Thinker:", thinker_reply)

# For simulation purposes, let’s ask the thinker what the object is (in real game, this is hidden)
reveal_object_prompt = [
    {"role": "system", "content": "You are playing 20 Questions. Think of an object or thing and just one word. Now tell me (just for logging) what you are thinking of. Reply only with the thing."}
]
object_answer = call_chatgpt(reveal_object_prompt)
print("🔒 Secret Object:", object_answer)

# Step 2: Guesser starts asking questions
guesser_messages = [
    {"role": "system", "content": f"You are playing 20 Questions. Ask yes/no questions to figure out what the object is. Do not repeat questions. The object is kept secret by the other player. Begin by asking your first question."},
]

# Let’s keep track of Q&A
history = []
q_count = 1

for i in range(1, 11):
    print(f"\n🔄 Round {q_count}")
    q_count += 1
    # Guesser asks a question
    question = call_chatgpt(guesser_messages)
    print("Guesser:", question)
    history.append(("Guesser", question))

    # Thinker responds (yes/no)
    thinker_round = [
        {"role": "system", "content": f"You are playing 20 Questions. The secret object is: {object_answer}."},
        {"role": "user", "content": f"The other player asked: {question}. Respond only with 'Yes', 'No', or 'I don't know'."}
    ]
    answer = call_chatgpt(thinker_round)
    print("Thinker:", answer)
    history.append(("Thinker", answer))

    # Add to conversation history for guesser
    guesser_messages.append({"role": "assistant", "content": question})
    guesser_messages.append({"role": "user", "content": answer})


    print(f"\n🔄 Round {q_count}")
    q_count += 1
    # Check if guesser wants to guess
    guess_check_prompt = guesser_messages + [
        {"role": "user", "content": "Based on the answers so far, do you want to guess? If yes, say: 'Is it <guess>?'. If not, ask the next yes/no question."}
    ]
    next_move_question = call_chatgpt(guess_check_prompt)
    print("Guesser next move:", next_move_question)
    history.append(("Guesser", next_move_question))

    if next_move_question.lower().startswith("is it a"):
        # Thinker validates guess
        guess = next_move_question[8:].strip(" ?.")
        guess = next_move_question[8:].strip(" ?")

        if guess.lower() == object_answer.lower():
            print("Guesser guessed correctly!")
            break
    # Thinker responds (yes/no)
    thinker_round = [
        {"role": "system", "content": f"You are playing 20 Questions. The secret object is: {object_answer}."},
        {"role": "user", "content": f"The other player asked: {next_move_question}. Respond only with 'Yes', 'No', or 'I don't know'."}
    ]
    answer = call_chatgpt(thinker_round)
    print("Thinker next move:", answer)
    history.append(("Thinker", answer))

    # Add to conversation history for guesser
    guesser_messages.append({"role": "assistant", "content": next_move_question})
    guesser_messages.append({"role": "user", "content": answer})

    # Prepare for next round
    guesser_messages.append({"role": "assistant", "content": next_move_question})
    question = next_move_question

else:
    print("❌ Guesser used all 20 questions without guessing correctly.")