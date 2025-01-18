
# Brochurify

Welcome to Brochurify! This project is designed to simplify website data extraction and summarization, providing a streamlined way to generate brochures from web content.

## Table of Contents

1. [About the Project](#about-the-project)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Project Structure](#project-structure)

---

## About the Project

An innovative project that simplifies website data extraction and summarization.

Key Technologies:
- FastAPI
- WebSockets for real-time communication
- LLMs for summarization and brochure generation

---

## Features

- **Webpage Summarization:** Provide a URL and get a concise summary.
- **Brochure Creation:** Generate a visually appealing, structured brochure from a website.
- **Real-time Processing:** Instant feedback using WebSockets.

---

## Installation

Follow these steps to set up the project locally:

### 1. **Clone the Repository:**

   ```bash
   git clone https://github.com/itsnotvahid/Brochurify.git
   cd Brochurify
   ```

### 2. **Create a Virtual Environment:**

   It's recommended to use a virtual environment to manage dependencies.

   On **Linux/macOS**, run:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

### 3. **Install Dependencies:**

   Ensure you have `pip` installed. Then, install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

### 4. **Create a `.env` File:**

   The application requires certain environment variables. Create a `.env` file in the root directory with the following content:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   SOCKET_HOST=127.0.0.1
   SOCKET_PORT=8912
   STATIC_HOST=127.0.0.1
   STATIC_PORT=8913
   ```

   Replace `your_openai_api_key_here` with your actual OpenAI API key.

---

## Usage

To run the application:

### 1. **Start the FastAPI Server with the `run.sh` script:**

   Make sure the `run.sh` script is executable. If not, change its permissions:

   ```bash
   chmod +x run.sh
   ```

   Now, run the script:

   ```bash
   ./run.sh
   ```

### 2. **Access the Application:**

   Open your browser and navigate to `"http://STATIC_HOST:STATIC_PORT" to interact with the application.

---

## Project Structure

- `main.py`: The entry point of the application.
- `api/`: Contains the API endpoints.
- `services/`: Includes the core logic for summarization and brochure generation.
- `static/`: Holds AI GENERATED static files.

---
