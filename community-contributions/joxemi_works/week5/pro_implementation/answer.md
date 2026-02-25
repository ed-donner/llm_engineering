# answer.py - Resumen rapido

## Que hace
- Recibe la pregunta del usuario.
- Busca contexto en la base vectorial (`preprocessed_db`) usando embeddings.
- Reescribe la pregunta para hacer una segunda busqueda mejor.
- Une resultados, los reranquea con LLM y se queda con los mejores.
- Genera la respuesta final usando esos fragmentos como contexto.

## De que depende
- Depende de que exista la base vectorial en `preprocessed_db`.
- Esa base la crea `ingest.py`.

## Idea clave
- `answer.py` es el motor RAG: recupera informacion relevante y redacta la respuesta.
