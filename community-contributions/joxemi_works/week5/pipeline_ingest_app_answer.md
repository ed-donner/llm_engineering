# Pipeline completo (modo dummie): `ingest` -> `app/chat` -> `answer` (2 iteraciones)

## 1) `ingest.py` (se ejecuta antes, una sola vez)

Objetivo: preparar la base vectorial (`vector_db`) para que luego se pueda buscar contexto semántico.

### Flujo
1. Lee documentos `.md` desde `week5/knowledge-base`.
2. Añade metadata `doc_type` según la carpeta.
3. Parte los documentos en chunks (`chunk_size=500`, `chunk_overlap=200`).
4. Genera embeddings con `text-embedding-3-large`.
5. Guarda todo en Chroma: `week5/vector_db`.

### Resultado
- Queda lista la base vectorial persistida en disco.
- `answer.py` la usará en tiempo real para recuperar contexto.

---

## 2) `app.py` + `chat()` + `answer_question()` (runtime)

Idea clave:
- `app.py` = interfaz Gradio.
- `chat()` = orquestador por cada mensaje.
- `answer_question()` = RAG interno (recupera contexto + responde con LLM).

### Hook principal en `app.py`
```python
message.submit(
    put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]
).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])
```

---

## 3) Iteración 1 (primer mensaje)

### Estado inicial
```python
history = []
```

### Paso a paso
1. Usuario escribe:
```python
message = "Hola"
```

2. Se ejecuta:
```python
put_message_in_chatbot(message, history)
```
Entradas:
```python
message = "Hola"
history = []
```
Salida:
```python
"", [{"role": "user", "content": "Hola"}]
```

3. Gradio llama:
```python
chat(history)
```
con:
```python
history = [{"role": "user", "content": "Hola"}]
```

4. Dentro de `chat()`:
```python
last_message = history[-1]["content"]  # "Hola"
prior = history[:-1]                   # []
answer, context = answer_question(last_message, prior)
```

5. Dentro de `answer_question()` (interno):
- combina pregunta + historial de usuario (`combined_question`)
- recupera top-k docs desde `vector_db` (`fetch_context`, `k=10`)
- inyecta contexto en `SYSTEM_PROMPT`
- llama al LLM (`gpt-4.1-nano`)
- devuelve `answer` y `docs`

6. Vuelve a `chat()`:
```python
history.append({"role": "assistant", "content": answer})
return history, format_context(context)
```

7. Pantalla:
- izquierda: conversación (`chatbot`)
- derecha: contexto/fuentes (`context_markdown`)

---

## 4) Iteración 2 (segunda pregunta)

### Estado al inicio de la iteración 2
```python
history = [
  {"role": "user", "content": "Hola"},
  {"role": "assistant", "content": "...respuesta 1..."}
]
```

### Paso a paso
1. Usuario escribe:
```python
message = "¿Qué cubre el plan premium?"
```

2. `put_message_in_chatbot` añade ese mensaje:
```python
history = [
  {"role": "user", "content": "Hola"},
  {"role": "assistant", "content": "...respuesta 1..."},
  {"role": "user", "content": "¿Qué cubre el plan premium?"}
]
```

3. `chat(history)` calcula:
```python
last_message = "¿Qué cubre el plan premium?"
prior = [
  {"role": "user", "content": "Hola"},
  {"role": "assistant", "content": "...respuesta 1..."}
]
```

4. Llama:
```python
answer, context = answer_question(last_message, prior)
```

5. `answer_question` repite RAG, ahora usando también historial previo para recuperar mejor contexto.

6. `chat()` agrega respuesta:
```python
history.append({"role": "assistant", "content": answer})
return history, format_context(context)
```

7. Pantalla actualizada:
- izquierda: chat con 4 mensajes (2 user + 2 assistant)
- derecha: contexto de la segunda respuesta

---

## 5) Orden real del pipeline

```text
ingest.py (una vez)
  -> app.py (UI)
     -> put_message_in_chatbot(...)
     -> chat(...)
        -> answer_question(...)
           -> retrieval en vector_db + LLM
        -> devuelve answer + context
     -> app pinta chat y fuentes
```
