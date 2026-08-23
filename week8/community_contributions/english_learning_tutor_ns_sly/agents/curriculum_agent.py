from agents.agent import Agent

class CurriculumAgent(Agent):
    """
    Adaptive learning agent that upgrades or downgrades
    user difficulty based on performance metrics.
    """

    LEVELS = [
        "Beginner",
        "Intermediate",
        "Advanced",
        "Native"
    ]

    def __init__(self):

        self.upgrade_threshold = 85
        self.downgrade_threshold = 40
        self.name = "CurriculumAgent"
        self.color = Agent.GREEN
        self.log("CurriculumAgent initialized")

    def evaluate(self, level, pronunciation, grammar, accent):

        avg_score = (pronunciation + grammar + accent) / 3

        idx = self.LEVELS.index(level)

        if avg_score > self.upgrade_threshold and idx < 3:
            return self.LEVELS[idx + 1]

        if avg_score < self.downgrade_threshold and idx > 0:
            return self.LEVELS[idx - 1]

        return level