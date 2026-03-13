import numpy as np
from agents.agent import Agent


class RLCurriculumAgent(Agent):
    """
    Reinforcement Learning agent for
    dynamic curriculum optimization.
    """

    LEVELS = [
        "Beginner",
        "Intermediate",
        "Advanced",
        "Native"
    ]

    def __init__(self):

        self.q_table = np.zeros((4, 4))

        self.learning_rate = 0.1
        self.discount = 0.9
        self.name = "RLCurriculumAgent"
        self.color = Agent.CYAN
        self.log("RLCurriculumAgent initialized")

    def state_index(self, level):

        return self.LEVELS.index(level)

    def action(self, level):

        idx = self.state_index(level)

        return np.argmax(self.q_table[idx])

    def update(self, level, action, reward):

        idx = self.state_index(level)

        self.q_table[idx][action] += self.learning_rate * (
            reward
            + self.discount * np.max(self.q_table[action])
            - self.q_table[idx][action]
        )

    def next_level(self, level):

        action = self.action(level)

        return self.LEVELS[action]