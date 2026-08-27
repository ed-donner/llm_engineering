from .agent import Agent
from ..patient_kb import retrieve_patient_records

class DataRetrievalAgent(Agent):
    """
    Simulates the Retriever in a RAG pipeline. Takes a query (like a patient name)
    and fetches relevant records from the document store.
    """
    name = "Data Retrieval Agent"
    color = Agent.CYAN

    def __init__(self):
        self.log("Initialized Data Retrieval Agent.")

    def retrieve(self, query: str) -> str:
        """Retrieve patient records given a query."""
        self.log(f"Querying vector DB/KB for: '{query}'")
        records = retrieve_patient_records(query)
        self.log("Data retrieval complete.")
        return records
