"""AI Mastered Dungeon Extraction Game Storyteller using OpenAI's GPT."""

from typing import List

from annotated_types import MaxLen
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from .tools import handle_tool_call, tools


# Environment initialization.
load_dotenv(override=True)

# Define globals.
MODEL = 'gpt-4o-mini'

# Client instantiation.
CLIENT = OpenAI()


# Define Pydantic model classes for response format parsing.
class _character_sheet(BaseModel):
    health: int
    max_health: int
    level: int
    experience: int


class _response_format(BaseModel):
    game_over: bool
    scene_description: str = Field(..., max_length=700)
    dungeon_deepness: int
    adventure_time: int
    adventurer_status: _character_sheet
    inventory_status: List[str]

    def __str__(self):
        """Represent response as a string."""
        response_view = (
            f'{self.scene_description}'
            f'\n\nInventory: {self.inventory_status}'
            f'\n\nAdventurer: {self.adventurer_status}'
            f'\n\nTime: {self.adventure_time}'
            f'\n\nDeepness: {self.dungeon_deepness}'
            f'\n\nGame Over: {self.game_over}')
        return response_view


def set_description_limit(limit):  # HBD: We modify the class definition in runtime.
    """Update "_response_format" class to set a new "scene_description" max length."""
    _response_format.model_fields['scene_description'].metadata[0] = MaxLen(limit)


# Function definition.
def narrate(message, history, system_message, client=CLIENT, model=MODEL):
    """Chat with the game engine."""
    messages = ([{"role": "system", "content": system_message}] + history
                + [{"role": "user", "content": message}])
    response = client.chat.completions.parse(model=model, messages=messages, tools=tools,
                                             response_format=_response_format)
    # Process tool calls.
    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        tool_response = handle_tool_call(message)
        messages.append(message)
        messages.append(tool_response)
        response = client.chat.completions.parse(model=model, messages=messages,
                                                 response_format=_response_format)
    # Return game's Master response.
    return response.choices[0].message.parsed
