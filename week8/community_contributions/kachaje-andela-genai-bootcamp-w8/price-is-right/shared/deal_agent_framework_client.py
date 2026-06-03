import sys
import os
# Add the shared directory to the path
shared_path = os.path.dirname(__file__)
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

import os
import sys
import logging
import json
import httpx
from typing import List, Optional
from agents.deals import Opportunity

BG_BLUE = '\033[44m'
WHITE = '\033[37m'
RESET = '\033[0m'

def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [Agents] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

class DealAgentFrameworkClient:

    MEMORY_FILENAME = "memory.json"

    def __init__(self):
        init_logging()
        self.memory = self.read_memory()

    def read_memory(self) -> List[Opportunity]:
        if os.path.exists(self.MEMORY_FILENAME):
            with open(self.MEMORY_FILENAME, "r") as file:
                data = json.load(file)
            opportunities = [Opportunity(**item) for item in data]
            return opportunities
        return []

    def write_memory(self) -> None:
        data = [opportunity.model_dump() for opportunity in self.memory]
        with open(self.MEMORY_FILENAME, "w") as file:
            json.dump(data, file, indent=2)

    def log(self, message: str):
        text = BG_BLUE + WHITE + "[Agent Framework] " + message + RESET
        logging.info(text)

    async def run(self) -> List[Opportunity]:
        self.log("Kicking off Planning Agent")
        async with httpx.AsyncClient() as client:
            # Extract URLs from memory for the planning agent
            memory_urls = [opp.deal.url for opp in self.memory]
            result = await client.post("http://localhost:8006/plan", json={"memory": memory_urls})
            
            if result.status_code == 200:
                opportunity_data = result.json()
                if opportunity_data:
                    opportunity = Opportunity(**opportunity_data)
                    self.memory.append(opportunity)
                    self.write_memory()
                    self.log(f"Planning Agent has completed and returned: {opportunity}")
                else:
                    self.log("Planning Agent completed with no new opportunities")
            else:
                self.log(f"Planning Agent failed with status {result.status_code}")
        
        return self.memory

if __name__=="__main__":
    import asyncio
    asyncio.run(DealAgentFrameworkClient().run())
