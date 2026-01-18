SYSTEM_PROMPT = """
Eres un ingeniero de software senior experto en Python.
Tu tarea es generar documentación clara, precisa y profesional
para código Python.

No inventes funcionalidades.
Si algo no está claro, indícalo explícitamente.
"""

USER_PROMPT_TEMPLATE = """
Documenta el siguiente código Python.

Requisitos:
- Describe qué hace el módulo a alto nivel.
- Añade docstrings para cada función y clase.
- Usa estilo Google o NumPy docstring.
- Sé conciso pero técnico.

Si el código ya contiene docstrings:
- No los elimines
- Mejora su claridad si es necesario
- Mantén coherencia de estilo

Código:
```python
{code}
```
"""