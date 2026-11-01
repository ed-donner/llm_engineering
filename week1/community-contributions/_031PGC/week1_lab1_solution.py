import os
from dotenv import load_dotenv
from scraper import fetch_website_contents

from openai import OpenAI

msjGeneral = ""

def carga_key():
    isOk = False
    load_dotenv(override=True)
    api_key_openAI = os.getenv('OPENAI_API_KEY')

    # Check the key
    if not api_key_openAI:
        msjGeneral="EL API_KEY de OpenAI no fue encontrada"        
    elif not api_key_openAI.startswith("sk-proj-"):
        msjGeneral="API_KEY encontrada, pero no inicia con sk-proj-"
    elif api_key_openAI.strip() != api_key_openAI:
        msjGeneral="API_KEY encontrada, pero tienes que eliminar espacios"
    else:
        print("API_KEY de OpenAI encontrada.")
        msjGeneral=""
        isOk=True
    return isOk

# Step 1: Create your prompts
system_prompt = """Eres un experto en analizar y pronosticar el resultado de partidos de futbol,
    de manera sarcastica y divertida en español y muy resumido.
    """

user_prompt = """
    Usa el contenido del sitio web si trae datos útiles.
    Si el sitio está vacío o bloqueado, usa tu conocimiento general sobre esos equipos.
    Da un pronóstico probable del partido entre los dos equipos mencionados.
    """

# Step 2: Make the messages list
def getInfo(team1,team2,url):
    """Funcion para definir el mensaje
        parametros:
            team1: equipo local
            team2: equipo visitante
        return
            regresa una lista de dicsionarios
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": url+" "+user_prompt+" "+team1+"vs"+team2}
    ]

# Step 3: 

def ejecutarPronostico(t1, t2, url):
    openai = OpenAI()# crea objeto de OpenAI
    website = fetch_website_contents(url)#funcion que saca el contenido de un website
    response = openai.chat.completions.create(
        model = "gpt-4.1-mini",
        messages = getInfo(t1,t2,website)
    )#llamada a OpenAI
    return response.choices[0].message.content#retoorna el msj devuelto por la 


# Step 4: execuion and result
if carga_key() == False:
    print(msjGeneral);
else:
    print("Bienvenido al pronosticador 2026")
    t1 = input("Ingresa el nombre del equipo local: ")
    t2 = input("Ingresa el nombre del equipo visitante: ")
    print(ejecutarPronostico(t1,t2,"https://www.sofascore.com"))