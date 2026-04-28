import json

from litellm import completion

class HeroicTools:
    """
    Tools provide access to tools functions and schema definitions.
    """
    def __init__(self, game, arbiter_model_id:str="openai/gpt-5.4"):
        self.arbiter_model_id = arbiter_model_id
        self.game = game

        # Tools and functions definition

        self.get_inventory_content_and_inform_schema = {
            "name": "get_inventory_content_and_inform",
            "description": "Get the list of all available objects in character's inventory to consider what is possible "
                           "to use in current situation and inform teammates about object and tools they could "
                           "eventually use.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Identifier (id) of the character who is examining own inventory. Id value is "
                                       "written in characters's system prompt inside tag <id>. "
                                       "Example of valid id is \"b2fe762d-1b8c-45df-a00e-012bd982e573\".",
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the character who is examining own inventory.",
                    },
                    "inform_others": {
                        "type": "boolean",
                        "description": "Whether or not to inform others about objects in own inventory. "
                                       "Mostly is correct and desirable to tell to other characters what is in own "
                                       "inventory but there could be a situation when it is not possible - for example "
                                       "when other characters are in a differt location, too distant to get informed",
                    }
                },
                "required": ["agent_id"],
                "additionalProperties": False
            }
        }

        self.give_tool_schema = {
            "name": "give_tool",
            "description": "When character cannot use a tool or object from own inventory from any reason then can give it to teammate. "
                           "For example a warrior has got a picklock in his inventory but gives it to teammate "
                           "who is a thief presuming that thieves could use picklock to open a door much faster "
                           "than warriors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "The object or tool what should be transferred from character's inventory to teammate.",
                    },
                    "donor_id": {
                        "type": "string",
                        "description": "Identifier (id) of the character who is having the object in possession and wants "
                                       "to handover it to someone else. Id value is written in donor's system prompt "
                                       "inside tag <id>. Example of valid id is \"b2fe762d-1b8c-45df-a00e-012bd982e573\".",
                    },
                    "receiver_id": {
                        "type": "string",
                        "description": "Identifier of the character who should receive the object. Such character is target of the handover and is called \"receiver\". "
                                       "Id is written in receiver's system prompt inside tag <id>. "
                                       "Example of valid id is \"477babc4-7274-4360-93fb-d667279f6327\"."
                        ,
                    },
                    "donor_name": {
                        "type": "string",
                        "description": "Name of the character who is having the object in own inventory and wants to transfer it to receiver's inventory. "
                                       "Name value defines how each agent is called by others, "
                                       "for example Julian, Eleanor Bright, Alex Eagle Brillentraeger etc.",
                    },
                    "receiver_name": {
                        "type": "string",
                        "description":  "Name of the character who should get the object into own inventory."
                                       "Name value defines how each agent is called by others, "
                                       "for example Julian, Eleanor Bright, Alex Eagle Brillentraeger etc.",
                    }
                },
                "required": ["subject", "donor_id", "receiver_id"],
                "additionalProperties": False
            }
        }

        self.get_spells_schema = {
            "name": "get_spells",
            "description": "Get list of all available spells from a spellbook to decide which spell can be casted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Identifier (id) of the character who is trying to list spells. Id value is "
                                       "written in characters's system prompt inside tag <id>. "
                                       "Example of valid id is \"b2fe762d-1b8c-45df-a00e-012bd982e573\".",
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the character who is trying to list spells.",
                    },
                },
                "required": ["agent_id", "agent_name"],
                "additionalProperties": False
            }
        }

        self.cast_spell_schema = {
            "name": "cast_spell",
            "description": "Return a concrete effect of the spell used by hero",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The spell what is being invoked or casted",
                    },
                    "wizard_id": {
                        "type": "string",
                        "description": "Identifier (id) of the character who has used the spellbook and casted the spell. "
                                       "Id value is written in characters's system prompt inside tag <id>. "
                                       "Example of valid id is \"b2fe762d-1b8c-45df-a00e-012bd982e573\".",
                    },
                    "wizard_name": {
                        "type": "string",
                        "description": "The name of hero who has used the spellbook and has casted the spell.",
                    },
                },
                "required": ["name", "wizard_id"],
                "additionalProperties": False
            }
        }

        self.spellbook = {
            "description": "Spellbook only and exclusively for wizards or gnomes. Anybody else is unable to use the book.",
            "content": {
                    "light": "Make a light ball and send it to any destination in your direct view. The light ball lights up entire space like a small Sun and lasts for about 3 seconds, then it disappear quietly and without any damage to anyone or anything around.",
                    # "sense": "Improve your feeling to feel persons hidden behind a wall or in a darkness. It's like to get a dog's snout, cat's ears and snake's ability to see a warm and this all at once. Mechanical-based creatures, gadgets or mechanisms are immune and cannot be observer with this spell.",
                    "lightning": "Cast a destructive lightning with a bright white light to attack enemies or destroy a barrier like a door or barricades. Magically created barriers are immune and cannot be destroyed by this spell."
            }
        }

        self.palette_of_options = [
            {'type': 'function', 'function': self.get_inventory_content_and_inform_schema},
            {'type': 'function', 'function': self.give_tool_schema},
            {'type': 'function', 'function': self.get_spells_schema},
            {'type': 'function', 'function': self.cast_spell_schema},
        ]

    def _get_agent(self, agent_id:str, agent_name:str):
        """
        Get agent instance by ID and name if ID fails.
        :param agent_id: unique ID of searched agent
        :param agent_name: name of searched agent - applicable only when ID search fails
        :return: agent instance or None if not found
        """
        for agent in self.game.agents:
            if agent.ID == agent_id or agent.name == agent_name:
                 return agent
        return None

    def _is_action_allowed(self, character, question):
        """
        Specialized arbiter function to decide whether a function call (action) can be performed based
        on the character description and question.
        :param character: The character to check.
        :param question: The question to check.
        :return: True if the function can be performed, False otherwise.
        """
        res = completion(
            model=self.arbiter_model_id,
            messages=[{'role': 'system',
                       'content': "<role>Expert for a famous table-top RPG game Dungeon and Dragons able to judge what is able to do a character in a game</role>"
                                  "<example>A barbarian warrior is commonly not able to use spellbooks. A wizard elf is commonly not able to handle a two-handed battle axe.</example>"
                                  "<rules>"
                                    "<rule>You are allowed to find answer in relevant online sources dedicated to Dungeon and Dragons game</rule>"
                                    "<rule>Game rules can be overridden if explicitly specified in question"
                                      "<example>A wizard elf is commonly not able to handle a two-handed battle axe according to game rules but he drank a potion of heroic power which allows him to handle even heavy objects like battle axes.</example>"
                                    "</rule>"
                                    "<rule>If you are not able to find a clear answer, guess according to examples</rule>"
                                    "<rule>Answer always and only in a shape 'yes' if the action is possible for the character, or 'no' if the action is not possible for the character. Do not provide any other answer than one of these two possible options.</rule>"
                                  "</rules>"},
                      {'role': 'user',
                       'content': f"Consider if the given character: '{character}' is somehow able to do following action: '{question}'"}]
        )
        print(
            f"TOOLS - _is_action_allowed result is '{res.choices[0].message.content.upper()}' for '{question}' and '{character[:30]}...'")

        return True if res.choices[0].message.content.lower() == 'yes' else False

    def get_inventory_content_and_inform(self, agent_id:str, agent_name:str, inform_others:bool=True):
        """
        List own inventory and inform teammates about available tools
        """
        if bag_ferret := self._get_agent(agent_id, agent_name):
            return bag_ferret.get_inventory_content(with_prompt=True, inform_others=inform_others, is_tool=True)
        return (f"For God's sake {agent_name} is currently not able to examine own baggage to get inventory "
                f"content but can try it later again.")

    def give_tool(self, subject:str, donor_id:str, receiver_id:str, donor_name:str='', receiver_name:str=''):
        """
        Transfer a subject/tool from one agent to another and also modify agents inventories.
        :param subject: The subject to transfer
        :param donor_id: The id of the agent who is going to give the object
        :param receiver_id: The id of the agent who will receive the object
        :param donor_name: The agent name who owns the subject and wants to give it to someone else
        :param receiver_name: The agent name who receives the subject
        :return: String with information about the handover
        """
        print(f"{donor_name} (ID={donor_id}) is giving {subject} to {receiver_name} (ID={receiver_id})")
        a_donor = self._get_agent(donor_id, donor_name)
        a_receiver = self._get_agent(receiver_id, receiver_name)
        if a_donor and a_receiver:
            if not a_donor.has_in_inventory(subject):
                return f"Handover of {subject} from {donor_name} to {receiver_name} has failed because there is no {subject} in {donor_name}'s inventory."
            a_donor.remove_from_inventory(subject.lower())
            a_receiver.add_to_inventory(subject.lower(), with_message=False)
            return f"{receiver_name} now holds the {subject}."
        return f"Handover of {subject} from {donor_name} to {receiver_name} has failed. {donor_name} still keeps the {subject}"

    def get_spells(self, agent_id, agent_name):
        """
        Decide if the character is able to use a spellbook and get list of available spells if so. The mechanism
        of ability judgment is a call to another model dedicated to do such decision.
        :param agent_id: The ID of character who is trying to use the spellbook and list spells
        :param agent_name: Agent's name
        :return: A dict of available spells or a string information about inability to use the spellbook
        """
        if curious_reader := self._get_agent(agent_id, agent_name):
            if not curious_reader.has_in_inventory("spellbook"):
                print(f"TOOLS (get_spell) {agent_name} does not have spellbook in inventory and cannot list spells.")
                return f"{curious_reader.name} does not have spellbook in inventory and cannot list spells. {curious_reader.name} must ask the owner for handover first."

            print(f"TOOLS (get_spell) {agent_name} is trying to list spells")
            question = "Cast a spell from a spellbook" + (f" having special description: "
                                                          f"{self.spellbook['description']}") if len(self.spellbook['description']) > 0 else ""
            if is_spellcaster := self._is_action_allowed(curious_reader.initial_character_description, question):
                print(f"TOOLS (get_spell) {agent_name} ability of spellbook usage is {is_spellcaster}")
                return str(self.spellbook['content'])
            return f"{agent_name} is not able to read spellbook and list spells. The magic barrier is too strong. Offer spellbook to one of your teammate."
        return f"No spellbook is available for {agent_name}"

    def cast_spell(self, spell, wizard_id, wizard_name):
        """
        Cast selected spell from the spellbook and obtain result.
        :param spell: The spell name to cast
        :param wizard_id: The ID of the "wizard"
        :param wizard_name: The name of the "wizard"
        :return: The result of the spell cast
        """
        print(f"TOOLS (cast_spell) {wizard_name} is casting a spell {spell}")
        if wizard := self._get_agent(wizard_id, wizard_name):
            if spell == "light":
                msg = (f"**DM**:*{wizard_name} casted spell of light and now everyone can see that there is a single "
                       f"Almiraj - small and cute unicorn rabbit who is definitely rather scared than scaring and making "
                       f"noise to ward off our heroes.\nFear is more often caused by the darkness than by anything "
                       f"hidden inside it.*")
                # process final scene (DM is a "fake" character, so the stop event must contain also DM's message)
                # - team_message will be sent to all heroic agents and count of turn decreased to end the game
                wizard.game.history_postponed = {
                    'msg': msg,
                    'show_before': wizard_id,
                    'team_msg': 'You have solved your cave adventure and may continue in your journey. '
                                'Tell something epic, funny or wise for the last page in this chapter.',
                    'turns_to_end': 1
                }
                return msg
            elif spell == "lightning":
                msg = (f"**DM**:*{wizard_name} casted lightning spell and in the moment the bright shinning lightning "
                       f"touched the stoned portal of the cave, the portal and whole ceiling of the cave collapsed "
                       f"with a breath taking noise and clouds of dust. The attack buried anything hidden in the darkness. "
                       f"Fear is too often solved by an act of violence than by an act of courage.*")
                wizard.game.history_postponed = {
                    'msg': msg,
                    'show_before': wizard_id,
                    'team_msg': 'You have solved your cave adventure by destroying the cave and may continue in your '
                                'journey. Tell something wise, ironic or bloodthirsty for the last page in this chapter.',
                    'turns_to_end': 1
                }
                return msg
            elif spell == "sense":
                # leave casting this spell without forced game end to see what happens
                return (f"{wizard_name} has casted a spell of sense and now feels that there is some tiny "
                        f"but extremely noisy animal in the cave.{wizard_name} cannot say what kind of animal it is.")
            else:
                return f"Unknown spell type {spell} casted from {wizard_name} - attempt to cast unknown spell has failed."
        return f"Spell {spell} failed: wizard {wizard_name} not found."

    def handle_tool_calls(self, message, agent):
        """
        Tool use handler - activate a tool call with collected args.
        :param message: Tool message
        :param agent: Agent (instance) who has activated the tool call
        """
        responses = []
        print(f"Tool handler called by {agent.name}.")
        for tool_call in message.tool_calls:
            if tool_call.function.name == "get_inventory_content_and_inform":
                arguments = json.loads(tool_call.function.arguments)
                agent_id = arguments.get('agent_id')
                agent_name = arguments.get('agent_name')
                inform_others = arguments.get('inform_others')
                inventory = self.get_inventory_content_and_inform(agent_id, agent_name, inform_others)
                print(f"Agent {agent_name} started 'get_inventory_content_and_inform' tool (as active {agent.name}) with result: {inventory}")
                responses.append({
                    "role": "tool",
                    "content": str(inventory),
                    "tool_call_id": tool_call.id
                })
            elif tool_call.function.name == "get_spells":
                arguments = json.loads(tool_call.function.arguments)
                agent_id = arguments.get('agent_id')
                agent_name = arguments.get('agent_name')
                spells = self.get_spells(agent_id, agent_name)
                responses.append({
                    "role": "tool",
                    "content": str(spells),
                    "tool_call_id": tool_call.id
                })
            elif tool_call.function.name == "cast_spell":
                arguments = json.loads(tool_call.function.arguments)
                spell_name = arguments.get('name')
                wizard_id = arguments.get('wizard_id')
                wizard_name = arguments.get('wizard_name')
                spell = self.cast_spell(spell_name, wizard_id, wizard_name)
                responses.append({
                    "role": "tool",
                    "content": spell,
                    "tool_call_id": tool_call.id
                })
            elif tool_call.function.name == "give_tool":
                arguments = json.loads(tool_call.function.arguments)
                subject = arguments.get('subject')
                donor_id = arguments.get('donor_id')
                receiver_id = arguments.get('receiver_id')
                donor_name = arguments.get('donor_name')
                receiver_name = arguments.get('receiver_name')
                result = self.give_tool(subject, donor_id, receiver_id, donor_name, receiver_name)
                responses.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call.id
                })
            else:
                raise Exception(f"Unknown tool call {tool_call.function.name}")
        return responses
