# AURA – Autonomous University Response Assistant

## Background

AURA (Autonomous University Response Assistant) started as an exercise in building intelligent agents and utilizing local large language models (LLMs). 

The original objective was to create a basic AI assistant capable of reasoning and routing tasks. As the development progressed through multiple phases, it evolved into a comprehensive, self-hosted personal AI assistant tailored specifically for college students, complete with a full-stack web interface and a Retrieval-Augmented Generation (RAG) pipeline for interacting with course materials.

## Features

* **Multi-Model Routing:** Automatically routes queries to the most appropriate local model (e.g., Llama 3.1 for general reasoning, Qwen 3 for coding).
* **Document Chat (RAG):** Allows users to upload PDF college notes and ask questions grounded entirely in their materials.
* **Task Management:** Tracks upcoming assignments, exams, and personal tasks.
* **Daily AI Summaries:** Generates daily morning summaries of upcoming tasks and sends them via Telegram.
* **Interactive Dashboard:** Provides a clean, responsive Next.js frontend for managing chats, documents, and tasks.
* **Dockerized Deployment:** Fully containerized backend and frontend for easy deployment and persistence.

## Tech Stack

* Python
* FastAPI
* SQLite (Database)
* ChromaDB (Vector Database)
* Ollama (Llama 3.1, Qwen 3)
* LangChain
* Next.js (TypeScript, Tailwind CSS)
* Docker

## What I Learned

This project provided practical experience with:

* Developing full-stack AI applications
* Implementing Retrieval-Augmented Generation (RAG) pipelines
* Architecting multi-model routing systems and agents using LangChain
* Building interactive frontends with Next.js and integrating them with FastAPI
* Setting up background scheduling (APScheduler) and Telegram Bot notifications
* Containerizing complex applications using Docker and Docker Compose

## Repository

[* Development Repository*](https://github.com/sohamkadu17/AURA)

## Future Improvements

Future versions will include real-time multi-agent collaboration, integration with university learning management systems (e.g., Canvas/Moodle), and an expanded mobile-friendly interface.
