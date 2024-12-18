# imports

import os
import re
from typing import List
from sentence_transformers import SentenceTransformer
import joblib
from agents.agent import Agent

class RandomForestAgent(Agent):

    name = "Agente de Bosque Aleatorio"
    color = Agent.MAGENTA

    def __init__(self):
        """
        Inicialice este objeto cargando los pesos del modelo guardado
        y el modelo de codificación vectorial SentenceTransformer
        """
        self.log("El Agente de Bosque Aleatorio se está inicializando")
        self.vectorizer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.model = joblib.load('random_forest_model.pkl')
        self.log("El Agente de Bosque Aleatorio está listo")

    def price(self, description: str) -> float:
        """
        Inicializa este objeto cargando los pesos del modelo guardado
        Usa un modelo de Bosque aleatorio para estimar el precio del artículo descrito
        :param description: el producto que se va a estimar
        :return: el precio en coma flotante
        """        
        self.log("El Agente de Bosque aleatorio ha empezado una predicción")
        vector = self.vectorizer.encode([description])
        result = max(0, self.model.predict(vector)[0])
        self.log(f"El agente de Random Forest ha terminado - predicción ${result:.2f}")
        return result