# Job Matcher

**Live App:** https://davenjeru--job-search-service-web-ui.modal.run

**Repository:** https://github.com/davenjeru/job_matcher

An AI-powered job search assistant that matches your resume to relevant job listings using semantic search and generates tailored cover letters.

## Features

- **Resume Parsing** - Extracts skills, experience, and job titles from your resume using GPT-4o-mini
- **Semantic Job Matching** - Uses RAG (Retrieval-Augmented Generation) with ChromaDB and sentence-transformers to find jobs that match your profile
- **Cover Letter Generation** - Automatically generates personalized cover letters tailored to each job
- **Push Notifications** - Sends Pushover notifications for high-scoring matches (80%+)
- **Real-time Agent Activity** - Watch the AI agents work in real-time through the activity log

## Architecture

The application uses a multi-agent architecture:

| Agent | Purpose |
|-------|---------|
| **ResumeAgent** | Parses resume text into a structured profile |
| **JobMatchAgent** | Finds matching jobs using vector similarity search |
| **CoverLetterAgent** | Generates tailored cover letters |
| **NotificationAgent** | Sends push notifications for top matches |