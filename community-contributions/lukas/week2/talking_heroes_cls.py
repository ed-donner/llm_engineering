import os

from dotenv import load_dotenv
from pathlib import Path

from models.Game import Game
from models.Gui import Gui

def main():
    load_dotenv(override=True)

    # information extending basic character definition/task - intended as public (shared within team) or/and private
    # information (not shared among agents...unless agent's mouth "decides" to share)
    user_prompt_extensions = [
        {'public': "Character is a kind-natured snarky joker.",
         'private': "Task of this character is to persuade teammates to find any other way into the cave, "
                    "because character feels that the main entrance is a trap."},
        {'public': "Character is wise but pragmatic speaker.",
         'private': "Task of this character is to persuade teammates to leave the cave, go to the nearest village "
                    "and help anyone in need. It may improve team karma better than to attack some creatures "
                    "and get their treasures."},
        {'public': "Character commonly does not care about someone else's feelings or fears, but knows "
                   "that the teamwork requires democratic agreements, which is boring but also often life-saving.",
         'private': "The goal the character wants the most is to run directly inside the cave, brutally attack "
                    "anything inside and in the end to stand on a heap of defeated creatures with victorious smile "
                    "shining brighter than Sun reflecting admiringly from his oiled muscles. Business as usual."}
    ]

    # model ids to use
    model_ids = ["openai/gpt-5.4", "anthropic/claude-sonnet-4-6", "openai/gpt-5.4"]
    # model_ids = ["openai/gpt-5.4", "openai/gpt-5.4", "openai/gpt-5.4"]

    # Initial screen information (emulating Dungeon master) + initial agent prompt for getting situation context
    initial_history = ("**DM**: *Our heroes are standing in front of a mysteriously looking cave experiencing some "
                       "strange noise from inside. Due to darkness they cannot see what makes the noise. "
                       "Trick or Treat? They have started to talk what to do...*\n\n")

    # System prompt template for agents - will be "personalized" later
    system_prompt = """
                <role>Act as characters from famous table-top role playing game Dungeon and Dragons.</role>
                <context>You are on the way to a village in troubles, but you still don't know details. You unintentionally have encountered a mysteriously looking cave, hearing some ugly noise from inside, but due to darkness you cannot see what is there.</context>
                <task>Your task is to chat with your teammates according to role details you get in user prompt and decide what to do.</task>
                <rules>
                    <rule>Each character has an unique ID - your ID is <<ID>></rule>
                    <rule>All characters must speak in English language</rule>
                    <rule>Dialogues are prefixed with character Name to make it clear who says what. When the character name is used as prefix then it must be also marked as bold with double star.
                        <example>**Alex**: I can find another entrance.</example>
                    </rule>
                    <rule>You may react each other marking your teammate with naming
                        <example>**Brandon**: Alex, I totally agree with you but there is some issue...</example>
                    </rule>
                    <rule>Each response must be shorter than 333 characters.</rule>
                    <rule>You can use tools from your inventory only if you explicitly own such a tool in your inventory or baggage. If you cannot use the tool from any reason, offer it to someone else and hand it over if your teammate agrees.
                        <example>Brandon tells he has a magic sword in his baggage but is too weak to use it. You may ask for the sword and try to use it instead of Brandon.</example>
                    </rule>
                    <rule>Messages marked with tag "private" are known only to you, but you can share the information with team anytime - just talk about it.</rule>
                </rules>
                """

    data_file = Path(
        os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent, "data", "dnd_characters.txt"))

    game = Game(
        data_file_path=data_file,
        initial_history=initial_history,
        system_prompt=system_prompt,
        user_prompt_extensions=user_prompt_extensions,
        model_ids=model_ids
    )

    gui = Gui(game)
    gui.run()

if __name__ == '__main__':
    main()