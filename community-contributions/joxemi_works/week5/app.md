# app.py - Resumen rapido

## Que hace
- Levanta una interfaz web con Gradio para chatear.
- Recoge el mensaje del usuario.
- Llama a `answer_question(...)` para obtener respuesta y contexto.
- Muestra la respuesta en el chat y, al lado, los fragmentos usados.

## A quien llama
- Importa `answer_question` desde `implementation.answer`.
- En esta estructura de estudio, ese rol corresponde a `pro_implementation/answer.py`.

## Idea clave
- `app.py` es la capa de interfaz: muestra y conecta, no indexa ni recupera por si sola.
