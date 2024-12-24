from pydantic import BaseModel
from typing import List, Dict, Self
from bs4 import BeautifulSoup
import re
import feedparser
from tqdm import tqdm
import requests
import time

feeds = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
        "https://www.dealnews.com/c39/Computers/?rss=1",
        "https://www.dealnews.com/c238/Automotive/?rss=1",
        "https://www.dealnews.com/f1912/Smart-Home/?rss=1",
        "https://www.dealnews.com/c196/Home-Garden/?rss=1",
       ]

def extract(html_snippet: str) -> str:
    """
    Utilice Beautiful Soup para limpiar este fragmento de HTML y extraer texto útil
    """
    soup = BeautifulSoup(html_snippet, 'html.parser')
    snippet_div = soup.find('div', class_='snippet summary')
    
    if snippet_div:
        description = snippet_div.get_text(strip=True)
        description = BeautifulSoup(description, 'html.parser').get_text()
        description = re.sub('<[^<]+?>', '', description)
        result = description.strip()
    else:
        result = html_snippet
    return result.replace('\n', ' ')

class ScrapedDeal:
    """
    Una clase para representar una oferta recuperada de una fuente RSS
    """
    category: str
    title: str
    summary: str
    url: str
    details: str
    features: str

    def __init__(self, entry: Dict[str, str]):
        """
        Rellene esta instancia en función del diccionario proporcionado
        """
        self.title = entry['title']
        self.summary = extract(entry['summary'])
        self.url = entry['links'][0]['href']
        stuff = requests.get(self.url).content
        soup = BeautifulSoup(stuff, 'html.parser')
        content = soup.find('div', class_='content-section').get_text()
        content = content.replace('\nmore', '').replace('\n', ' ')
        if "Features" in content:
            self.details, self.features = content.split("Features")
        else:
            self.details = content
            self.features = ""

    def __repr__(self):
        """
        Devuelve una cadena para describir esta oferta
        """
        return f"<{self.title}>"

    def describe(self):
        """
        Devuelve una cadena más larga para describir esta transacción y usarla al llamar a un modelo
        """
        return f"Título: {self.title}\nDetalles: {self.details.strip()}\nCaracterísticas: {self.features.strip()}\nURL: {self.url}"

    @classmethod
    def fetch(cls, show_progress : bool = False) -> List[Self]:
        """
        Recuperar todas las ofertas de los canales RSS seleccionados 
        """
        deals = []
        feed_iter = tqdm(feeds) if show_progress else feeds
        for feed_url in feed_iter:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                deals.append(cls(entry))
                time.sleep(0.5)
        return deals

class Deal(BaseModel):
    """
    Una clase para representar un acuerdo con una descripción resumida
    """
    product_description: str
    price: float
    url: str

class DealSelection(BaseModel):
    """
    Una clase para representar una lista de ofertas
    """
    deals: List[Deal]

class Opportunity(BaseModel):
    """
    Una clase para representar una posible oportunidad: un acuerdo en el que estimamos que
    debería costar más de lo que se ofrece
    """
    deal: Deal
    estimate: float
    discount: float