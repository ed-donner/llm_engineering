
class MouthAnimationGuide:
    """
    Provides mouth articulation guidance
    for phoneme pronunciation.
    """

    def __init__(self):

        self.mouth_positions = {

            "θ": {
                "instruction": "Place tongue between teeth and blow air.",
                "animation": "tongue_between_teeth.gif"
            },

            "ð": {
                "instruction": "Place tongue between teeth and vibrate voice.",
                "animation": "voiced_th.gif"
            },

            "r": {
                "instruction": "Curl tongue slightly without touching roof.",
                "animation": "r_sound.gif"
            },

            "l": {
                "instruction": "Touch tongue behind upper teeth.",
                "animation": "l_sound.gif"
            }

        }

    def guide(self, phoneme):

        return self.mouth_positions.get(
            phoneme,
            {
                "instruction": "Practice slow articulation.",
                "animation": None
            }
        )