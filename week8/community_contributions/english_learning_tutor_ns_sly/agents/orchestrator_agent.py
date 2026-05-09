from agents.agent import Agent

from agents.lesson_agent import LessonAgent
from agents.pronunciation_agent import PronunciationAgent
from agents.grammar_agent import GrammarAgent
from agents.rl_curriculum_agent import RLCurriculumAgent
from speech.phoneme_heatmap import PhonemeHeatmap
from speech.mouth_animation import MouthAnimationGuide
from progress.progress_tracker import ProgressTracker


class LearningOrchestrator(Agent):
    """
    Central learning workflow coordinator.
    """

    def __init__(self):

        self.lesson = LessonAgent()
        self.pronunciation = PronunciationAgent()
        self.grammar = GrammarAgent()
        self.rl = RLCurriculumAgent()
        self.heatmap = PhonemeHeatmap()
        self.mouth = MouthAnimationGuide()

        self.progress = ProgressTracker()
        self.name = "LearningOrchestrator"
        self.color = Agent.MAGENTA
        self.log("LearningOrchestrator initialized")


    def run_exercise(self, level, exercise, spoken_text, user_audio, username, category):

        pronunciation = self.pronunciation.evaluate(
            exercise,
            spoken_text,
            user_audio,
            user_audio
        )

        heatmap = self.heatmap.generate(
            exercise,
            spoken_text
        )

        tips = [
            self.mouth.guide(e["expected"])
            for e in pronunciation["errors"]
        ]

        grammar = self.grammar.evaluate(spoken_text)

        # RL curriculum
        new_level = self.rl.next_level(level)
        
        # update progress
        self.progress.update(
            username,
            level,
            category,
            exercise,
            pronunciation["pronunciation_score"],
            pronunciation["accent_score"]
        )
        progress_data = self.progress.get_level_progress(username, level)
        self.log(f"Exercise completed: {exercise}")
        self.log(f"Pronunciation score: {pronunciation['pronunciation_score']}")
        self.log(f"Accent score: {pronunciation['accent_score']}")
        self.log(f"Grammar score: {grammar.grammar_score}")
        self.log(f"Heatmap: {heatmap}")
        self.log(f"Tips: {tips}")
        self.log(f"Recommended level: {new_level}")
        self.log(f"Progress: {progress_data}")

        seen = set()
        unique_tips = []

        for tip in tips:
            instruction = tip["instruction"]
            if instruction not in seen:
                seen.add(instruction)
                unique_tips.append(f"- {instruction}")

        tip_text = "\n".join(unique_tips)
        
        return {

            "exercise": exercise,

            "pronunciation": pronunciation,

            "grammar": grammar,

            "heatmap": heatmap,

            "tips": tip_text,

            "recommended_level": new_level,

            "level_progress": progress_data
        }