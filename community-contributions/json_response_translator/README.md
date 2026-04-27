# JSON Spanish Translator API

A simple FastAPI-based microservice that translates **JSON field names
and their corresponding values into Spanish** while preserving the exact
structure of the original JSON.

------------------------------------------------------------------------

## 🚀 Features

-   Accepts any valid JSON payload
-   Translates field names and values into Spanish
-   Maintains original JSON structure
-   Returns strictly valid JSON
-   Deterministic output (`temperature=0`)
-   Swagger UI auto-generated documentation

------------------------------------------------------------------------

## 🏗️ Project Structure

    spanish-json-translator/
    │
    ├── main.py
    ├── requirements.txt
    ├── .env
    └── README.md

------------------------------------------------------------------------

## ⚙️ Requirements

-   Python 3.9+
-   OpenAI API Key

------------------------------------------------------------------------

## 📦 Installation

### 1️⃣ Create Virtual Environment (Recommended)

``` bash
python -m venv venv
```

Activate it:

**Windows**

``` bash
venv\Scripts\activate
```

**Mac/Linux**

``` bash
source venv/bin/activate
```

### 2️⃣ Install Dependencies

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🔐 Environment Variables

Create a `.env` file:

    OPENAI_API_KEY=your_openai_api_key_here

------------------------------------------------------------------------

## ▶️ Running the Application

``` bash
uvicorn main:app --reload
```

API will be available at:

    http://127.0.0.1:8000

Swagger documentation:

    http://127.0.0.1:8000/docs

------------------------------------------------------------------------

## 📡 API Endpoint

### POST `/translate-json`

#### Request Example

``` json
{
  "name": "John Doe",
  "city": "New York",
  "orderStatus": "Pending"
}
```

#### Response Example

``` json
{
  "nombre": "Juan Doe",
  "ciudad": "Nueva York",
  "estadoPedido": "Pendiente"
}
```

------------------------------------------------------------------------

## 🧠 How It Works

1.  Receives JSON payload
2.  Converts JSON into string
3.  Sends request to OpenAI model (`gpt-4.1-nano`)
4.  Enforces structured JSON output
5.  Returns translated JSON

------------------------------------------------------------------------

## 🐳 Optional Docker Setup

### Dockerfile

``` dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run

``` bash
docker build -t spanish-translator .
docker run -p 8000:8000 --env-file .env spanish-translator
```

------------------------------------------------------------------------