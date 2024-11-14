# Ingeniería de LLM  - Domina el mundo de la IA y los LLMs

## Tu viaje de 8 semanas hacia el dominio completo de estos temas comienza hoy

![Voyage](voyage.jpg)


Me alegro mucho de que me acompañes en este camino. Vamos a construir proyectos inmensamente satisfactorios en las próximas semanas. Algunos serán fáciles, otros supondrán un reto, ¡y muchos te ASOMBRARÁN! Los proyectos se basan unos en otros para que desarrolles una experiencia cada vez más profunda cada semana. Una cosa es segura: te divertirás mucho por el camino.


### Una nota antes de empezar

Estoy aquí para ayudarte a tener más éxito en tu aprendizaje. Si te encuentras con algún problema, o si tienes alguna idea sobre cómo puedo mejorar el curso, por favor, ponte en contacto conmigo en la plataforma o enviándome un correo electrónico directamente (juangabriel@frogames.es). Siempre es bueno conectar con la gente en LinkedIn para construir la comunidad - me encontrarás aquí:  
[https://www.linkedin.com/in/juan-gabriel-gomila-salas/
](https://www.linkedin.com/in/juan-gabriel-gomila-salas/)


Los recursos anexos al curso, incluidas las slides y links de utilidad, los tienes en: https://cursos.frogamesformacion.com/pages/blog/ingenieria-de-llms-recursos

## Instrucciones de Gratificación Instantánea para la Semana 1, Día 1

¡Comenzaremos el curso instalando Ollama para que puedas ver los resultados de inmediato!
1. Descarga e instala Ollama desde https://ollama.com
2. En una PC, inicia un Símbolo del sistema/PowerShell (Presiona Win + R, escribe `cmd` y presiona Enter). En una Mac, inicia una Terminal (Aplicaciones > Utilidades > Terminal).
3. Ejecuta `ollama run llama3.2` o, para máquinas más pequeñas, prueba `ollama run llama3.2:1b`
4. Si esto no funciona, es posible que debas ejecutar `ollama serve` en otro PowerShell (Windows) o Terminal (Mac) e intentar el paso 3 nuevamente
5. Y si eso no funciona en tu equipo, lo he configurado en la nube. Esto está en Google Colab, que necesitará que tengas una cuenta de Google para iniciar sesión, pero es gratis: https://colab.research.google.com/drive/1i5hHBpd424_gNuO0T8AsbLDBR2toRh8K?usp=sharing 

Si tienes algún problema, ¡contacta conmigo!

## A continuación, instrucciones de configuración

Después de realizar el proyecto rápido de Ollama y de presentarme y presentar el curso, nos ponemos a trabajar con la configuración completa del entorno.

Espero haber hecho un buen trabajo para que estas guías sean infalibles, pero comuníquese conmigo de inmediato si encuentra obstáculos:

- Usuarios de PC, podéis seguir las instrucciones en [SETUP-PC.md](SETUP-PC.md)
- Usuarios de Mac, podéis seguir las instrucciones en [SETUP-mac.md](SETUP-mac.md)
- Usuarios de Linux, ¡las instrucciones para Mac deberían ser lo suficientemente precisas!

### Un punto importante sobre los costes de las API

Durante el curso, te sugeriré que pruebes los principales modelos a la vanguardia del progreso, conocidos como los modelos Frontier. También te sugeriré que ejecutes modelos de código abierto utilizando Google Colab. Estos servicios tienen algunos cargos, pero mantendré el coste al mínimo, unos pocos céntimos cada vez.

Por favor, controla el uso de tu API para asegurarte de que estás cómodo con el gasto; he incluido enlaces más abajo. No hay necesidad de gastar más de un par de dólares para todo el curso. Usted puede encontrar que los proveedores de IA como OpenAI requiere un crédito mínimo como \ $ 5 para su región; sólo debemos gastar una fracción de ella, pero usted tendrá un montón de oportunidades para poner a buen uso en sus propios proyectos. Durante la Semana 7 tienes la opción de gastar un poco más si te está gustando el proceso: ¡yo mismo gasto unos 10 $ y los resultados me hacen muy feliz! Pero no es necesario en absoluto; lo importante es que te centres en aprender.

También te mostraré, cuando sea posible, una alternativa si no deseas gastarte nada de dinero en el uso de APIs.


### Cómo está organizado este Repo

Hay carpetas para cada una de las «semanas», que representan módulos de la clase, culminando en una potente solución autónoma de IA Agentica en la Semana 8 que se basa en muchas de las semanas anteriores.    
Siga las instrucciones de configuración que hay justo en los siguientes apartados, y a continuación, abre la carpeta de la Semana 1 y prepárate para la alegría.


### La parte más importante

El mantra del curso es: la mejor manera de aprender es **HACIENDO**. Debes trabajar conmigo, ejecutando cada celda, inspeccionando los objetos para obtener una comprensión detallada de lo que está sucediendo. Después, modifica el código y hazlo tuyo. Hay jugosos retos para ti a lo largo del curso. Me encantaría que enviaras tu código para que pueda seguir tu progreso, y puedo poner tus soluciones a disposición de los demás para que compartamos tu progreso. Aunque los proyectos son divertidos, están diseñados ante todo para ser _educativos_, enseñándote habilidades empresariales que puedes poner en práctica en tu trabajo.



## A partir de la Semana 3, también usaremos Google Colab para correr con GPUs.

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



## ¡Y eso es todo! ¡Feliz programación y nos vemos en clase!


