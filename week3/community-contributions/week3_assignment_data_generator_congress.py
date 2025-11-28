# %% [markdown]
''' Este script permite **generar datos sintéticos realistas** para analizar la cobertura mediática de eventos (congresos, conferencias, foros) utilizando **modelos de lenguaje avanzados** (GPT-4 y Claude).
### Tres tipos de datasets generables:

1. **Eventos**
   - Información básica del evento: nombre, fechas, ubicación, asistencia esperada
   - Ejemplo: "Congreso de Turismo Sostenible 2025 en Valencia"

2. **Cobertura Mediática**
   - Artículos de prensa sobre el evento
   - Incluye: título, resumen, fuente, sentimiento, alcance
   - Fuentes variadas: nacionales, regionales, internacionales, especializadas

3. **Menciones en Redes Sociales**
   - Posts de Twitter, Facebook, Instagram, LinkedIn, TikTok
   - Métricas de engagement: likes, shares, comentarios, alcance
   - Análisis de sentimiento y hashtags
'''


import os
import json
import tempfile
from datetime import datetime, timedelta
from dateutil import parser as dateparser
from dotenv import load_dotenv

import pandas as pd
import gradio as gr
from faker import Faker
import openai
from anthropic import Anthropic

# Configuración inicial
load_dotenv()
fake = Faker()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MAX_RECORDS_ALLOWED = 5

# Configuración de clientes
openai.api_key = OPENAI_API_KEY
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================================
# UTILIDADES
# ============================================================================

def extract_json_from_text(text: str) -> str:
    """Extrae JSON array de respuesta LLM, manejando bloques ```json```."""
    if not text:
        raise ValueError("Respuesta vacía del modelo")
    
    # Remover bloques de código
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    
    # Buscar inicio del array
    idx = text.find('[')
    if idx >= 0:
        text = text[idx:]
    
    return text.strip()

def parse_json_safe(text: str) -> list:
    """Parsea JSON array con manejo robusto de errores."""
    try:
        json_str = extract_json_from_text(text)
        data = json.loads(json_str)
        if not isinstance(data, list):
            raise ValueError("El JSON no es un array")
        return data
    except Exception as e:
        snippet = text[:500] if text else ""
        raise ValueError(f"Error parseando JSON: {e}\nSnippet: {snippet}")

def save_to_csv(df: pd.DataFrame) -> str:
    """Guarda DataFrame en archivo temporal CSV."""
    fd, path = tempfile.mkstemp(suffix=".csv", prefix="synthetic_")
    os.close(fd)
    df.to_csv(path, index=False)
    return path

# ============================================================================
# PROMPTS
# ============================================================================

PROMPTS = {
    "events": """Genera exactamente {n} eventos en formato JSON array. Cada objeto debe tener:
- event_id: string (EVT-XXXXXX)
- event_name: string
- start_date: ISO 8601
- end_date: ISO 8601
- location_city: string
- main_topic: string
- expected_attendance: integer

Contexto: Tipo={event_type}, Fechas={start_iso} a {end_iso}, Location={location}, Asistencia={attendance}, Idioma={language}

Devuelve SOLO el array JSON, sin texto adicional.""",

    "media_coverage": """Genera exactamente {n} artículos en formato JSON array. Cada objeto debe tener:
- article_id, event_id, published_at (ISO 8601), source_name, source_type (national/regional/international)
- title, summary (2 oraciones), language, sentiment_score (-1 a 1), stance (positive/neutral/negative)
- reach (integer), topic_tags (array), entities (array)

Contexto: Evento={event_name} ({event_id}), Tipo={event_type}, Fechas={start_iso} a {end_iso}, Location={location}, Source={source_type}, Idioma={language}

Devuelve SOLO el array JSON con variedad y coherencia temporal.""",

    "social_mentions": """Genera exactamente {n} posts en formato JSON array. Cada objeto debe tener:
- post_id, event_id, timestamp (ISO 8601), platform (twitter/facebook/instagram/linkedin/tiktok), handle
- text, language, sentiment_score (-1 a 1), stance (positive/neutral/negative)
- likes, shares, replies, reach (integers), hashtags (array), entities (array)

Contexto: Evento={event_name} ({event_id}), Tipo={event_type}, Fechas={start_iso} a {end_iso}, Location={location}, Idioma={language}

Devuelve SOLO el array JSON con variedad en plataformas y engagement natural."""
}

# ============================================================================
# LLAMADAS A MODELOS
# ============================================================================

def call_openai(prompt: str, api_key: str, model: str = "gpt-4o-mini", temp: float = 0.7) -> tuple:
    """Llama a OpenAI y extrae texto de respuesta."""
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=temp
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"OpenAI error: {e}"

def call_anthropic(prompt: str, api_key: str, model: str = "claude-3-5-haiku-latest", temp: float = 0.7) -> tuple:
    """Llama a Anthropic y extrae texto de respuesta."""
    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}]
        )
        return "".join(block.text for block in response.content if hasattr(block, "text")), None
    except Exception as e:
        return None, f"Anthropic error: {e}"

# ============================================================================
# GENERACIÓN
# ============================================================================

def generate_dataset(provider: str, dataset_type: str, n: int, context: dict, 
                    language: str, api_key: str = None, temp: float = 0.7) -> tuple:
    """Genera dataset sintético usando LLM especificado."""
    
    if not (0 < n <= MAX_RECORDS_ALLOWED):
        raise ValueError(f"n debe estar entre 1 y {MAX_RECORDS_ALLOWED}")
    
    # Preparar prompt
    prompt = PROMPTS[dataset_type].format(n=n, language=language, **context)
    
    # Seleccionar modelo y API key
    models = {"openai": "gpt-4o-mini", "anthropic": "claude-3-5-haiku-latest"}
    model = models.get(provider)
    
    if not api_key:
        api_key = OPENAI_API_KEY if provider == "openai" else ANTHROPIC_API_KEY
    
    # Llamar modelo
    call_fn = call_openai if provider == "openai" else call_anthropic
    text, err = call_fn(prompt, api_key, model, temp)
    
    if err:
        return None, err
    
    # Parsear respuesta
    try:
        records = parse_json_safe(text)
        return records, None
    except Exception as e:
        return None, str(e)

# ============================================================================
# INTERFAZ GRADIO
# ============================================================================

def run_generation(provider, event_type, start_date, end_date, location, 
                  attendance, source_type, language, dataset_type, n_items, api_key_input):
    """Handler principal para generación desde UI."""
    
    try:
        n_items = int(n_items)
        if not (0 < n_items <= MAX_RECORDS_ALLOWED):
            return "", f"Número debe estar entre 1 y {MAX_RECORDS_ALLOWED}", None
        
        # Parsear fechas
        start_dt = dateparser.parse(start_date)
        end_dt = dateparser.parse(end_date)
        
        # Preparar contexto
        event_id = f"EVT-{fake.unique.random_number(digits=6)}"
        context = {
            "event_id": event_id,
            "event_name": f"{event_type} - {location}",
            "start_iso": start_dt.isoformat(),
            "end_iso": end_dt.isoformat(),
            "location": location,
            "attendance": int(attendance),
            "event_type": event_type,
            "source_type": source_type
        }
        
        # Mapear idioma
        lang_map = {"español": "español", "ingles": "english"}
        lang = lang_map.get(language.lower(), language)
        
        # Generar datos
        records, err = generate_dataset(
            provider=provider.lower(),
            dataset_type=dataset_type,
            n=n_items,
            context=context,
            language=lang,
            api_key=api_key_input.strip() or None
        )
        
        if err:
            return "", f"Error: {err}", None
        
        # Crear DataFrame y guardar
        df = pd.DataFrame(records)
        csv_path = save_to_csv(df)
        preview = df.head(20).to_html(index=False)
        status = f"✅ Generados {len(df)} registros con {provider} ({lang})"
        
        return preview, status, csv_path
        
    except Exception as e:
        return "", f"Error: {str(e)}", None

# ============================================================================
# UI
# ============================================================================

with gr.Blocks(title="Generador Sintético de Datos") as demo:
    gr.Markdown("# Generador Sintético de Datos Mediáticos de Eventos")
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### Configuración")
            provider = gr.Radio(["openai", "anthropic"], value="openai", label="Proveedor LLM")
            api_key_input = gr.Textbox(label="API Key (opcional)", type="password", 
                                      placeholder="Deja vacío para usar .env")
            
            gr.Markdown("### Parámetros del Evento")
            event_type = gr.Dropdown(
                ["Congreso de odontólogos", "Congreso de diabetes", "Congreso de energía", 
                 "Congreso de movilidad urbana", "Foro empresarial"],
                value="Congreso de turismo", label="Tipo de evento"
            )
            start_date = gr.Textbox(value=datetime.now().date().isoformat(), label="Fecha inicio (YYYY-MM-DD)")
            end_date = gr.Textbox(value=(datetime.now() + timedelta(days=2)).date().isoformat(), 
                                 label="Fecha fin (YYYY-MM-DD)")
            location = gr.Dropdown(
                ["Valencia", "Sydney", "Ljubljana", "Larissa", "Heidelberg", "Paris", "London", "New York"],
                value="Valencia", label="Ciudad"
            )
            attendance = gr.Number(value=300, label="Asistencia esperada", precision=0)
            
            gr.Markdown("### Parámetros de Generación")
            source_type = gr.Radio(
                ["national", "regional", "international"],
                value="national", label="Tipo de fuente (media)"
            )
            language = gr.Radio(["español", "ingles"], value="español", label="Idioma")
            dataset_type = gr.Radio(
                ["events", "media_coverage", "social_mentions"],
                value="media_coverage", label="Tipo de dataset"
            )
            n_items = gr.Slider(1, MAX_RECORDS_ALLOWED, value=5, step=1, 
                              label=f"Cantidad de registros (máx {MAX_RECORDS_ALLOWED})")
            
            generate_btn = gr.Button("Generar Dataset", variant="primary")
        
        with gr.Column(scale=3):
            gr.Markdown("### Resultados")
            preview = gr.HTML("<i>Preview aparecerá aquí tras generar...</i>")
            status = gr.Textbox(label="Estado", interactive=False)
            csv_file = gr.File(label="Descargar CSV")
    
    generate_btn.click(
        fn=run_generation,
        inputs=[provider, event_type, start_date, end_date, location, attendance, 
                source_type, language, dataset_type, n_items, api_key_input],
        outputs=[preview, status, csv_file]
    )

if __name__ == "__main__":
    demo.launch(share=False, debug=True)