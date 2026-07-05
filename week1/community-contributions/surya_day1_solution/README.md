# LLM-Powered Interview Prep Question Generator

## Overview

This is a small tool that helps you prepare for technical interviews.  
You type a topic (for example: “binary search trees”, “system design basics”, or “SQL joins”), and the tool generates a set of interview-style questions with short answers.

## Features

- Ask for any CS / ML / software engineering topic.  
- Generates 5 interview-style questions for that topic.  
- Provides concise answers (2–4 sentences) for each question.  
- Outputs everything in Markdown so it is easy to read and save as notes.

## How it works

- Loads your LLM API key from a `.env` file.  
- Asks you for a topic using a simple `interview_questions()` prompt.  
- Sends a system prompt that tells the model to act like an interview coach.  
- Sends your topic as the user message.  
- Displays the model’s Q&A output as formatted Markdown.



