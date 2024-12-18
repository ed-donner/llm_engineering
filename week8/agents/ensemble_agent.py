import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

from agents.agent import Agent
from agents.specialist_agent import SpecialistAgent
from agents.frontier_agent import FrontierAgent
from agents.random_forest_agent import RandomForestAgent

class EnsembleAgent(Agent):

    name = "Agente de Conjunto"
    color = Agent.YELLOW
    
    def __init__(self, collection):
        """
        Crea una instancia de Ensemble, creando cada uno de los modelos
        y cargando los pesos del Ensemble
        """
        self.log("Inicializando Agente de Conjunto")
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.random_forest = RandomForestAgent()
        self.model = joblib.load('ensemble_model.pkl')
        self.log("Agente de Conjunto listo")

    def price(self, description: str) -> float:
        """
        Ejecuta este modelo de conjunto
        Pide a cada uno de los modelos que fije el precio del producto
        Luego, utiliza el modelo de regresión lineal para obtener el precio ponderado
        :param description: la descripción de un producto
        :return: una estimación de su precio
        """
        self.log("Ejecutando Agente de Ensemble: colaboración con agentes de bosque aleatorio, especialistas y fronterizos")
        specialist = self.specialist.price(description)
        frontier = self.frontier.price(description)
        random_forest = self.random_forest.price(description)
        X = pd.DataFrame({
            'Specialist': [specialist],
            'Frontier': [frontier],
            'RandomForest': [random_forest],
            'Min': [min(specialist, frontier, random_forest)],
            'Max': [max(specialist, frontier, random_forest)],
        })
        y = self.model.predict(X)[0]
        self.log(f"El Agente de Conjunto ha terminado - predicción ${y:.2f}")
        return y