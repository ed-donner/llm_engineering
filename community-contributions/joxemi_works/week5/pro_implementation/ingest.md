# ingest.py - Resumen rapido

## Que hace
- Lee documentos `.md` desde `knowledge-base`.
- Pide al LLM que los divida en chunks con solape.
- Genera embeddings de esos chunks.
- Guarda textos, metadatos y vectores en Chroma (`preprocessed_db`, coleccion `docs`).

## Para que sirve
- Prepara el indice que luego usa `answer.py` para responder preguntas.

## Idea clave
- `ingest.py` es la fase de preparacion/indexado del conocimiento.
