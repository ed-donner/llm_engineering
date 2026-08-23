import asyncio
import json

import litellm
import re

from itertools import cycle
from logging import getLogger
from pathlib import Path

from .Agent import Agent

logger = getLogger(__name__)

class AgentFactory:

    def __init__(self, assigned_game, source_file:str, prompt_extensions:list[str]=None):
        """
        Init instance
        :param source_file:
        """
        self.assigned_game = assigned_game
        self.source_file = source_file
        self.summarizer_prompt = """
        You are provided with a text containing a game character. Your task is to pick name and a summary 
        of each character describing personality and communication style with maximum 333 characters. Your task is 
        also to pick objects what is character having in inventory, mostly marked explicitly in the text 
        for example like "Inventory: object1, object2,...". Character may have no, single or more objects in inventory.
        Output format must be JSON and only JSON with structure: 
        [
            {
                "name": "name of character",
                "class": "character's class name",
                "description": "summary of character",
                "inventory": ["object1", "object2"]
            }
        ]
        When there is no object in inventory, return empty list "inventory": [].
        """
        self.prompt_extensions = prompt_extensions

    async def process_character_data(self, enriched_agent: tuple[dict, dict]):
        """
        Extract character name and short summary from given description
        """
        try:
            scaffolded_agent = enriched_agent[0]
            prompt_extension = enriched_agent[1]
            print("Starting with", enriched_agent[1]['public'][:50]+'...')

            response = await litellm.acompletion(
                model="openai/gpt-5-mini",
                messages=[
                    {'role': 'system', 'content': self.summarizer_prompt},
                    {'role': 'user', 'content': enriched_agent[0]['prompt']}],
                reasoning_effort="low"
            )
            result = json.loads(response.choices[0].message.content)
            result = result if not isinstance(result, list) else result[0]
            scaffolded_agent['name'] = result['name']
            scaffolded_agent['class'] = result['class']
            scaffolded_agent['prompt'] = (
                f"Your name is {result['name']}. You are a {result['class'] if result['class'] else 'character'} "
                f"with following description: {result['description']}.")
            scaffolded_agent['inventory'] = result['inventory']

            if prompt_extension:
                if public_ext := prompt_extension.get('public'):
                    scaffolded_agent['prompt'] += ' ' + public_ext
                if private_ext := prompt_extension.get('private'):
                    scaffolded_agent['private_prompt'] = private_ext
            print("Agent thrown into game:", scaffolded_agent['name'])
            return Agent(
                self.assigned_game,
                scaffolded_agent['model_id'],
                scaffolded_agent['name'],
                scaffolded_agent['prompt'],
                scaffolded_agent.get('private_prompt', None),
                scaffolded_agent.get('inventory', None)
            )
        except litellm.exceptions.BadRequestError as e:
            print(f"BadRequestError in AgentFactory.process_character_description\nError details: {e.args}")
        except IndexError as e:
            print(f"IndexError in AgentFactory.process_character_description\nError details: {e.args}")
        except Exception as e:
            print(f"Unhandled Error in AgentFactory.process_character_description\nError details: {e.args}")

    async def generate(self, models:str|list[str], agent_count:int=3):
        """
        Read characters from text file and generate agents.
        :param assigned_game: game instance to be assigned to generated agent
        :param models: model id or list of model ids to assign to each agent - when the requested count of agents
            differs from count of model ids
        :param agent_count: number of agents to generate
        :param prompt_extensions: list of extended information to be appended to agent characteristics
        """
        if isinstance(models, str):
            models = [models]
        if len(models) != agent_count:
            logger.warning(msg="Agent count differs from number of models - using either less models than given "
                               "or using models cyclically (although warning is not a wall consider to modify args "
                               "to match each other if you prefer warningless program executions...)")
        models = cycle(models)

        if not Path(self.source_file).exists():
            raise FileNotFoundError(f'{self.source_file} not found')
        with open(self.source_file, "r", encoding="utf-8") as datafile:
            content = datafile.read()

        if not (characters := re.findall('Character [0-9]+:', content)):
            raise ValueError(f"Data file {self.source_file} does not contain a character list "
                             f"separated by 'Character N:'.")
        if len(characters) < agent_count:
            raise ValueError(
                f"Count of requested Agents ({agent_count}) is higher than 'Character N:' entries "
                f"in {self.source_file} ({len(characters)})"
            )

        agents_scaffold = []
        for i in range(agent_count):
            # create list of dicts with complete characters description picked from file to post to summarizer
            agent_model = next(models)
            start = content.find(characters[i])
            finish = -1 if i == len(characters) - 1 else content.find(characters[i+1])
            agent_description = content[start:finish]
            agents_scaffold.append(
                {'model_id': agent_model, 'prompt': self.summarizer_prompt + agent_description, 'name': '', 'class': ''}
            )

        if self.prompt_extensions:
            # check size of extensions list
            if len(self.prompt_extensions) > len(agents_scaffold):
                print(f"WARNING: list of prompt extensions {len(self.prompt_extensions)} is longer "
                      f"than number of agents {len(agents_scaffold)} - redundant extensions are ignored!")
                # and update ext. before zip to make extensions and agents lists the same length (for async creation)
                self.prompt_extensions = self.prompt_extensions[:len(agents_scaffold)]
            if len(self.prompt_extensions) < len(agents_scaffold):
                print(f"WARNING: list of prompt extensions {len(self.prompt_extensions)} is shorter "
                      f"than number of agents {len(agents_scaffold)} - redundant agents are not enriched! "
                      f"Solve this warning by adding empty items in extension list definition "
                      f"for agent positions without enrichment needs.")
        else:
            # or generate empty extension structure before zip (for async creation)
            self.prompt_extensions = [{'public':'', 'private':''} for _ in range(len(agents_scaffold))]

        async def run_summarizer(enriched_agents):
            # inline async function for calling agent creation asynchronously
            return await asyncio.gather(*[self.process_character_data(ea) for ea in enriched_agents])

        res = await run_summarizer(zip(agents_scaffold, self.prompt_extensions))
        return list(res)
