#!/bin/bash

echo "Starting AI Tutor..."
echo "Use the url http://localhost:8501 to access the app"
echo ""

cd "$(dirname "$0")"
streamlit run day5_task.py
