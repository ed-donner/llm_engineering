import os
import re

from pathlib import Path

from .Helper import helper
from . import AgentFactory
from . import HeroicTools

class Game:
    """
    Game class servers as a main game handler
    """
    def __init__(
            self,
            data_file_path: Path,
            agents_count:int=3,
            user_prompt_extensions=None,
            model_ids:list[str]|str='',
            initial_history:str= '',
            system_prompt:str= ''
    ):
        self.source_file = (data_file_path or
                       os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent, "data", "dnd_characters.txt"))
        self.user_prompt_extensions = user_prompt_extensions
        self.model_ids = model_ids
        self.system_prompt = system_prompt
        self.agents_count = agents_count
        self.agents = []
        self.agents_tools = HeroicTools.HeroicTools(self)
        self.history = initial_history
        self.messages = []
        self.game_expenses = []
        self.history_postponed = {}

        # litellm._turn_on_debug()

    def set_lang(self, lang):
        self.system_prompt = re.sub(r"<rule>All characters must speak in \w+ language</rule>",
                                    f"<rule>All characters must speak in {lang} language</rule>",
                                    self.system_prompt)

    def get_available_tools(self) -> list | None:
        """
        Get tools to use in current Game instance
        :return: list of Tools (strings)
        """
        tools = self.agents_tools.palette_of_options
        return tools

    async def lets_talk(self, turns:int, lang:str):
        """
        Start talking of agents in defined count of turns
        :param turns: number of turns to be played
        :param lang: language name (English or Czech)
        """
        self.set_lang(lang)
        factory = AgentFactory.AgentFactory(assigned_game=self, source_file=self.source_file,
                                            prompt_extensions=self.user_prompt_extensions)
        self.agents = await factory.generate(models=self.model_ids, agent_count=self.agents_count)

        async for _, piece_of_text in helper.pretend_streaming(self.history):
            yield _, piece_of_text

        for agent in self.agents:
            print(f"Let agent {agent.name} meet the team.")
            agent.meet_heroic_team(self.agents, self.system_prompt)
            agent.meet_heroic_actions()

        i = 0
        while i < turns:
            if i > turns:
                # test of early game ending (chapter/scene solved and so there is no need for further actions)
                break
            for agent in self.agents:
                print(f"Turn #{i + 1} has started with agent {agent.name}.")
                msg = {'role': 'assistant', 'content': ''}
                if self.history_postponed:
                    if agent.ID == self.history_postponed.get('show_before'):
                        self.history += self.history_postponed['msg'] + "\n\n"
                    if team_msg := self.history_postponed.get('team_msg'):
                        # team message is sent to all agents
                        for a in self.agents:
                            a.listen({'role': 'user', 'content': team_msg})
                    if remaining_turns := self.history_postponed.get('turns_to_end'):
                        # decrease count of turns to stop earlier
                        turns = i + remaining_turns if i + remaining_turns < turns else turns
                        print(f"Game-stop event encountered (task solved), game is going to end in turn {turns+1}.")
                    # clear history
                    self.history_postponed = {}
                for spending, a_chunk in agent.talk():
                    msg['content'] += a_chunk
                    self.history += f"{a_chunk}"
                    updated = False
                    for item in self.game_expenses:
                        if item['name'] == spending.get('name'):
                            item['expenses'] = spending.get('expenses')
                            updated = True
                            break
                    if not updated:
                        self.game_expenses.append(spending)
                    yield self.game_expenses, self.history
                self.history += '\n\n'

                if msg.get('content'):
                    for teammate in [teammate for teammate in self.agents if teammate.ID != agent.ID]:
                        teammate.listen(msg.copy())
            i += 1


