#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from app import launch

load_dotenv()

if __name__ == "__main__":
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set in .env")
        exit(1)

    print("Starting Unit Test Generator...")
    print("Open http://localhost:7860 in your browser")
    launch()
