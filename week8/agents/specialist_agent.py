import modal
from agents.agent import Agent


class SpecialistAgent(Agent):
    """
    Un agente que ejecuta nuestro LLM optimizado que se ejecuta de forma remota en Modal
    """

    name = "Agente Especialista"
    color = Agent.RED

    def __init__(self):
        """
        Configura este agente creando una instancia de la clase modal
        """
        self.log("El agente especialista se está inicializando: se está conectando al modal")
        Pricer = modal.Cls.lookup("pricer-service", "Pricer")
        self.pricer = Pricer()
        self.log("El agente especialista está listo")
        
    def price(self, description: str) -> float:
        """
        Realizar una llamada remota para devolver la estimación del precio de este artículo
        """
        self.log("El agente especialista está llamando al modelo remoto ajustado")
        result = self.pricer.price.remote(description)
        self.log(f"El Agente especialista ha terminado - predicción ${result:.2f}")
        return result
