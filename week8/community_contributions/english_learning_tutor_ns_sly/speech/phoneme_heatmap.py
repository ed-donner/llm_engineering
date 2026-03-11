from speech.phoneme_feedback import PhonemeFeedback


class PhonemeHeatmap:
    """
    Generates phoneme-level pronunciation heatmaps
    for UI visualization.
    """

    def __init__(self):
        self.phoneme = PhonemeFeedback()

    def generate(self, expected_text, spoken_text):

        errors = self.phoneme.compare(
            expected_text,
            spoken_text
        )

        expected_words = expected_text.split()

        heatmap = []

        for word in expected_words:

            if any(e["expected"] in word for e in errors):

                heatmap.append({
                    "word": word,
                    "status": "incorrect"
                })

            else:

                heatmap.append({
                    "word": word,
                    "status": "correct"
                })

        return heatmap