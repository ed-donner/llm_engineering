# InterView-Coder 2.0

InterView-Coder 2.0 captures coding problems directly from your screen, extracts text using OCR, and generates optimized solutions using a local LLM.

## Features

* Region-based screen capture with global hotkeys.
* OCR-powered problem extraction using Tesseract.
* AI-generated solutions via Ollama:

  * Problem analysis
  * Brute-force, improved, and optimal approaches
  * Time & space complexity
  * JavaScript implementations
* Automatic clipboard copy of the final solution.

## Hotkeys

| Hotkey             | Action                                      |
| ------------------ | ------------------------------------------- |
| `Ctrl + Shift + S` | Set top-left capture corner                 |
| `Ctrl + Shift + D` | Set bottom-right capture corner             |
| `Ctrl + Shift + A` | Run Capture → OCR → AI → Clipboard pipeline |

## Installation

### Prerequisites

```bash
brew install tesseract
```

Install Ollama and pull the required model:

```bash
ollama pull gemma4:latest
```

### Setup

```bash
git clone <repo-url>
cd <repo-name>

pip install -r requirements.txt
# or
uv sync
```

If necessary, update the Tesseract path in `ocr/reader.py`.

## Project Structure

```text
ai/        AI prompting and Ollama integration
capture/   Screen capture and region selection
ocr/       OCR processing
ui/        Popup interface
utils/     Utility functions
temp/      Temporary screenshots
main.py    Application entry point
```

## Disclaimer

For educational and competitive programming practice only. Ensure usage complies with the rules of the platform you are using.
