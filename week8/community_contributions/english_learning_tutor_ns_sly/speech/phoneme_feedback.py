
from phonemizer import phonemize


class PhonemeFeedback:
    """
    Highlights phoneme mistakes and generates learning tips.
    """

    def phonemes(self, text):
        print(f"text--phonemes---: {text}")
        return phonemize(
            text,
            language="en-us",
            backend="espeak",
            strip=True
        ).split()

    def compare(self, expected_text, spoken_text):

        exp = self.phonemes(expected_text)
        spk = self.phonemes(spoken_text)

        errors = []

        for i in range(min(len(exp), len(spk))):

            if exp[i] != spk[i]:

                errors.append({
                    "expected": exp[i],
                    "spoken": spk[i],
                    "tip": self.tip(exp[i])
                })

        return errors

    def tip(self, phoneme):

        tips = {
            "θ": "Place tongue between teeth to pronounce TH.",
            "ð": "Voice the TH sound with airflow between teeth.",
            "r": "Curl the tongue slightly without touching roof.",
            "l": "Touch tongue tip behind upper teeth."
        }

        return tips.get(phoneme, "Practice slow articulation.")