
"""
Drug Interaction Checker Agent 
"""

import pandas as pd
from pathlib import Path
from .base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class DrugInteractionChecker(BaseAgent):
    """Agent that checks for drug-drug interactions using indexed lookup"""

    def __init__(self, vectorstore, llm):
        """
        Initialize drug interaction checker with indexed lookup

        Args:
            vectorstore: Chroma vector database
            llm: Language model for generation
        """
        super().__init__(vectorstore, llm)

        # Load interactions CSV
        csv_path = Path(__file__).parent.parent / "drugs-knowledge-base" / "db_drug_interactions.csv"
        print("Loading drug interactions database...")
        interactions_df = pd.read_csv(csv_path)
        print(f"Loaded {len(interactions_df)} interactions")

        # Build indexed lookup dictionary for O(1) access
        # Key: frozenset of two normalized drug names
        # Value: interaction description
        self.interaction_index = {}

        print("Building interaction index...")
        for _, row in interactions_df.iterrows():
            drug1 = row['Drug 1'].strip().lower()
            drug2 = row['Drug 2'].strip().lower()
            description = row['Interaction Description']

            # Create bidirectional key (frozenset handles both directions)
            key = frozenset([drug1, drug2])
            self.interaction_index[key] = description

        print(f"✓ Interaction index built with {len(self.interaction_index)} unique pairs")

    def _normalize_drug_name(self, drug_name: str) -> str:
        """Normalize drug name for matching"""
        # Get base name (first word) and lowercase
        return drug_name.strip().split()[0].lower()

    def check_interactions(self, drugs: list) -> list:
        """
        Check for interactions between drugs using fast indexed lookup

        Args:
            drugs: List of drug names

        Returns:
            list: List of interactions found
        """
        if len(drugs) < 2:
            return []

        interactions_found = []

        for i, drug1 in enumerate(drugs):
            for drug2 in drugs[i+1:]:
                # Normalize drug names
                drug1_normalized = self._normalize_drug_name(drug1)
                drug2_normalized = self._normalize_drug_name(drug2)

                # Fast O(1) lookup in index
                key = frozenset([drug1_normalized, drug2_normalized])

                if key in self.interaction_index:
                    description = self.interaction_index[key]

                    # Use LLM to analyze severity (keep this part)
                    analysis_prompt = f"""Analyze this drug interaction:

Drugs: {drug1} and {drug2}
Interaction: {description}

Provide:
1. Severity level (Minor/Moderate/Major/Contraindicated)
2. Clinical recommendation
3. Brief explanation for patient

Format:
SEVERITY: [level]
RECOMMENDATION: [what to do]
EXPLANATION: [patient-friendly explanation]"""

                    response = self.llm.invoke([HumanMessage(content=analysis_prompt)])

                    interactions_found.append({
                        "drug1": drug1,
                        "drug2": drug2,
                        "description": description,
                        "analysis": response.content
                    })

        return interactions_found

    def process(self, query: str, drugs: list = None, **kwargs) -> dict:
        """
        Process query and check for interactions

        Args:
            query: User query
            drugs: List of drug names (optional)
            **kwargs: Additional arguments

        Returns:
            dict: Contains has_interactions flag and list of interactions
        """
        if drugs is None or len(drugs) < 2:
            return {"has_interactions": False, "interactions": []}

        interactions = self.check_interactions(drugs)

        return {
            "has_interactions": len(interactions) > 0,
            "interactions": interactions,
            "drugs_checked": drugs
        }
