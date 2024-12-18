# imports

import os
import re
import math
import json
from typing import List, Dict
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import chromadb
from items import Item
from testing import Tester
from agents.agent import Agent


class FrontierAgent(Agent):

    name = "Agente Frontera"
    color = Agent.BLUE

    MODEL = "gpt-4o-mini"
    
    def __init__(self, collection):
        """
        Configura esta instancia conectándose a OpenAI, al almacén de datos Chroma,
        y configurando el modelo de codificación vectorial
        """
        self.log("Inicializando el Agente Frontera")
        self.openai = OpenAI()
        self.collection = collection
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.log("Agente Frontera listo")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        """
        Crea un contexto que se puede insertar en el mensaje
        :param similars: productos similares al que se está estimando
        :param prices: precios de los productos similares
        :return: texto para insertar en el mensaje que proporciona contexto
        """
        message = "Para brindar algo de contexto, aquí hay algunos otros elementos que podrían ser similares al elemento que necesita estimar.\n\n"
        for similar, price in zip(similars, prices):
            message += f"Producto potencialmente relacionado:\n{similar}\nEl precio es ${price:.2f}\n\n"
        return message

    def messages_for(self, description: str, similars: List[str], prices: List[float]) -> List[Dict[str, str]]:
        """
        Crea la lista de mensajes que se incluirán en una llamada a OpenAI
        Con el sistema y el indicador de usuario
        :param description: una descripción del producto
        :param similars: productos similares a este
        :param prices: precios de productos similares
        :return: la lista de mensajes en el formato esperado por OpenAI
        """
        system_message = "Estimas los precios de los artículos. Respondes solo con el precio, sin explicaciones."
        user_prompt = self.make_context(similars, prices)
        user_prompt += "Y ahora va la pregunta para ti:\n\n"
        user_prompt += "¿Cuánto cuesta este producto?\n\n" + description
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "El precio es $"}
        ]

    def find_similars(self, description: str):
        """
        Devuelve una lista de elementos similares al indicado buscando en el almacén de datos de Chroma
        """
        self.log("Frontier Agent está realizando una búsqueda RAG en el almacén de datos de Chroma para encontrar 5 productos similares")
        vector = self.model.encode([description])
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results['documents'][0][:]
        prices = [m['price'] for m in results['metadatas'][0][:]]
        self.log("El Agente Frontera ha encontrado productos similares")
        return documents, prices

    def get_price(self, s) -> float:
        """
        Una utilidad que extrae un número de punto flotante de un string
        """
        s = s.replace('$','').replace(',','')
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Realizar una llamada a OpenAI para estimar el precio del producto descrito,
        buscando 5 productos similares e incluyéndolos en el mensaje para dar contexto
        :param description: una descripción del producto
        :return: una estimación del precio
        """
        documents, prices = self.find_similars(description)
        self.log("El Agente Frontera está a punto de llamar a OpenAI con un contexto que incluye 5 productos similares")
        response = self.openai.chat.completions.create(
            model=self.MODEL, 
            messages=self.messages_for(description, documents, prices),
            seed=42,
            max_tokens=5
        )
        reply = response.choices[0].message.content
        result = self.get_price(reply)
        self.log(f"El Agente Frontera ha terminado - predicción ${result:.2f}")
        return result
        