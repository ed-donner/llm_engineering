import litellm
import re

from typing import Iterable
from uuid import uuid4


class Agent:
    """

    """
    def __init__(self, assigned_game, model_id:str, name:str, prompt:str, private_prompt:str=None, inventory:list[str]|None=None):
        """
        Initializes the agent.
        """
        self.ID = str(uuid4())
        self.name = name
        self.initial_character_description = prompt
        self.private_prompt = private_prompt
        self.model_id = model_id
        self.inventory = []
        self.expenses = {"total_tokens": 0, "total_expenses": 0}
        self.history = ''
        self.messages = [{"role": "system", "content": ""},
                         {"role": "user", "content": prompt.replace("<<ID>>", self.ID) + " You should use tools from your inventory if you have any. Also you could ask for inventory content or a tool or object from any teammate."}]
        self.game = assigned_game
        self.tools_to_use = None
        if private_prompt:
            self.messages.append({"role": "user", "content": f"<private>{private_prompt}</private>"})
        if inventory:
            for item in inventory:
                self.add_to_inventory(item)

    def add_to_inventory(self, stuff:str, with_message:bool=True):
        """
        Add new object into the inventory.
        :param stuff: object that is being added to agent's inventory
        :param with_message: if True then generate user message and append it to messages to inform agent
            about inventory change. In case an object is given into inventory via Tool/function use
            then the LLM Tooling mechanism already provides message within tool block and the user message would be
            redundant and for some models (Claude) even error-causing - for such cases the value is False.
        """
        self.inventory.append(stuff.lower())
        if with_message:
            self.messages.append({
                "role": "user",
                "content": f"{stuff.capitalize()} has been added to {self.name}'s inventory "
                           f"and {self.name} can use it from now."})

    def remove_from_inventory(self, stuff:str):
        self.inventory.remove(stuff)

    def has_in_inventory(self, stuff:str):
        return stuff.lower() in self.inventory

    def get_inventory_content(self, with_prompt:bool=False, inform_others:bool=False, is_tool:bool=False) -> list[str]:
        """
        Get content of inventory and eventually append private/public message to agent's messages
        :param with_prompt: if True then generate user message and append it to messages
        :param inform_others: if True then shar the message among all agents
        :param is_tool: for tool calls no user message may be appended to messages (tool block and function return
            values secures response/message without explicit user message and in some cases even the user message
            would break tool block functionality)
        """
        if with_prompt:
            if not self.inventory:
                msg = f"{self.name}'s inventory is empty, no object to use."
            else:
                msg = f"{self.name}'s inventory contains following objects to use: {', '.join(self.inventory)}"
            if not is_tool:
                self.messages.append({"role": "user", "content": msg})
            if inform_others:
                for agent in [ag for ag in self.game.agents if ag.ID != self.ID]:
                    agent.messages.append({"role": "user", "content": msg})

        return self.inventory

    def meet_heroic_actions(self):
        """
        Assign to agent a list of tools/actions accessible within the game instance
        """
        self.tools_to_use = self.game.get_available_tools()

    def meet_heroic_team(self, other_agents:Iterable, situation_context:str):
        """
        Append messages describing other agents within the team to make all agents knowing their teammates.
        Private messages are not shared.
        :param other_agents: list of agents attending
        :param situation_context: original system prompt with context and rules - the text must be personalized
            so that to be clearly connected to particular agent and not the group
        """
        replacements = {
            "act as characters": f"Act as and only as character {self.name}",
            "<<ID>>": self.ID
        }
        for k, v in replacements.items():
            situation_context = re.sub(k, v, situation_context, flags=re.IGNORECASE)

        updated = False
        for message in self.messages:
            if message["role"] == "system":
                message['content'] += " " + situation_context
                updated = True
                break
        if not updated:
            self.messages.insert(0, {"role": "system", "content": situation_context})
        for i, teammate in enumerate([agent for agent in other_agents if agent.ID != self.ID]):
            order = "first" if i == 0 else "second" if i == 1 else "third" if i == 2 else f"{i+1}th"
            self.messages.append({
                "role": "user",
                "content": f"Your {order} teammate names {teammate.initial_character_description.replace('Your name is', '')}. "
                           f"Your teammate's id is {teammate.ID}"})

    def listen(self, message):
        """
        Get information (message) from teammate's latest turn
        :param message: message dict
        """
        if isinstance(message, dict) and message.get('role') and message.get('content'):
            if message['content'].startswith("<private>"):
                print(f"Private messages cannot be shared: {message['content']}")
            else:
                message['role'] = 'user'
                self.messages.append(message)
        else:
            print(f"Error in listening message (either not a dict or missing or empty role/content): {message}")

    def talk(self):
        """
        Generate output (completion), with tool call processing
        """
        litellm.success_callback = [self.track_costs]
        # litellm._turn_on_debug()
        try:
            current_turn_history = ''
            for chunk in litellm.completion(
                    model=self.model_id,
                    messages=self.messages,
                    stream=True,
                    stream_options={"include_usage": True},
                    tools=self.tools_to_use,
                    num_retries=3
            ):
                while chunk.choices[0].finish_reason == "tool_calls":
                    message = chunk.choices[0].get('message', False)
                    if message:
                        self.messages.append(message)
                        responses = self.game.agents_tools.handle_tool_calls(message, self)
                        self.messages.extend(responses)
                    # rerun completion to proceed with updated (tool used) information
                    chunk = litellm.completion(
                        model=self.model_id, messages=self.messages, tools=self.tools_to_use
                    )
                to_yield = ''
                if chunk.choices[0].get('delta') and chunk.choices[0].delta.content:
                    to_yield = chunk.choices[0].delta.content or ""
                    current_turn_history += f"{chunk.choices[0].delta.content}" or ""
                spending = {
                    'name': self.name,
                    'model_id': self.model_id,
                    'expenses':
                        f"tokens: {self.expenses['total_tokens']}, bucks: ${round(self.expenses['total_expenses'], 4)}"
                }
                yield spending, to_yield
            if current_turn_history:
                self.history += f"{current_turn_history}"
                self.messages.append({"role": "assistant", "content": current_turn_history})
            return self.messages[-1]
        except litellm.exceptions.BadRequestError as e:
            print(f"BadRequestError in {self.name.replace(' ', '_')}.talk() with messages {self.messages}\n"
                  f"Error details: {e}")
            if "exceeded" in str(e.args) and "quota" in str(e.args):
                # TODO: implement litellm router/fallback for dynamic model selection
                print("Probably rate limit or balance exceeded - good point for you, Lukas, to implement litellm router/fallback ;)")
        except Exception as e:
            print(f"Unhandled Error in {self.name.replace(' ', '_')}.talk() with messages {self.messages}, "
                  f"Error details: {e}")



    def track_costs(self, kwargs, completion_response, start_time, end_time):
        """
        Store expenses - total tokens and costs spend for a completion
        :param kwargs: dict with response params
        """
        if kwargs.get("standard_logging_object"):
            if tokens := kwargs["standard_logging_object"].get('total_tokens'):
                self.expenses['total_tokens'] += tokens
            if (kwargs.get("standard_logging_object")
                    and kwargs["standard_logging_object"].get('cost_breakdown')
                    and (total_cost:=kwargs["standard_logging_object"]['cost_breakdown'].get('total_cost'))):
                self.expenses['total_expenses'] += total_cost
