# InterView-Coder 2.0

InterView-Coder 2.0 is a high-performance tool designed to assist competitive programmers by automatically capturing coding problems from the screen, processing them via OCR and AI, and providing optimal solutions in real-time.

## 🚀 Features

- **Region-Based Screen Capture**: Define a specific screen area for problem extraction using hotkeys.
- **OCR Pipeline**: Integrated Tesseract OCR to convert screenshots into clean, editable text.
- **AI-Powered Solver**: Uses local LLMs (via Ollama) to analyze problems and provide:
  - Problem understanding.
  - Brute force, better, and optimal approaches.
  - Time and Space complexity analysis.
  - Clean JavaScript implementations for all approaches.
- **Instant Clipboard Integration**: Automatically copies the final solution to the clipboard upon completion.

## 📺 Demo

Check out the process in action:
[Watch Process Demo](Process.mov) (watch this after cloning the repository in your machine)
[if you are not in mac then first chnage .mov to .mp4 and then watch]

## ⌨️ Hotkeys

| Hotkey             | Action                                                                                                   |
| :----------------- | :------------------------------------------------------------------------------------------------------- |
| `Ctrl + Shift + S` | Set the **Top-Left** corner of the capture region                                                        |
| `Ctrl + Shift + D` | Set the **Bottom-Right** corner of the capture region                                                    |
| `Ctrl + Shift + A` | **Run Pipeline**: Capture $\rightarrow$ OCR $\rightarrow$ AI $\rightarrow$ Popup $\rightarrow$ Clipboard |

## 🛠️ Installation & Setup

### Prerequisites

- **macOS**: Optimized for macOS (requires `pyobjc` for stealth UI features).
- **Tesseract OCR**: Must be installed on your system.
  ```bash
  brew install tesseract
  ```
- **Ollama**: Required for local AI inference.
  - Install Ollama from [ollama.com](https://ollama.com).
  - Pull the required model:
    ```bash
    ollama pull gemma4:latest
    ```

### Setup

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or use uv
   uv sync
   ```
3. Ensure Tesseract path is correct in `ocr/reader.py` (defaults to `/opt/homebrew/bin/tesseract`).

## 📂 Project Structure

- `main.py`: The core orchestration engine and hotkey listener.
- `ai/`: AI logic, prompting, and Ollama API integration.
- `capture/`: Screen capture and region management.
- `ocr/`: Text extraction using Tesseract.
- `ui/`: Stealth popup window implementation.
- `utils/`: Text cleaning and helper utilities.
- `temp/`: Local storage for temporary screenshots.

## ⚠️ Disclaimer

This tool is intended for educational and competitive programming practice. Please ensure its use complies with the rules of the platform you are using.
