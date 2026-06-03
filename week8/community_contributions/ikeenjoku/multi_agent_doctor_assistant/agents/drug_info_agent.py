"""
Drug Information Agent - Provides detailed medication information
"""

import pandas as pd
from pathlib import Path
from .base_agent import BaseAgent


class DrugInfoAgent(BaseAgent):
    """Agent that provides detailed drug information from Medicine_Details.csv"""

    def __init__(self, vectorstore, llm):
        """
        Initialize drug information agent

        Args:
            vectorstore: Chroma vector database
            llm: Language model for generation
        """
        super().__init__(vectorstore, llm)

        # Load medicine details CSV for direct lookup
        csv_path = Path(__file__).parent.parent / "drugs-knowledge-base" / "Medicine_Details.csv"
        self.medicines_df = pd.read_csv(csv_path)

        # Build drug name index for fast extraction
        self.drug_names = self.medicines_df['Medicine Name'].str.lower().tolist()

    def extract_drug_names(self, query: str) -> list:
        """
        Extract drug names from query using CSV database

        Args:
            query: User query

        Returns:
            list: List of matched drug names (original case)
        """
        query_lower = query.lower()
        found_drugs = []

        for drug in self.drug_names:
            # Match base name (e.g., "augmentin" from "augmentin 625")
            base_name = drug.split()[0]
            if base_name in query_lower or drug in query_lower:
                # Find original case from dataframe
                original = self.medicines_df[
                    self.medicines_df['Medicine Name'].str.lower() == drug
                ]['Medicine Name'].iloc[0]
                found_drugs.append(original)

        return list(set(found_drugs))  # Remove duplicates

    def get_drug_details(self, drug_name: str) -> dict:
        """
        Get detailed information about a specific drug

        Args:
            drug_name: Name of the drug

        Returns:
            dict: Drug details including composition, uses, side effects, etc.
        """
        # Direct CSV lookup
        drug_row = self.medicines_df[
            self.medicines_df['Medicine Name'].str.contains(drug_name, case=False)
        ]

        if drug_row.empty:
            return None

        drug_data = drug_row.iloc[0].to_dict()

        # Enhance with RAG context for additional information
        try:
            rag_docs = self.vectorstore.similarity_search(
                f"{drug_name} composition uses side effects",
                filter={"doc_type": "drug_info"},
                k=2
            )
        except Exception:
            # If filtering fails, do unfiltered search
            rag_docs = self.vectorstore.similarity_search(
                f"{drug_name} composition uses side effects",
                k=2
            )

        return {
            "medicine_name": drug_data['Medicine Name'],
            "composition": drug_data['Composition'],
            "uses": drug_data['Uses'],
            "side_effects": drug_data['Side_effects'],
            "image_url": drug_data['Image URL'],
            "manufacturer": drug_data['Manufacturer'],
            "reviews": {
                "excellent": drug_data['Excellent Review %'],
                "average": drug_data['Average Review %'],
                "poor": drug_data['Poor Review %']
            },
            "rag_context": rag_docs
        }

    def process(self, query: str, **kwargs) -> dict:
        """
        Process query and return drug information

        Args:
            query: User query
            **kwargs: Additional arguments

        Returns:
            dict: Contains found_drugs flag and list of drug details
        """
        drugs = self.extract_drug_names(query)

        if not drugs:
            return {"found_drugs": False, "drugs": []}

        drug_details = []
        for drug in drugs:
            details = self.get_drug_details(drug)
            if details:
                drug_details.append(details)

        return {
            "found_drugs": True,
            "drugs": drug_details
        }
