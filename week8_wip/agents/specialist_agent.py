import modal

class SpecialistAgent:

    def __init__(self):
        Pricer = modal.Cls.lookup("pricer-service", "Pricer")
        self.pricer = Pricer()
        
    def price(self, description: str) -> float:
        return self.pricer.price.remote(description)
