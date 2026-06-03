# ===========================================
#  MINI CHATBOT (ONLINE + LOCAL) CON CONTEXTO
#  - Opción 1: OpenAI online (gpt-4.1-mini)
#  - Opción 2: Ollama local (deepseek-r1:8b)
#  - Arranca Ollama automáticamente si no está activo
# ===========================================

# -----------------------------
# IMPORTS
# -----------------------------

import os                 # Para leer variables de entorno
import time               # Para esperas controladas
import subprocess         # Para arrancar procesos (ollama serve)
import requests           # Para comprobar si Ollama está vivo (HTTP ping)
from dotenv import load_dotenv  # Para cargar .env
from openai import OpenAI       # Cliente moderno OpenAI (sirve también con Ollama compatible)

# -----------------------------
# CARGA DE ENTORNO
# -----------------------------

load_dotenv(override=False)

# -----------------------------
# CONFIG POR DEFECTO
# -----------------------------

ONLINE_MODEL = "gpt-4.1-mini"
LOCAL_MODEL = "deepseek-r1:8b"

# Endpoints por defecto
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/v1"

# -----------------------------
# FUNCIONES OLLAMA
# -----------------------------

def ollama_esta_activo(url: str = OLLAMA_BASE_URL) -> bool:
    """
    Comprueba si el servidor de Ollama está respondiendo en la URL base.
    Devuelve True si responde (HTTP 200), False si no.
    """
    try:
        r = requests.get(url, timeout=1)
        return r.status_code == 200
    except requests.RequestException:
        return False


def asegurar_ollama() -> None:
    """
    Arranca 'ollama serve' si Ollama no está ya activo.
    Espera hasta 10 segundos a que el servidor responda.
    """
    # Si ya está activo, no hacemos nada
    if ollama_esta_activo():
        print("✔ Ollama ya está activo.")
        return

    # Si no está activo, intentamos arrancarlo
    print("▶ Arrancando Ollama (ollama serve)...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        raise RuntimeError(
            "No se encontró el comando 'ollama'. "
            "Instala Ollama y asegúrate de que está en el PATH."
        )

    # Esperamos a que esté listo (máx 10 s)
    for _ in range(10):
        if ollama_esta_activo():
            print("✔ Ollama listo.")
            return
        time.sleep(1)

    raise RuntimeError("❌ Ollama no respondió tras intentar arrancarlo.")

# -----------------------------
# SELECCIÓN DE BACKEND
# -----------------------------

def elegir_backend():
    """
    Permite elegir entre:
      1) Online (OpenAI)
      2) Local (Ollama)
    Devuelve (client, model_name, backend_name).
    """
    print("Selecciona backend:")
    print(f"  1) Online (OpenAI) -> {ONLINE_MODEL}")
    print(f"  2) Local (Ollama)  -> {LOCAL_MODEL}")
    opcion = input("Opción (1/2): ").strip()

    # --------
    # ONLINE
    # --------
    if opcion == "1":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()

        # Validamos API key
        if not api_key:
            raise ValueError(
                "Has elegido ONLINE pero falta OPENAI_API_KEY en el entorno/.env."
            )

        # Creamos cliente para OpenAI online (sin base_url)
        client = OpenAI(api_key=api_key)

        return client, ONLINE_MODEL, "ONLINE"

    # --------
    # LOCAL
    # --------
    elif opcion == "2":
        # Aseguramos que Ollama esté corriendo
        asegurar_ollama()

        # Cliente apuntando a Ollama
        client = OpenAI(
            base_url=OLLAMA_API_URL,
            api_key="ollama"  # Ollama no valida key; el SDK exige un valor
        )

        return client, LOCAL_MODEL, "LOCAL (Ollama)"

    else:
        raise ValueError("Opción inválida. Debe ser '1' o '2'.")

# -----------------------------
# MAIN
# -----------------------------

def main():
    # Elegimos backend y modelo
    client, model_name, backend_name = elegir_backend()

    # Contexto inicial (memoria)
    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres un asistente técnico, claro y preciso. "
                "Respondes en español."
            ),
        }
    ]

    print("\n=== Chatbot iniciado ===")
    print(f"Backend: {backend_name}")
    print(f"Modelo:  {model_name}")
    print("Escribe 'salir' para terminar.\n")

    # Bucle principal
    while True:
        entrada = input("Tú: ")

        if entrada.strip().lower() == "salir":
            print("Asistente: ¡Hasta luego!")
            break

        # Guardamos mensaje de usuario
        mensajes.append({"role": "user", "content": entrada})

        # Llamada al modelo
        respuesta = client.chat.completions.create(
            model=model_name,
            messages=mensajes
        )

        # Extraemos texto
        texto = respuesta.choices[0].message.content

        # Mostramos
        print(f"Asistente: {texto}\n")

        # Guardamos respuesta en contexto
        mensajes.append({"role": "assistant", "content": texto})

# -----------------------------
# ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    main()
