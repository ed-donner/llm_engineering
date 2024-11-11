# Ingeniería de LLM  - Master en IA y LLMs

## Tu viaje de 8 semanas hacia el dominio completo de estos temas comienza hoy

![Voyage](voyage.jpg)

Me alegro mucho de que me acompañes en este camino. Vamos a construir proyectos inmensamente satisfactorios en las próximas semanas. Algunos serán fáciles, otros supondrán un reto, ¡y muchos te ASOMBRARÁN! Los proyectos se basan unos en otros para que desarrolles una experiencia cada vez más profunda cada semana. Una cosa es segura: te divertirás mucho por el camino.

### Una nota antes de empezar

Estoy aquí para ayudarte a tener más éxito en tu aprendizaje. Si te encuentras con algún problema, o si tienes alguna idea sobre cómo puedo mejorar el curso, por favor, ponte en contacto conmigo en la plataforma o enviándome un correo electrónico directamente (juangabriel@frogames.es). Siempre es bueno conectar con la gente en LinkedIn para construir la comunidad - me encontrarás aquí:  
[https://www.linkedin.com/in/juan-gabriel-gomila-salas/
](https://www.linkedin.com/in/juan-gabriel-gomila-salas/)

### Un punto importante sobre los costes de las API

Durante el curso, te sugeriré que pruebes los principales modelos a la vanguardia del progreso, conocidos como los modelos Frontier. También te sugeriré que ejecutes modelos de código abierto utilizando Google Colab. Estos servicios tienen algunos cargos, pero mantendré el coste al mínimo, unos pocos céntimos cada vez.

Por favor, controla el uso de tu API para asegurarte de que estás cómodo con el gasto; he incluido enlaces más abajo. No hay necesidad de gastar más de un par de dólares para todo el curso. Usted puede encontrar que los proveedores de IA como OpenAI requiere un crédito mínimo como \ $ 5 para su región; sólo debemos gastar una fracción de ella, pero usted tendrá un montón de oportunidades para poner a buen uso en sus propios proyectos. Durante la Semana 7 tienes la opción de gastar un poco más si te está gustando el proceso: ¡yo mismo gasto unos 10 $ y los resultados me hacen muy feliz! Pero no es necesario en absoluto; lo importante es que te centres en aprender.

### Cómo está organizado este Repo

Hay carpetas para cada una de las «semanas», que representan módulos de la clase, culminando en una potente solución autónoma de IA Agentica en la Semana 8 que se basa en muchas de las semanas anteriores.    
Siga las instrucciones de configuración a continuación, a continuación, abra la carpeta de la Semana 1 y prepárese para la alegría.

### La parte más importante

El mantra del curso es: la mejor manera de aprender es **HACIENDO**. Debes trabajar conmigo, ejecutando cada celda, inspeccionando los objetos para obtener una comprensión detallada de lo que está sucediendo. Después, modifica el código y hazlo tuyo. Hay jugosos retos para ti a lo largo del curso. Me encantaría que enviaras tu código para que pueda seguir tu progreso, y puedo poner tus soluciones a disposición de los demás para que compartamos tu progreso. Aunque los proyectos son divertidos, están diseñados ante todo para ser _educativos_, enseñándote habilidades empresariales que puedes poner en práctica en tu trabajo.

## Instrucciones de configuración

Debo confesar por adelantado: configurar un entorno potente para trabajar en la vanguardia de la IA no es tan sencillo como me gustaría. Para la mayoría de la gente estas instrucciones irán genial; pero en algunos casos, por la razón que sea, te encontrarás con un problema. No dudes en ponerte en contacto conmigo: estoy aquí para ayudarte a ponerte en marcha rápidamente. No hay nada peor que sentirse _atrapado_. Envíame un mensaje, un correo electrónico o un mensaje de LinkedIn y te ayudaré a despegarte rápidamente.

El enfoque recomendado es utilizar Anaconda para su entorno. Es una poderosa herramienta que construye un entorno científico completo. Anaconda asegura que estás trabajando con la versión correcta de Python y que todos tus paquetes son compatibles con los míos, incluso si estamos en diferentes plataformas.

**Actualización** Algunas personas han tenido problemas con Anaconda - ¡horror! La idea de Anaconda es que sea realmente fácil y sencillo trabajar con el mismo entorno. Si tienes algún problema con las instrucciones de abajo, por favor salta al final de este README para el enfoque alternativo usando `pip` con `virtualenv`, y con suerte estarás funcionando rápidamente. Y por favor, envíame un mensaje si puedo ayudarte con algo.

En este curso usaremos principalmente Jupyter Lab. Para aquellos que no conozcan Jupyter Lab / Jupyter Notebook, es un encantador entorno de Ciencia de Datos en el que puedes simplemente pulsar shift+return en cualquier celda para ejecutarlo; ¡empieza por arriba y ve bajando! Cuando pasemos a Google Colab en la semana 3, experimentarás la misma interfaz para los tiempos de ejecución de Python en la nube.

### Para usuarios de Windows

1. **Instale Git** (si no está ya instalado):

- Descarga Git desde https://git-scm.com/download/win
- Ejecute el instalador y siga las instrucciones, utilizando las opciones por defecto

2. **Abrir símbolo del sistema:**

- Pulsa Win + R, escribe `cmd`, y pulsa Enter

3. **Navega hasta la carpeta de tus proyectos:**

Si tienes una carpeta específica para proyectos, navega hasta ella utilizando el comando cd. Por ejemplo  
`cd C:\Users\YourUsername\Documents\Projects`

Si no tienes una carpeta de proyectos, puedes crear una:
```
mkdir C:\Users\YourUsername\Documents\Projects
cd C:\Users\YourUsername\Documents\Projects
```

4. **Clonar el repositorio:**

- Ve a la página GitHub del curso
- Haz clic en el botón verde 'Código' y copia la URL
- En el símbolo del sistema, escribe esto, sustituyendo todo lo que hay después de la palabra 'clone' por la URL copiada: `git clone <paste-url-here>`

5. **Instala Anaconda:**

- Descarga Anaconda desde https://docs.anaconda.com/anaconda/install/windows/
- Ejecute el instalador y siga las instrucciones.
- Un estudiante mencionó que si se te pide actualizar Anaconda a una versión más reciente durante la instalación, no deberías hacerlo, ya que podría haber problemas con la última actualización para PC. (¡Gracias por el consejo!)

6. **Configurar el entorno

- Abre Anaconda Prompt (búscalo en el menú Inicio)
- Navegue a la carpeta del repositorio clonado usando `cd path\to\repo` (sustituya `path\to\repo` por la ruta real al directorio llm_engineering, su versión clonada localmente del repositorio)
- Cree el entorno: `conda env create -f environment.yml`.
- Espere unos minutos a que se instalen todos los paquetes
- Active el entorno: `conda activate llms`.  

Deberías ver `(llms)` en tu prompt, lo que indica que has activado tu nuevo entorno.
7. **Iniciar Jupyter Lab:**

- En Anaconda Prompt, desde la carpeta `llm_engineering`, escribe: `jupyter lab`

...y Jupyter Lab debería abrirse, listo para que empieces. Abre la carpeta `week1` y haz doble click en `day1.ipnbk`.

### Para usuarios de Mac

1. **Instala Git** si no está ya instalado (lo estará en la mayoría de los casos)

- Abra Terminal (Aplicaciones > Utilidades > Terminal)
- Escriba `git --version` Si no está instalado, se le pedirá que lo instale

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

4. **Instala Anaconda:**

- Descarga Anaconda desde https://docs.anaconda.com/anaconda/install/mac-os/
- Haz doble clic en el archivo descargado y sigue las instrucciones de instalación

5. **Configurar el entorno:**

- Abrir Terminal
- Navegue a la carpeta del repositorio clonado usando `cd ruta/a/repo` (sustituya `ruta/a/repo` por la ruta real al directorio llm_engineering, su versión clonada localmente del repositorio)
- Cree el entorno: `conda env create -f environment.yml`.
- Espere unos minutos a que se instalen todos los paquetes
- Active el entorno: `conda activate llms`.

Deberías ver `(llms)` en tu prompt, lo que indica que has activado tu nuevo entorno.

6. **Inicia Jupyter Lab:**

- En Terminal, desde la carpeta `llm_engineering`, escribe: `jupyter lab`

...y Jupyter Lab debería abrirse, listo para que empieces. Abre la carpeta `week1` y haz doble click en `day1.ipnbk`.

### Cuando lleguemos a ello, crear tus claves API

Especialmente durante las semanas 1 y 2 del curso, escribirás código para llamar a las API de los modelos de Frontier (modelos a la vanguardia del progreso). Tendrás que acompañarme en la creación de cuentas y claves API.

- [GPT API](https://platform.openai.com/) from OpenAI
- [Claude API](https://console.anthropic.com/) from Anthropic
- [Gemini API](https://ai.google.dev/gemini-api) from Google

Inicialmente sólo usaremos OpenAI, así que puedes empezar con eso, y cubriremos los demás poco después. La página web donde puedes configurar tu clave OpenAI es [aquí](https://platform.openai.com/api-keys). Mira la nota extra sobre los costes de la API más abajo si eso te preocupa. Un estudiante me comentó que OpenAI puede tardar unos minutos en registrarse; si al principio recibes un mensaje de error diciendo que te has quedado sin cuota, espera unos minutos e inténtalo de nuevo. Otra razón por la que puedes encontrarte con el error de cuota agotada es si aún no has añadido un método de pago válido a tu cuenta de OpenAI. Puedes hacerlo haciendo clic en tu foto de perfil en el sitio web de OpenAI y luego en «Tu perfil». Una vez redirigido a la página de tu perfil, elige «Facturación» en el menú del panel izquierdo. Tendrás que introducir un método de pago válido y cargar tu cuenta con un pequeño anticipo. Se recomienda **desactivar** la recarga automática como medida de seguridad adicional. Si sigues teniendo problemas, consulta más consejos para solucionar problemas en el cuaderno de la Semana 1, Día 1, y/o envíame un mensaje.

Más adelante en el curso utilizarás la fabulosa plataforma HuggingFace; una cuenta está disponible gratuitamente en [HuggingFace](https://huggingface.co) - puedes crear un token API desde el menú Avatar >> Configuración >> Tokens de acceso.

Y en la Semana 6/7 utilizarás la estupenda plataforma [Weights & Biases](https://wandb.ai) para vigilar tus lotes de entrenamiento. Las cuentas también son gratuitas, y puedes configurar un token de forma similar.

Cuando tengas estas claves, crea un nuevo archivo llamado `.env` en el directorio raíz de tu proyecto. Este archivo no aparecerá en Jupyter Lab porque es un archivo oculto; deberías crearlo usando algo como Notepad (PC) o nano (Mac / Linux). He puesto instrucciones detalladas al final de este README.

Debería tener un contenido como este, y para empezar sólo necesitas la primera línea:

```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

Este archivo está listado en el archivo `.gitignore`, por lo que no se registrará y tus claves permanecerán seguras.
Si tienes algún problema con este proceso, hay una solución sencilla que explico en el vídeo.

### A partir de la Semana 3, también usaremos Google Colab para correr con GPUs.

Usted debe ser capaz de utilizar el nivel gratuito o gasto mínimo para completar todos los proyectos en la clase. Yo personalmente me he suscrito a Colab Pro+ y me encanta, pero no es obligatorio.

Infórmate sobre Google Colab y crea una cuenta de Google (si aún no tienes una) [aquí](https://colab.research.google.com/)

Los enlaces de los colab están en las carpetas de la semana y también aquí:  
- Para la semana 3 día 1, este Google Colab muestra lo que [colab puede hacer](https://colab.research.google.com/drive/1DjcrYDZldAXKJ08x1uYIVCtItoLPk1Wr?usp=sharing)
- Para la semana 3 día 2, aquí está el colab sobre [pipelines API] de HuggingFace(https://colab.research.google.com/drive/1aMaEw8A56xs0bRM4lu8z7ou18jqyybGm?usp=sharing)
- Para la semana 3 día 3, aquí está el colab sobre [Tokenizers](https://colab.research.google.com/drive/1WD6Y2N7ctQi1X9wa6rpkg8UfyA4iSVuz?usp=sharing)
- Para la semana 3 día 4, vamos a un colab con HuggingFace [modelos](https://colab.research.google.com/drive/1hhR9Z-yiqjUe7pJjVQw4c74z_V3VchLy?usp=sharing)
- Para la semana 3 día 5, volvemos al colab para hacer nuestro [Meeting Minutes product](https://colab.research.google.com/drive/1KSMxOCprsl1QRpt_Rq0UqCAyMtPqDQYx?usp=sharing)
- Para la semana 7, utilizaremos estos libros de Colab: [Día 1](https://colab.research.google.com/drive/15rqdMTJwK76icPBxNoqhI7Ww8UM-Y7ni?usp=sharing) | [Día 2](https://colab.research.google.com/drive/1T72pbfZw32fq-clQEp-p8YQ4_qFKv4TP?usp=sharing) | [Días 3 y 4](https://colab.research.google.com/drive/1csEdaECRtjV_1p9zMkaKKjCpYnltlN3M?usp=sharing) | [Día 5](https://colab.research.google.com/drive/1igA0HF0gvQqbdBD4GkcK3GpHtuDLijYn?usp=sharing)


### Seguimiento de los gastos de la API

Puedes mantener tu gasto de API muy bajo a lo largo de este curso; puedes monitorizar el gasto en los dashboards: [aquí](https://platform.openai.com/usage) para OpenAI, [aquí](https://console.anthropic.com/settings/cost) para Anthropic y [aquí](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/cost) para Google Gemini.

Los gastos de los ejercicios de este curso deberían ser siempre bastante bajos, pero si prefieres que sean mínimos, asegúrate de elegir siempre las versiones más baratas de los modelos:
1. Para OpenAI: Utiliza siempre el modelo `gpt-4o-mini` en el código en lugar de `gpt-4o`.
2. Para Anthropic: Utilice siempre el modelo `claude-3-haiku-20240307` en el código en lugar de los otros modelos Claude
3. Durante la semana 7, estate atento a mis instrucciones para utilizar el conjunto de datos más barato

## ¡Y eso es todo! ¡Feliz codificación!

### Instrucciones alternativas si Anaconda te da problemas

Primero por favor ejecute
`python --version`  
Para saber en qué python estás. Lo ideal sería que estuvieras usando Python 3.11.x, para que estemos completamente sincronizados. Puedes descargar python en  
https://www.python.org/downloads/

Aquí están los pasos:

Después de clonar el repositorio, entra en el directorio raíz del proyecto `llm_engineering`.
A continuación:

1. Crear un nuevo entorno virtual: `python -m venv venv`.  
2. Active el entorno virtual con  
En un Mac: `source venv/bin/activate`  
En un PC: `venv\Scripts\activate`.
3. Ejecute `pip install -r requirements.txt`.
4. Cree un archivo llamado `.env` en el directorio raíz del proyecto y añada las claves privadas de la API, como se indica a continuación. (La siguiente sección tiene instrucciones más detalladas para esto, si lo prefiere).
   
```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

5. Ejecuta `jupyter lab` para iniciar Jupyter y dirígete a la carpeta intro para empezar.

Avísame si tienes problemas.

### Guía para crear el archivo `.env`.

**Para usuarios de PC:**

1. Abre el bloc de notas (Windows + R para abrir el cuadro Ejecutar, introduce bloc de notas).

2. En el Bloc de notas, escriba el contenido del archivo, por ejemplo:

```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```
Compruebe que no hay espacios antes ni después del signo `=`, y que no hay espacios al final de la clave.

3. 3. Vaya a Archivo > Guardar como. En el menú desplegable «Guardar como tipo», seleccione Todos los archivos. En el campo «Nombre de archivo», escriba «.env». Elija la raíz de la carpeta del proyecto (la carpeta llamada `llm_engineering`) y haga clic en Guardar.  

4. 4. Navegue hasta la carpeta donde guardó el archivo en el Explorador y asegúrese de que se guardó como «.env» y no como «.env.txt» - si es necesario, cámbiele el nombre a «.env» - puede que tenga que asegurarse de que la opción «Mostrar extensiones de archivo» está activada para que pueda ver las extensiones de archivo. Envíame un mensaje o un correo electrónico si esto no tiene sentido.

**Para usuarios de Mac:**

1. Abre Terminal (Comando + Espacio para abrir Spotlight, escribe Terminal y presiona Enter)

2. cd a su directorio raíz del proyecto

cd /ruta/a/tu/proyecto

(en otras palabras, cambia al directorio como `/Usuarios/su_nombre/Proyectos/llm_engineering`, o donde hayas clonado llm_engineering).

3. Crea el archivo .env con

nano .env

4. Luego escribe tus claves API en nano:

```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

5. Guarde el archivo:

Control + O  
Enter (para confirmar que se guarda el archivo)  
Control + X para salir del editor

6. Utilice este comando para listar los archivos de su fichero

`ls -a`

Y confirma que el archivo `.env` está ahí.
