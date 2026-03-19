from agents.agent import Agent
from speech.phoneme_feedback import PhonemeFeedback
from speech.accent_scorer import AccentScorer
from agents.agent import Agent


class PronunciationAgent(Agent):
    """
    Evaluates pronunciation accuracy using phoneme alignment.
    """

    def __init__(self):

        self.phoneme = PhonemeFeedback()
        self.accent = AccentScorer()
        self.name = "PronunciationAgent"
        self.color = Agent.RED
        self.log("PronunciationAgent initialized")

    def evaluate(
        self,
        expected_text,
        spoken_text,
        user_audio,
        reference_audio
    ):
        print(f"expected_text: {expected_text}")
        print(f"spoken_text: {spoken_text}")

        phoneme_errors = self.phoneme.compare(
            expected_text,
            spoken_text
        )

        accent_score = self.accent.score(
            user_audio,
            reference_audio
        )

        pronunciation_score = max(0, 100 - len(phoneme_errors) * 5)

        return {

            "pronunciation_score": pronunciation_score,
            "accent_score": accent_score,
            "phoneme_errors": phoneme_errors,
             "errors": phoneme_errors
        }