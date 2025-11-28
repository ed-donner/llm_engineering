# 🖥️ Tutorial de la Línea de Comandos para Usuarios de Windows

Este tutorial completo está diseñado para estudiantes que nunca han usado la **línea de comandos (Command Prompt o PowerShell)** en Windows. Aprenderás los conceptos básicos necesarios para trabajar con entornos de Python, módulos y notebooks dentro de **Cursor** (basado en VSCode), utilizando un entorno creado por `uv`.

---

## 📘 Parte 1: Introducción — ¿Qué es la línea de comandos?

La **línea de comandos** es una forma de interactuar con tu computadora escribiendo instrucciones en texto, en lugar de usar el ratón. Es una herramienta poderosa que te permite controlar el sistema operativo directamente.

### 🪟 En Windows existen varias opciones:
- **Símbolo del sistema (Command Prompt o CMD)**
- **PowerShell** (más moderno y avanzado)
- **Terminal de Windows** (una aplicación que puede contener varias pestañas de PowerShell, CMD o incluso WSL/Linux)

### 🧭 En este curso:
- Utilizaremos el **PowerShell** del sistema para la configuración inicial del entorno.
- Luego trabajaremos dentro del **Terminal integrado de Cursor**, que ofrece la misma funcionalidad.

> ⚡ Abre PowerShell: Presiona `Win + S`, escribe **PowerShell** y presiona `Enter`.

Verás una ventana con un texto similar a:
```powershell
PS C:\Users\tu_nombre>
```
Ahí es donde escribirás tus comandos.

---

## 📁 Parte 2: Conceptos preliminares — Archivos y directorios

En la línea de comandos, trabajas **dentro de carpetas** (llamadas *directorios*). Tu posición actual dentro del sistema se llama **directorio de trabajo actual**.

### 🔍 Ver la ubicación actual
```powershell
pwd
```
**Ejemplo:**
```powershell
PS C:\Users\Joxemi> pwd

Path
----
C:\Users\Joxemi
```

### 📂 Listar el contenido de un directorio
```powershell
ls
```
**Ejemplo:**
```powershell
PS C:\Users\Joxemi> ls
```
Salida típica:
```
    Directory: C:\Users\Joxemi

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----          21/04/2025     09:00                Documents
d----          21/04/2025     09:01                Downloads
-a---          20/04/2025     17:00             53 notas.txt
```

### 🧭 Cambiar de directorio
```powershell
cd nombre_carpeta
```
**Ejemplo:**
```powershell
cd Documents
```

Para volver al directorio anterior:
```powershell
cd ..
```
Para volver al inicio:
```powershell
cd ~
```

### 📄 Ver el contenido de un archivo
```powershell
type nombre_archivo.txt
```
**Ejemplo:**
```powershell
type notas.txt
```

---

### 🧠 Ejercicios
1. Abre PowerShell y ejecuta `pwd`.
2. Usa `ls` para listar los archivos.
3. Entra en la carpeta `Documents`.
4. Vuelve al directorio anterior con `cd ..`.
5. Crea un archivo de texto en el Bloc de notas, guárdalo y míralo con `type`.

---

## ⚙️ Parte 3: Comandos útiles — Crear, copiar, mover y borrar

### 🗂️ Crear un nuevo directorio
```powershell
mkdir nueva_carpeta
```
**Ejemplo:**
```powershell
mkdir proyecto_python
```

### 📝 Crear un archivo vacío
```powershell
New-Item archivo.txt
```

### 🧹 Eliminar archivos o carpetas
Eliminar archivo:
```powershell
rm archivo.txt
```
Eliminar carpeta con su contenido:
```powershell
rm -r carpeta
```
> ⚠️ No hay papelera. Los archivos se eliminan permanentemente.

### 🔀 Mover o renombrar
Renombrar:
```powershell
mv viejo.txt nuevo.txt
```
Mover a otra carpeta:
```powershell
mv archivo.txt carpeta/
```

### 📋 Copiar archivos o carpetas
```powershell
cp archivo.txt copia.txt
cp -r carpeta1 carpeta2
```

### 📎 Extensiones de archivos
| Extensión | Tipo de archivo |
|------------|----------------|
| `.txt`     | Texto plano |
| `.py`      | Script de Python |
| `.csv`     | Datos tabulares |
| `.json`    | Datos estructurados |
| `.md`      | Markdown |

**Ejemplo:**
```powershell
mv datos datos.json
```

---

### 🧠 Ejercicios
1. Crea una carpeta llamada `curso_python`.
2. Entra en ella y crea un archivo `notas.txt`.
3. Cópialo a `backup.txt`.
4. Renómbralo a `resumen.txt`.
5. Elimínalo.

---

## 🔒 Parte 4: Avanzado — Archivos ocultos, permisos e integración con OneDrive

### 🙈 Archivos ocultos
Algunos archivos están ocultos (como configuraciones del sistema). Para verlos:
```powershell
ls -Force
```

### 🔐 Permisos de archivo
Cada archivo tiene permisos de lectura/escritura. Para verlos:
```powershell
ls -l
```

Para cambiar permisos (avanzado):
```powershell
icacls archivo.txt /grant Usuario:F
```
> `F` significa control total. Usa con precaución.

### ☁️ OneDrive y sincronización
En Windows, las carpetas **Documentos**, **Escritorio** y **Imágenes** pueden estar sincronizadas con **OneDrive**.

Ruta típica de OneDrive:
```powershell
C:\Users\tu_usuario\OneDrive\Documentos
```

Esto significa que tus archivos se suben automáticamente a la nube. Si trabajas desde Cursor, asegúrate de que tus proyectos estén **locales** si no deseas sincronización.

Puedes verificar si un archivo está sincronizado (icono de nube o check verde en el Explorador).

---

## 🧩 Parte 5: Ejercicios prácticos

### 🧱 Ejercicio 1 — Crear un mini entorno de trabajo
1. Abre PowerShell.
2. Ve a tu carpeta de usuario:
   ```powershell
   cd ~
   ```
3. Crea una carpeta `curso_terminal`.
4. Entra en ella y crea un archivo `intro.txt`:
   ```powershell
   echo "Hola desde PowerShell" > intro.txt
   ```
5. Muestra su contenido con `type intro.txt`.

### 🧱 Ejercicio 2 — Simular un proyecto Python
1. Crea una carpeta `mi_proyecto`.
2. Dentro, crea una subcarpeta `src` y un archivo `main.py`:
   ```powershell
   mkdir src
   New-Item src\main.py
   ```
3. Copia `main.py` en una carpeta llamada `backup`.
4. Muestra la estructura completa:
   ```powershell
   ls -Recurse
   ```
5. Elimina la carpeta `backup`.

---

## ✅ Resumen final
Ahora sabes cómo:
- Navegar por carpetas (`cd`, `ls`, `pwd`)
- Crear, copiar, mover y eliminar archivos
- Ver archivos ocultos y cambiar permisos
- Entender cómo funciona OneDrive

Estas habilidades son fundamentales para desenvolverte en entornos de desarrollo y trabajar con Python y Cursor de manera profesional.

