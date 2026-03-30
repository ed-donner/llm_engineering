# 🚀 AI Career Planner

> An AI-powered tool that analyzes real job market demands and generates a personalized study plan for your target career.

**Stop guessing what to learn.** This project uses live job data + AI to tell you exactly what skills are in demand — then builds you a roadmap to get there.

---
![ai-career-planner](assets/ai-career-planner-demo.png)

## 📌 The Problem

Most learners struggle with three things:

- ❓ **What** skills to learn for a target career
- ❓ **Whether** those skills are actually in demand right now
- ❓ **How** to structure a learning roadmap that makes sense

---

## 💡 The Solution

AI Career Planner tackles this by:

1. **Fetching real job listings** from the live market (configurable by country)
2. **Identifying in-demand skills** from actual job descriptions
3. **Generating a custom AI-driven study plan** tailored to skill gaps

---

## ✨ Features

### 🔍 Live Job Search (via JSearch / RapidAPI)
- Fetches real job listings filtered by role and location
- Configurable filters: country, date range (e.g. posted within last week)
- Extracts: job title, company name, full job description

### 📊 Structured Data Extraction
Converts raw API responses into clean, usable Python objects:

```json
{
  "title": "Machine Learning Engineer",
  "company": "Company Name",
  "description": "Job description text..."
  ...
}
```

### 🧠 AI Career Intelligence
- Identifies most demanded skills and your personal skill gaps

### 📚 Study Plan Generator
- Generates a step-by-step learning roadmap
- Prioritizes skills by market demand
- Suggests projects to build along the way

---

## 🏗️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| Requests | API calls |
| RapidAPI (JSearch) | Live job listings |
| python-dotenv | Environment/key management |
| Google Gemini API | AI analysis |

---

## ⚙️ How It Works

```
User query (e.g. "machine learning engineer in singapore")
        ↓
  JSearch API call
        ↓
  Extract: title, company, company website, job apply link, description
        ↓
  Structured job dataset
        ↓
  AI provide study plan based on current market demand
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/waijian1/AI-career-planner.git
cd AI-career-planner
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Set up API keys

Create a `.env` file in the project root:

```env
X_RAPID_API_KEY=your_rapidapi_key
GOOGLE_API_KEY=your_google_api_key
```

> 🔑 Get your RapidAPI key at [rapidapi.com](https://rapidapi.com) — search for **JSearch**.

### 4. Run the Gradio App

```bash
uv run -m ai_career_planner
```

### 5. Enjoy your career planning with the Gradio App !

---

## 🔮 Roadmap

- [x] Job search API integration
- [x] Structured data extraction
- [x] Aggregate most in-demand skills
- [x] Generate personalized study plans
- [x] Build Gradio UI
- [x] Deploy as a web app

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 👨‍💻 Author

**Lim Wai Jian**
GitHub: [@waijian1](https://github.com/waijian1)

---

## ⭐ Support

If you find this useful, please consider:

- Starring ⭐ the repo
- Sharing it with others
- Contributing improvements via pull requests

Every bit of support helps keep the project going! 🚀