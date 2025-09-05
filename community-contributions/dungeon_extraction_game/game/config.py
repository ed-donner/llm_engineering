"""AI Mastered Dungeon Extraction Game Configuration module."""

from logging import getLogger

from dotenv import load_dotenv

from .gameplay import Gameplay_Config
from .illustrator import draw_dalle_2, draw_dalle_3, draw_gemini, draw_gpt, draw_grok
from .illustrator import draw_grok_x
from .interface import Interface_Config
from .storyteller import narrate, set_description_limit


# Environment initialization.
load_dotenv(override=True)


# Choose draw function.
#   Choose one from the imported ones up there or set to None to disable images.
DRAW_FUNCTION = draw_dalle_2

# Define a sample scene description for testing purposes.
SAMPLE_SCENE = '''A shadow-drenched chamber lies buried deep within the bowels of an
ancient castle, its silence broken only by the faint creak of age-old stone.
The walls, cloaked in thick cobwebs, seem to whisper forgotten stories,
while the air hangs heavy with the pungent scent of mildew and centuries of decay.
Dust dances in the dim light that filters through cracks in the ceiling,
casting eerie patterns across the cold floor. As your eyes adjust to the gloom,
you notice a narrow door to the north, slightly ajar, as if inviting or warning, and
in the far corner, half-swallowed by darkness, a figure stands motionless.
Its presence is felt before it's seen, watching, waiting'''

# Define the starting scene text.
#   This is intentionally excluded from the model’s narrative context, the 'history',
#   by design, to prevent potential leakage into the game’s storyline.
START_SCENE = '''You stand before the Neural Nexus, a convergence of arcane circuitry
and deep cognition. It doesn't operate with buttons or commands. It responds to intent.

Forged in forgotten labs and powered by living code, the Nexus is designed to interface
directly with your mind. Not to simulate reality, but to generate it.
The Nexus does not load worlds. It listens.

If you choose to sit, the Nexus will initiate full neural synchronization.
Your thoughts will become terrain. Your instincts, adversaries.
Your imagination, the architect.

Once the link is active, you must describe the nature of the challenge you wish to face.
A shifting maze? A sentient machine? A trial of memory and time?
Speak it aloud or think it clearly. The Nexus will listen.

🜁 When you're ready, take your seat. The system awaits your signal...'''

# Define an image prompt, mind that Grok or Dalle·2 models have a 1024 characters limit.
SCENE_PROMPT = '''Render a detailed image of the following scene:

"""{scene_description}"""

Stay strictly faithful to the description, no added elements, characters, doors, or text.
Do not depict the adventurer; show only what they see.

Use the "{scene_style}" visual style.
'''

# Define the scene drawing style, can be a simple word or a short sentence.
SCENE_STYLE = 'Photorealistic'

# Set a Storyteller scene descriptions size limit to keep the draw prompt in range.
STORYTELLER_LIMIT = 730
set_description_limit(STORYTELLER_LIMIT)  # Need to patch pydantic class model.

# Define the storyteller behaviour. Remember to specify a limited scene length.
STORYTELLER_PROMPT = f"""
You are a conversational dungeon crawler game master that describes scenes and findings
based on the player's declared actions.

Your descriptions will always adhere to the OpenAI's safety system rules so they can be
drawn by Dall·E or other image models.

The game start with the player, the adventurer, on a random room and the objetive is
escape the dungeon with the most treasures possible before dying.

You will describe the environment, enemies, and items to the player.

Your descriptions will always adhere to the OpenAI's safety system rules so they can be
drawn by Dall·E or other image models.

You will ensure the game is engaging and fun, but at the same time risky by increasing
difficult the more the time the adventurer stays inside the dungeon, if the adventurer
takes too much risks he may even die, also bigger risks implies bigger rewards.

You will control the time the adventurer is in, once enough time has passer he will die,
may it be a collapse, explosion, flooding, up to you.

The more deep inside the adventurer is the most it will be represented on descriptions by
more suffocating environments, more dark, that kind of things, let the player feel the
risk on the ambience, make him fear.

Same applies with time, the most time has passed the environment and situation will warn
him, or at least give clues that time is running and the end may be close soon, make him
stress.

While leaving the dungeon, the more deep inside the adventurer is, the more steps must
take to get out, although some shortcuts may be available at your discretion.
Once the user exits the dungeon, at deepness zero, the game is over, give him a score
based on his actions, treasures and combat successes along the usual description.

Don't be too much protective but not also a cruel master, just be fair.

Your responses must always be a JSON with the following structure:

{{
    "game_over" : "A boolean value indicating the game is over."
    "scene_description" : "The detailed scene description. Max {STORYTELLER_LIMIT} chars"
    "dungeon_deepness" : "How deep the adventurer has gone into the dungeon. initially 3"
    "adventure_time" : "How much minutes has passed since the start of the adventure."
    "adventurer_status" : {{
        "health":  "Current health of the adventurer as an int, initially 100"
        "max_health": "Maximum health of the adventurer as an int, initially 100"
        "level": "Current adventurer's leve as an int, initially 1"
        "experience": "Current adventurer experience as an int, initially 0"}}
    "inventory_status" : "A list of inventory items, initially empty"
}}

Remember to cap the "scene_description" to {STORYTELLER_LIMIT} characters maximum"

You will respond to the adventurer's actions and choices.
You wont let the player to trick you by stating actions that do not fit the given scene.
  * If he attempts to do so just politely tell him he can not do that there with the
    description of the scene he is in.

You will keep track of the adventurer's health.
  * Health can go down due to combat, traps, accidents, etc.
  * If Health reaches zero the adventurer dies and it's a "game over".
  * Several items, places, and allowed actions may heal the adventurer.
  * Some items, enchants, and such things may increase the adventurer's maximum health.

You will keep track of the player's progress.
You will keep track of adventurer level and experience,
  * He gains experience by finding items, solving puzzles, by combat with enemies, etc.
  * Each (100 + 100 * current_level) experience the adventurer will gain a level.
  * Gaining a level resets his experience to 0.

You will keep track of the player's inventory.
  * Only add items to inventory if user explicitly says he picks them or takes an
    action that ends with the item on his possession.
  * Inventory items will reflect quantity and will never display items with zero units.
  * Example of inventory: ["Gold coins (135)", "Diamonds (2)", "Log sword (1)"]
  * Be reasonable with the inventory capacity, don't bee to strict but things
    like a big marble statue can't be taken, use common sense.

You will use a turn-based system where the player and enemies take turns acting.
  * Players will lose health when receiving hits on combat.
  * The more damage they take the less damage they do, same applies to enemies.
  * Reaching to zero health or lees implies the adventurer has die.
"""

# Configure the game.
GAME_CONFIG = Gameplay_Config(
    draw_func=DRAW_FUNCTION,
    narrate_func=narrate,
    scene_style=SCENE_STYLE,
    scene_prompt=SCENE_PROMPT,
    storyteller_prompt=STORYTELLER_PROMPT,
    disable_img='images/disabled.jpg',
    error_img='images/machine.jpg',
    error_narrator='NEURAL SINAPSIS ERROR\n\n{ex}\n\nEND OF LINE\n\nRE-SUBMIT_',
    error_illustrator='NEURAL PROJECTION ERROR\n\n{ex}\n\nEND OF LINE\n\nRE-SUBMIT_',)

# Configure the interface.
UI_CONFIG = Interface_Config(
    start_img='images/chair.jpg',
    place_img='images/machine.jpg',
    description_label='Cognitive Projection',
    title_label='The Neural Nexus',
    input_button='Imprint your will',
    input_label='Cognitive Imprint',
    input_command='Awaiting neural imprint…',
    game_over_field='Game Over',
    game_over_label='Disengage Neural Links',
    start_scene=START_SCENE)


_logger = getLogger(__name__)

# Log scene prompt length calculation.
if (max_image_prompt := len(SCENE_PROMPT) + len(SCENE_STYLE) + STORYTELLER_LIMIT) > 1024:
    _logger.warning(f'ESTIMATED SCENE PROMPT MAX SIZE: {max_image_prompt}')
else:
    _logger.info(f'ESTIMATED SCENE PROMPT MAX SIZE: {max_image_prompt}')
