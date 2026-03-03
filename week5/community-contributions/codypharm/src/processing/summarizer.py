from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class PharmaSummarizer:
    def __init__(self):
        self.client = OpenAI()
        
        # Section-specific instructions matching your TARGET_SECTIONS
        self.section_instructions = {
            "indications_and_usage": (
                "Summarize ONLY the medical conditions, diseases, or purposes this drug treats. "
                "Focus on: what illness/condition is treated, which patient populations qualify. "
                "DO NOT mention dosages, administration, or how to take the drug."
            ),
            "dosage_and_administration": (
                "Summarize ONLY the dosing amounts, frequency, timing, and how to administer. "
                "Focus on: mg per dose, times per day, route (oral/IV/topical), special instructions. "
                "DO NOT mention what the drug treats or why it's prescribed."
            ),
            "warnings": (
                "Summarize ONLY the important safety warnings and precautions. "
                "Focus on: serious risks, monitoring requirements, patient populations needing caution. "
                "DO NOT mention contraindications (absolute prohibitions) or side effects."
            ),
            "boxed_warning": (
                "Summarize ONLY the FDA's most serious black box warnings. "
                "Focus on: life-threatening risks, mortality data, specific high-risk populations. "
                "Maintain the urgency and severity of the warning."
            ),
            "adverse_reactions": (
                "Summarize ONLY the side effects and adverse events observed. "
                "Focus on: specific symptoms, incidence rates/percentages, serious vs common reactions. "
                "DO NOT mention warnings, contraindications, or precautions."
            ),
            "contraindications": (
                "Summarize ONLY the absolute prohibitions - who must NEVER take this drug. "
                "Focus on: specific medical conditions, allergies, or situations that prohibit use. "
                "DO NOT mention warnings, precautions, or potential risks."
            ),
            "precautions": (
                "Summarize ONLY the precautionary measures and monitoring needed. "
                "Focus on: what to watch for, lab monitoring, dose adjustments, patient counseling. "
                "DO NOT mention absolute contraindications or common side effects."
            ),
            "drug_interactions": (
                "Summarize ONLY how this drug interacts with other medications or substances. "
                "Focus on: specific drug names, interaction mechanism, clinical significance, dose adjustments. "
                "DO NOT mention general warnings or contraindications."
            ),
            "use_in_specific_populations": (
                "Summarize ONLY the guidance for special patient groups. "
                "Focus on: pregnancy/lactation safety, pediatric use, geriatric considerations, renal/hepatic impairment. "
                "DO NOT mention general dosing or standard administration."
            )
        }

    def summarize(self, text: str, section: str) -> str:
        """
        Create a focused summary for semantic search.
        
        Args:
            text: Full section text
            section: Section name from TARGET_SECTIONS
        
        Returns:
            Concise, section-focused summary with section prefix
        """
        # Normalize section name
        section_key = section.lower().replace(" ", "_")
        
        # Get section-specific instruction
        specific_instruction = self.section_instructions.get(
            section_key,
            f"Summarize the key points from the {section} section in 2-3 sentences."
        )
        
        # Truncate very long texts
        text_sample = text[:2500] if len(text) > 2500 else text
        
        prompt = f"""You are a clinical pharmacist creating a focused summary for semantic search.

                SECTION TYPE: {section}

                STRICT INSTRUCTIONS:
                {specific_instruction}

                FORMATTING RULES:
                - Maximum 2-3 sentences
                - Use precise medical terminology
                - Be extremely specific to this section's scope
                - Do not mix information from other section types

                TEXT TO SUMMARIZE:
                {text_sample}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Add section prefix for stronger semantic distinction
        return f"[{section.upper()}] {summary}"

    def batch_summarize(self, chunks: list) -> list[str]:
        """
        Summarize multiple chunks efficiently.
        
        Args:
            chunks: List of Chunk objects with page_content and metadata
        
        Returns:
            List of summaries in same order
        """
        summaries = []
        for chunk in chunks:
            section = chunk.metadata.get("section", "unknown")
            summary = self.summarize(chunk.page_content, section)
            summaries.append(summary)
        return summaries