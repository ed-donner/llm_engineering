# Reddit Post Analyzer – GPT & Open Source Approaches

This project consists of two Jupyter notebooks that demonstrate different methods for analyzing Reddit post data:

- **Day 1:** `Day1_RedditAnalysis_gpt.ipynb` – Uses GPT-based sentiment and insight extraction from Reddit posts and comments.
- **Day 2:** `day2_RedditAnalysis_opensource.ipynb` – Implements an open-source alternative for Reddit data processing and basic sentiment/thematic analysis.

---

## 📌 Features

- Reddit post and comment scraping using PRAW  
- GPT-based sentiment summarization and insight structuring (Day 1)  
- Open-source sentiment and thematic analysis pipeline (Day 2)  
- Markdown-formatted output suitable for reporting

---

## 🛠️ Setup Instructions

### Reddit API Credentials Setup

To access Reddit data, you need to create a Reddit app and obtain credentials:

#### Steps to Get Your Reddit API Keys:

1. Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).
2. Scroll to the bottom and click **“create another app”** or **“create app”**.
3. Choose the **“script”** option.
4. Fill in the following fields:
   - **name:** e.g., Reddit Analyzer  
   - **redirect uri:** `http://localhost:8080`  
   - **description:** *(optional)*
5. After creating the app, you will get:
   - **client ID** (displayed under the app name)
   - **client secret**
6. Keep note of your Reddit **username** and **password** (these are used with script apps)

#### Store your credentials in a `.env` file:

Create a `.env` file in the root directory with the following format:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_custom_user_agent
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

These will be securely loaded into your script using the `dotenv` package.

---

## 🚀 Running the Notebooks

Make sure to activate your virtual environment (if applicable), install dependencies, and run the notebooks cell by cell in **Jupyter Lab** or **VS Code**.

---
