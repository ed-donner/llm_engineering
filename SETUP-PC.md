# Ingeniería de LLM  - Domina el mundo de la IA y los LLMs

## Instrucciones de configuración para Windows

Hola, usuarios de PC!

Debo confesar por adelantado: configurar un entorno potente para trabajar en la vanguardia de la IA no es tan sencillo como me gustaría. Para la mayoría de la gente estas instrucciones irán genial; pero en algunos casos, por la razón que sea, te encontrarás con un problema. No dudes en ponerte en contacto conmigo: estoy aquí para ayudarte a ponerte en marcha rápidamente. No hay nada peor que sentirse _atrapado_. Envíame un mensaje, un correo electrónico o un mensaje de LinkedIn y te ayudaré a despegarte rápidamente.

Email: juangabriel@frogames.es  
LinkedIn: https://www.linkedin.com/in/juan-gabriel-gomila-salas/

Utilizo una plataforma llamada Anaconda para configurar tu entorno. Es una herramienta potente que crea un entorno científico completo. Anaconda garantiza que estés trabajando con la versión correcta de Python y que todos tus paquetes sean compatibles con el mío, incluso si nuestros sistemas son completamente diferentes. La configuración lleva más tiempo y utiliza más espacio en el disco duro (más de 5 GB), pero es muy confiable una vez que está funcionando.

Dicho esto: si tienes algún problema con Anaconda, te he proporcionado un enfoque alternativo. Es más rápido y más simple y debería permitirte trabajar rápidamente, con menos garantías en cuanto a compatibilidad.


### Parte 1: Clonar el Repo

Aquí vas a obtener una copia local del código en tu ordenador.

1. **Instala Git** si no está ya instalado


- Descarga Git desde https://git-scm.com/download/win
- Run the installer and follow the prompts, using default options (press OK lots of times!)

2. **Abrir el símbolo del sistema:**

- Presiona Win + R, y escribe `cmd`, para luego pulsar Enter

3. **Navega hasta tu carpeta de proyecto:**

Si tienes una carpeta específica para proyectos, navega hasta ella utilizando el comando cd. Por ejemplo  
`cd C:\Users\YourUsername\Documents\Projects`

Si no tienes una carpeta de proyectos, puedes crear una:
```
mkdir C:\Users\YourUsername\Documents\Projects
cd C:\Users\YourUsername\Documents\Projects
```
4. **Clonar el repositorio:**

Ingresa la siguiente instrucción en el símbolo del sistema en la carpeta Proyectos:

`git clone https://github.com/joanby/llm_engineering.git`

Esto crea un nuevo directorio `llm_engineering` dentro de la carpeta Proyectos y descarga el código de la clase. Ejecuta `cd llm_engineering` para ingresar. Este directorio `llm_engineering` se conoce como el "directorio raíz del proyecto".

### Parte 2: Instalar el Entorno de Anaconda

There is an alternative to Part 2 if this gives you problems.

1. **Instala Anaconda:**

- Descarga Anaconda desde https://docs.anaconda.com/anaconda/install/windows/
- Ejecuta el instalador y sigue las instrucciones. Ten en cuenta que ocupa varios GB y que la instalación demora un tiempo, pero será una plataforma potente para usar en el futuro.

5. **Configurar el entorno:**

- Abre **Anaconda Prompt** (búscala desde el menú de inicio)
- Navegue hasta el "directorio raíz del proyecto" ingresando algo como `cd C:\Users\YourUsername\Documents\Projects\llm_engineering` usando la ruta real al directorio raíz del proyecto llm_engineering. Escribe `dir` y verifica que puedas ver los subdirectorios para cada semana del curso.
- Crea el entorno: `conda env create -f environment.yml`
- Espera unos minutos a que se instalen todos los paquetes. En algunos casos, esto puede llevar literalmente entre 20 y 30 minutos si no has utilizado Anaconda antes, e incluso más tiempo según tu conexión a Internet. ¡Están sucediendo cosas importantes! Si esto se ejecuta durante más de 1 hora y 15 minutos o te genera otros problemas, ves directamente a la Parte 2B.
- ¡Ya has creado un entorno de IA aislado y dedicado para ingeniería de LLM, ejecución de almacenes de datos vectoriales y mucho más! Ahora debes **activarlo** con este comando: `conda activate llms`

Deberías ver `(llms)` en tu prompt, lo que indica que has activado tu nuevo entorno.

3. **Inicia Jupyter Lab:**

- En el indicador de Anaconda, desde la carpeta `llm_engineering`, escribe: `jupyter lab`

...y Jupyter Lab debería abrirse, listo para que empieces. Si no has visto Jupyter Lab antes, te lo explicaré en un momento. Ahora cierra la pestaña del navegador de Jupyter Lab, cierra la Terminal y continúa con la Parte 3.

### Parte 2B - Alternativa a la Parte 2 si Anaconda te da problemas

1. **Abre la Command Prompt**

Presiona Win + R, escribe `cmd`, y presiona Enter  

Ejecuta `python --version` para averiguar qué versión de Python estás utilizando. Lo ideal sería que estuvieras utilizando una versión de Python 3.11, de modo que estemos completamente sincronizados.
Si no es así, no es un gran problema, pero es posible que tengamos que volver a este tema más adelante si tienes problemas de compatibilidad.
Puede descargar Python aquí:
https://www.python.org/downloads/

2. Navega hasta el "directorio raíz del proyecto" ingresando algo como `cd C:\Users\YourUsername\Documents\Projects\llm_engineering` usando la ruta real al directorio raíz del proyecto llm_engineering. Introduce `dir` y verifica que puedas ver los subdirectorios para cada semana del curso.


Luego, crea un nuevo entorno virtual con este comando:
`python -m venv llms`

3. Activa el entorno virtual mediante
`llms\Scripts\activate`
Deberías ver (llms) en el símbolo del sistema, lo cual es señal de que todo va bien.

4. Ejecuta `pip install -r requirements.txt`  
La instalación puede tardar unos minutos.

5. **Inicia Jupyter Lab:**

Desde la carpeta `llm_engineering`, escribe: `jupyter lab`  
...y Jupyter Lab debería abrirse, ya lo tienes todo listo para comenzar. Abre la carpeta `week1` y haz doble clic en `day1.ipynb`. ¡Éxito! Ahora cierra Jupyter Lab y continúa con la Parte 3.

Si hay algun problema, no dudes en escribirnos por el foro!

### Parte 3 - Clave de OpenAI (OPCIONAL pero recomendado)

Especialmente durante las semanas 1 y 2 del curso, escribirás código para llamar a las API de los modelos de Frontier (modelos a la vanguardia del progreso). Tendrás que acompañarme en la creación de cuentas y claves API.

Para la semana 1, solo necesitarás OpenAI y podrás agregar los demás si lo deseas más adelante.

1. Crea una cuenta OpenAI si no tienes una visitando:
https://platform.openai.com/

2. OpenAI solicita un crédito mínimo para usar la API. Para mí, en España (y en los Estados Unidos para Ed), es de $5. Las llamadas a la API gastarán de este monto $5. En este curso, solo usaremos una pequeña parte de este monto. Te recomiendo que hagas la inversión, ya que podrás darle un excelente uso. Pero si prefieres no pagar por la API, te doy una alternativa en el curso usando Ollama.

Puede agregar su saldo de crédito a OpenAI en Settings > Billing:
https://platform.openai.com/settings/organization/billing/overview

¡Te recomiendo que desactives la recarga automática!

3. Crear tu clave de API 

La página web donde configuras tu clave OpenAI está en https://platform.openai.com/api-keys: presiona el botón verde "Crear nueva clave secreta" y luego "Crear clave secreta". Mantén un registro de la clave API en algún lugar privado; no podrás recuperarla de las pantallas OpenAI en el futuro. Debería iniciar `sk-proj-`.

En la semana 2 también configuraremos claves para Anthropic y Google, lo cual podrás hacer aquí cuando lleguemos allí.
- Claude API en https://console.anthropic.com/ de Anthropic
- Gemini API en https://ai.google.dev/gemini-api de Google

Más adelante en el curso, utilizarás la fabulosa plataforma HuggingFace; hay una cuenta disponible de forma gratuita en https://huggingface.co; puedes crear un token de API desde el menú Avatar >> Settings >> Access Tokens.

Y en la semana 6/7, usarás la fantástica herramienta Weights & Biases en https://wandb.ai para supervisar tus lotes de entrenamiento. Las cuentas también son gratuitas y puedes configurar un token de manera similar.


### Parte 4 - El fichero .env

Cuando tengas todas estas claves, crea un nuevo archivo llamado `.env` en el directorio raíz de tu proyecto. El nombre del archivo debe tener exactamente los cuatro caracteres ".env" en lugar de "my-keys.env" o ".env.txt". A continuación, te indicamos cómo hacerlo:

1. Abre Notepad (Windows + R para abrir la ventana de ejecución, luego introduce `notepad`)

2. En el Bloc de notas, escriba esto, reemplazando xxxx con su clave API (comenzando con `sk-proj-`).

```
OPENAI_API_KEY=xxxx
```

Si tienes otras claves, puedes agregarlas también o volver a esta sección en las próximas semanas:

```
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

Comprueba que no haya espacios antes o después del signo `=`, y que no haya espacios al final de la clave.

3. Ve a Archivo > Guardar como. En el menú desplegable "Guardar como tipo", selecciona Todos los archivos. En el campo "Nombre de archivo", escribe exactamente **.env** como nombre de archivo. Elige guardarlo en el directorio raíz del proyecto (la carpeta llamada `llm_engineering`) y haz clic en Guardar.

4. Navega hasta la carpeta donde guardaste el archivo en el Explorador y asegúrate de que se haya guardado como ".env" y no como ".env.txt"; si es necesario, cámbiale el nombre a ".env". Es posible que tengas que asegurarte de que "Mostrar extensiones de archivo" esté configurado en "Activado" para que puedas ver las extensiones de archivo. Envíame un mensaje o un correo electrónico si eso no tiene sentido.

Este archivo no aparecerá en Jupyter Lab porque Jupyter oculta los archivos que comienzan con un punto. Este archivo aparece en el archivo `.gitignore`, por lo que no se registrará y tus claves permanecerán seguras.

### Parte 5 - ¡¡Hora del espectáculo!!

- Abra el **Anaconda Prompt** (búsquelo en el menú Inicio)

- Navegue hasta el "directorio raíz del proyecto" ingresando algo como `cd C:\Users\YourUsername\Documents\Projects\llm_engineering` usando la ruta real al directorio raíz de su proyecto llm_engineering. Escriba `dir` y verifique que pueda ver los subdirectorios para cada semana del curso.

- Active su entorno con `conda activate llms` (o `llms\Scripts\activate` si utilizó el enfoque alternativo en la Parte 2B)

- Debería ver (llms) en su mensaje, lo cual es una señal de que todo está bien. Y ahora, escriba: `jupyter lab` y Jupyter Lab debería abrirse, listo para que comience. Abra la carpeta `week1` y haga doble clic en `day1.ipynb`.

¡Y listo!

Ten en cuenta que, cada vez que inicies Jupyter Lab en el futuro, deberás seguir estas instrucciones de la Parte 5 para iniciarlo desde el directorio `llm_engineering` con el entorno `llms` activado.

Para aquellos que son nuevos en Jupyter Lab/Jupyter Notebook, es un entorno de ciencia de datos encantador en el que simplemente pueden presionar shift+return en cualquier celda para ejecutarlo; comiencen en la parte superior y avancen hacia abajo. Hay un cuaderno en la carpeta week1 con una [Guía para Jupyter Lab](week1/Guide%20to%20Jupyter.ipynb) y un tutorial de [Python intermedio](week1/Intermediate%20Python.ipynb), si eso te resulta útil. Cuando pasemos a Google Colab en la semana 3, experimentarán la misma interfaz para los entornos de ejecución de Python en la nube.

Si tienes algún problema, he incluido un cuaderno en la semana 1 llamado [troubleshooting.ipynb](week1/troubleshooting.ipynb) para resolverlo.
