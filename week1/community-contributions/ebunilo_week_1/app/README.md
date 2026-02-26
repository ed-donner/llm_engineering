# Company Brochure Generator – Deployment

Web API for the Week 1 Day 5 business solution: generate a company brochure from a website URL.

## Quick start (local)

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- **Health:** http://localhost:8000/health  
- **Docs:** http://localhost:8000/docs  
- **Brochure:** `POST /brochure` with JSON: `{"company_name": "Hugging Face", "url": "https://huggingface.co"}`

---

## Deploy with Docker (private cloud server)

### 1. Build and run with Docker

On the server (or from a machine that will push the image):

```bash
cd week1/community-contributions/ebunilo_week_1/app
cp .env.example .env
# Set OPENAI_API_KEY in .env

docker build -t brochure-generator:latest .
docker run -d --name brochure-app -p 8000:8000 --env-file .env brochure-generator:latest
```

### 2. Deploy with Docker Compose

```bash
cd week1/community-contributions/ebunilo_week_1/app
cp .env.example .env
# Set OPENAI_API_KEY in .env

docker compose up -d
```

- App: http://YOUR_SERVER:8000  
- Health: http://YOUR_SERVER:8000/health  

### 3. Optional: reverse proxy (Nginx) on the same server

Example Nginx config to expose the app on port 80/443:

```nginx
# /etc/nginx/sites-available/brochure-app
server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/brochure-app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4. Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for brochure generation |
| `OPENAI_LINK_MODEL` | No | Model for link selection (default: gpt-4o-mini) |
| `OPENAI_BROCHURE_MODEL` | No | Model for brochure text (default: gpt-4o-mini) |
| `PORT` | No | Port inside container (default: 8000) |

---

## API

- **GET /health** – Liveness/readiness (e.g. for Kubernetes or load balancers).  
- **POST /brochure** – Body: `{"company_name": "<name>", "url": "<website URL>"}`. Returns `{"brochure": "<markdown string>"}`.

Example:

```bash
curl -X POST http://localhost:8000/brochure \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Hugging Face", "url": "https://huggingface.co"}'
```
