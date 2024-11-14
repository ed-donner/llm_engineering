# Ingeniería de LLM  - Domina el mundo de la IA y los LLMs

## Instrucciones de configuración para Mac

Hola, usuarios de Mac!

Debo confesar por adelantado: configurar un entorno potente para trabajar en la vanguardia de la IA no es tan sencillo como me gustaría. Para la mayoría de la gente estas instrucciones irán genial; pero en algunos casos, por la razón que sea, te encontrarás con un problema. No dudes en ponerte en contacto conmigo: estoy aquí para ayudarte a ponerte en marcha rápidamente. No hay nada peor que sentirse _atrapado_. Envíame un mensaje, un correo electrónico o un mensaje de LinkedIn y te ayudaré a despegarte rápidamente.

Email: juangabriel@frogames.es  
LinkedIn: https://www.linkedin.com/in/juan-gabriel-gomila-salas/

Utilizo una plataforma llamada Anaconda para configurar tu entorno. Es una herramienta potente que crea un entorno científico completo. Anaconda garantiza que estés trabajando con la versión correcta de Python y que todos tus paquetes sean compatibles con el mío, incluso si nuestros sistemas son completamente diferentes. La configuración lleva más tiempo y utiliza más espacio en el disco duro (más de 5 GB), pero es muy confiable una vez que está funcionando.

Dicho esto: si tienes algún problema con Anaconda, te he proporcionado un enfoque alternativo. Es más rápido y más simple y debería permitirte trabajar rápidamente, con menos garantías en cuanto a compatibilidad.

### Parte 1: Clonar el Repo

Aquí vas a obtener una copia local del código en tu ordenador.

1. **Instala Git** si no está ya instalado (lo estará en la mayoría de los casos)

- Abre el Terminal (Aplicaciones > Utilidades > Terminal)
- Escribe `git --version` Si no está instalado, se te pedirá que lo instales pulsado intro.

2. **Navega hasta la carpeta de tus proyectos:**.

Si tienes una carpeta específica para proyectos, navega hasta ella usando el comando cd. Por ejemplo
`cd ~/Documentos/Proyectos`

Si no tienes una carpeta de proyectos, puedes crear una:
```
mkdir ~/Documents/Projects
cd ~/Documents/Projects
```

3. **Clonar el repositorio**

- Ve a la página GitHub del curso
- Haz clic en el botón verde 'Código' y copia la URL
- En Terminal, escribe esto, sustituyendo todo lo que hay después de la palabra 'clone' por la URL copiada: `git clone <pega-url-aquí>`


### Parte 2: Instalar el entorno de Anaconda

Existe una alternativa a la Parte 2 si esto te causa problemas.

1. **Instala Anaconda:**

- Descarga Anaconda desde https://docs.anaconda.com/anaconda/install/mac-os/
- Haz doble clic en el archivo descargado y sigue las instrucciones de instalación. Ten en cuenta que ocupa varios GB y que la instalación demora un poco, pero será una plataforma potente para usar en el futuro.

2. **Configurar el entorno:**

- Abre una nueva Terminal (Aplicaciones > Utilidades > Terminal)
- Navega hasta el "directorio raíz del proyecto" usando `cd ~/Documents/Projects/llm_engineering` (reemplaza esta ruta según sea necesario con la ruta real al directorio llm_engineering, tu versión clonada localmente del repositorio). Ejecuta `ls` y verifica que puedes ver los subdirectorios para cada semana del curso.
- Crea el entorno mediante: `conda env create -f environment.yml`
- Espera unos minutos a que se instalen todos los paquetes. En algunos casos, esto puede llevar literalmente entre 20 y 30 minutos si no has utilizado Anaconda antes, e incluso más tiempo según tu conexión a Internet. ¡Están sucediendo cosas importantes! Si esto se ejecuta durante más de 1 hora y 15 minutos o te genera otros problemas, ves directamente a la Parte 2B.
- ¡Ya has creado un entorno de IA aislado y dedicado para ingeniería de LLM, ejecución de almacenes de datos vectoriales y mucho más! Ahora debes **activarlo** con este comando: `conda activate llms`

Deberías ver `(llms)` en tu prompt, lo que indica que has activado tu nuevo entorno.

3. **Inicia Jupyter Lab:**

- En Terminal, desde la carpeta `llm_engineering`, escribe: `jupyter lab`


...y Jupyter Lab debería abrirse, listo para que empieces. Si no has visto Jupyter Lab antes, te lo explicaré en un momento. Ahora cierra la pestaña del navegador de Jupyter Lab, cierra la Terminal y continúa con la Parte 3.


### Parte 2B - Alternativa a la Parte 2 si Anaconda te da problemas


1. **Abre una nueva Terminal** (Aplicaciones > Utilidades > Terminal)

Primero por favor ejecuta
`python --version`  
Para saber en qué python estás. Lo ideal sería que estuvieras usando Python 3.11.x, para que estemos completamente sincronizados. Puedes descargar python en  
https://www.python.org/downloads/

2. Navega hasta el "directorio raíz del proyecto" usando `cd ~/Documents/Projects/llm_engineering` (reemplaza esta ruta según sea necesario con la ruta real al directorio llm_engineering, tu versión clonada localmente del repositorio). Ejecuta `ls` y verifica que puedes ver los subdirectorios para cada semana del curso.

Luego, crea un nuevo entorno virtual con este comando:
`python -m venv llms`

3. Activa el entorno virtual mediante:  
`source llms/bin/activate`
Deberías ver (llms) en el símbolo del sistema, lo cual es señal de que todo va bien.

4. Ejecuta `pip install -r requirements.txt`  
Esto puede que tarde varios minutos en instalarlo todo.

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

1. Abre el Terminal (Aplicaciones > Utilidades > Terminal)

2. Navega hasta el "directorio raíz del proyecto" usando `cd ~/Documents/Projects/llm_engineering` (reemplaza esta ruta con la ruta real al directorio llm_engineering, tu versión clonada localmente del repositorio).

3. Crea el fichero .env mediante

```
nano .env
```

4. Luego escribe tus claves API usando nano, reemplazando xxxx con tu clave API (comenzando con `sk-proj-`).

```
OPENAI_API_KEY=xxxx
```

Si tienes otras claves, puedes agregarlas también o volver a esta sección en las próximas semanas:

```
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

5. Guarda el fichero pulsando:

Control + O  
Enter (para confirmar el guardado del file)  
Control + X para salir del editor

6. Utilice este comando para listar los archivos en el directorio raíz de su proyecto:

`ls -a`

Y confirma que el archivo `.env` está allí.

Este archivo no aparecerá en Jupyter Lab porque Jupyter oculta los archivos que comienzan con un punto. Este archivo se incluye en el archivo `.gitignore`, por lo que no se registrará y sus claves permanecerán seguras.

### Parte 5 - ¡¡Hora del espectáculo!!

- Abre el Terminal (Aplicaciones > Utilidades > Terminal)
  
- Navega hasta el "directorio raíz del proyecto" usando `cd ~/Documents/Projects/llm_engineering` (reemplaza esta ruta con la ruta real al directorio llm_engineering, tu versión clonada localmente del repositorio). Ejecuta `ls` y verifica que puedas ver los subdirectorios para cada semana del curso.

- Activa tu entorno con `conda activate llms` (o `source llms/bin/activate` si utilizaste el enfoque alternativo en la Parte 2B)

- Deberías ver (llms) en el mensaje, lo que indica que todo está bien. Ahora, escribe: `jupyter lab` y Jupyter Lab debería abrirse, listo para que puedas comenzar. Abre la carpeta `week1` y haz doble clic en `day1.ipynb`.

¡Y listo!

Ten en cuenta que, cada vez que inicies Jupyter Lab en el futuro, deberás seguir estas instrucciones de la Parte 5 para iniciarlo desde el directorio `llm_engineering` con el entorno `llms` activado.

Para aquellos que son nuevos en Jupyter Lab/Jupyter Notebook, es un entorno de ciencia de datos encantador en el que simplemente pueden presionar shift+return en cualquier celda para ejecutarlo; comiencen en la parte superior y avancen hacia abajo. Hay un cuaderno en la carpeta week1 con una [Guía para Jupyter Lab](week1/Guide%20to%20Jupyter.ipynb) y un tutorial de [Python intermedio](week1/Intermediate%20Python.ipynb), si eso te resulta útil. Cuando pasemos a Google Colab en la semana 3, experimentarán la misma interfaz para los entornos de ejecución de Python en la nube.

Si tienes algún problema, he incluido un cuaderno en la semana 1 llamado [troubleshooting.ipynb](week1/troubleshooting.ipynb) para resolverlo.
