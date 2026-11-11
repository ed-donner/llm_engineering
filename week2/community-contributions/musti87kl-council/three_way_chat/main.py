# importing config runs it once, which loads the keys
import config
from personas import gpt_model, claude_model, llama_model, gpt_system, claude_system, llama_system
from chat import ask

# the seating plan: (name, model, persona), in speaking order
bots = [
    ("Alex", gpt_model, gpt_system),
    ("Blake", claude_model, claude_system),
    ("Charlie", llama_model, llama_system),
]

transcript = "Charlie: Welcome to the debate! Which club is the best in history?\n"
print(transcript)

# running total of what the whole debate costs
total_cost = 0

# 11 rounds, each bot speaks once per round
for turn in range(11):
    for name, model, system in bots:
        # ask() returns a tuple, so catch both values at once
        reply, cost = ask(model, system, transcript + f"\nYou are {name}. Write only your next message.")
        print(f"{name}: {reply}\n   (cost: {cost*100:.4f} cents)\n")
        transcript += f"{name}: {reply}\n"
        total_cost += cost

print(f"Whole debate cost: {total_cost*100:.4f} cents")