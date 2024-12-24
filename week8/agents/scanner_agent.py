import os
import json
from typing import Optional, List
from openai import OpenAI
from agents.deals import ScrapedDeal, DealSelection
from agents.agent import Agent


class ScannerAgent(Agent):

    MODEL = "gpt-4o-mini"

    SYSTEM_PROMPT = """Identifica y resume las 5 ofertas más detalladas de una lista, seleccionando las ofertas que tengan la descripción más detallada y de alta calidad y el precio más claro.
    Responde estrictamente en JSON sin explicación, usando este formato. Debes proporcionar el precio como un número derivado de la descripción. Si el precio de una oferta no está claro, no incluyas esa oferta en tu respuesta.
    Lo más importante es que respondas con las 5 ofertas que tengan la descripción del producto más detallada con el precio. No es importante mencionar los términos de la oferta; lo más importante es una descripción detallada del producto.
    Ten cuidado con los productos que se describen como "$XXX de descuento" o "reducidos en $XXX"; este no es el precio real del producto. Solo responde con productos cuando estés muy seguro del precio.
    
    {"deals": [
        {
            "product_description": "Un resumen claro del producto en 4 o 5 oraciones. Los detalles del artículo son mucho más importantes que el motivo por el que es una buena oferta. Evita mencionar descuentos y cupones; céntrate en el artículo en sí. Debe haber un párrafo de texto para cada artículo que elijas.",
            "price": 99.99,
            "url": "the url as provided"
        },
        ...
    ]}"""
    
    USER_PROMPT_PREFIX = """Responde con las 5 ofertas más prometedoras de esta lista, seleccionando aquellas que tengan la descripción del producto más detallada y de mayor calidad y un precio claro que sea mayor a 0.
    Responde estrictamente en JSON, y solo en JSON. Debes reformular la descripción para que sea un resumen del producto en sí, no los términos de la oferta.
    Recuerda responder con un párrafo de texto en el campo product_description para cada uno de los 5 artículos que selecciones.
    Ten cuidado con los productos que se describen como "$XXX de descuento" o "reducidos en $XXX": este no es el precio real del producto. Solo responde con productos cuando estés muy seguro del precio.
    
    Ofertas:
    
    """

    USER_PROMPT_SUFFIX = "\n\nResponda estrictamente en JSON e incluya exactamente 5 transacciones, no más."

    name = "Agente Escáner"
    color = Agent.CYAN

    def __init__(self):
        """
        Configure esta instancia inicializando OpenAI
        """
        self.log("Inicializando Agente Escáner")
        self.openai = OpenAI()
        self.log("El Agente Escáner está listo")

    def fetch_deals(self, memory) -> List[ScrapedDeal]:
        """
        Busque ofertas publicadas en feeds RSS
        Devuelva cualquier oferta nueva que aún no esté en la memoria proporcionada
        """
        self.log("El Agente Escáner está a punto de obtener ofertas de la fuente RSS")
        urls = [opp.deal.url for opp in memory]
        scraped = ScrapedDeal.fetch()
        result = [scrape for scrape in scraped if scrape.url not in urls]
        self.log(f"El Agente de Escáner ha recibido {len(result)} ofertas sin escrapear")
        return result

    def make_user_prompt(self, scraped) -> str:
        """
        Cree un mensaje de usuario para OpenAI basado en las ofertas recopiladas proporcionadas
        """
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += '\n\n'.join([scrape.describe() for scrape in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def scan(self, memory: List[str]=[]) -> Optional[DealSelection]:
        """
        Llama a OpenAI para que te proporcione una lista de ofertas con un alto potencial de buenas descripciones y precios
        Usa StructuredOutputs para asegurarte de que se ajuste a nuestras especificaciones
        :param memory: una lista de URL que representan ofertas ya realizadas
        :return: una selección de buenas ofertas, o None si no hay ninguna
        """
        scraped = self.fetch_deals(memory)
        if scraped:
            user_prompt = self.make_user_prompt(scraped)
            self.log("El agente del escáner llama a OpenAI mediante salida estructurada")
            result = self.openai.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
              ],
                response_format=DealSelection
            )
            result = result.choices[0].message.parsed
            result.deals = [deal for deal in result.deals if deal.price>0]
            self.log(f"El Agente Escáner ha recibido {len(result.deals)} ofertas con precio>0 de OpenAI")
            return result
        return None
                
