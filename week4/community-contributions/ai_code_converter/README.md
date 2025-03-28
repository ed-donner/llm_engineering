# CodeXchange AI

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI/CD](https://github.com/alakob/ai_code_converter/actions/workflows/python-test.yml/badge.svg)](https://github.com/alakob/ai_code_converter/actions/workflows/python-test.yml)

A powerful tool for converting and executing code between different programming languages using AI models.

## Overview

CodeXchangeAI  is a Python application that leverages various AI models to translate code between programming languages while maintaining functionality and idiomatic patterns.

### Key Features

- Multi-language code conversion
- Real-time code execution
- Multiple AI model support (GPT, Claude, DeepSeek, GROQ, Gemini)
- File upload/download functionality
- Syntax highlighting
- Detailed logging system
- Docker support

## Quick Start

```bash
# Clone the repository
git clone git@github.com:alakob/ai_code_converter.git
cd ai_code_converter

# Configure environment
cp .env.example .env
# Edit .env with your API keys

```

### Using the Docker Wrapper Script (Recommended)

For a more convenient way to run the application with Docker, you can use the provided wrapper script:

```bash
# Make the script executable
chmod +x run-docker.sh

# Run the application
./run-docker.sh            # Build and run normally
./run-docker.sh -d         # Run in detached mode
./run-docker.sh -p 8080    # Run on port 8080
./run-docker.sh -s         # Stop the container
./run-docker.sh -h         # Show help message
```

## CI/CD Pipeline

CodeXchange AI uses GitHub Actions for continuous integration and deployment. The pipeline includes:

### Automated Testing
- Runs Python tests on multiple Python versions (3.9, 3.10, 3.11)
- Performs code linting and style checks
- Generates test coverage reports

### Docker Image Validation
- Builds the Docker image to verify Dockerfile integrity
- Performs vulnerability scanning with Trivy
- Validates container startup and dependencies

### Deployment Automation
- Automatically deploys to staging environment when changes are pushed to develop branch
- Creates production releases with semantic versioning
- Publishes Docker images to Docker Hub

### Setting Up for Development

To use the CI/CD pipeline in your fork, you'll need to add these secrets to your GitHub repository:

1. `DOCKERHUB_USERNAME`: Your Docker Hub username
2. `DOCKERHUB_TOKEN`: A Docker Hub access token (not your password)

See the [CI/CD documentation](docs/ci_cd_pipeline.md) for detailed setup instructions.

The wrapper script provides several options for customizing the Docker deployment:

```bash
Usage: ./run-docker.sh [OPTIONS]

Options:
  -b, --build        Build the Docker image without running the container
  -d, --detach       Run container in detached mode (background)
  -e, --env FILE     Specify an environment file (default: .env)
  -p, --port PORT    Specify the port to expose (default: 7860)
  -l, --logs         Follow the container logs after starting
  -s, --stop         Stop the running container
  -r, --restart      Restart the container
  -D, --down         Stop and remove the container
  -k, --keys         Check for API keys and show setup instructions if missing
  -h, --help         Display this help message
  -v, --version      Display script version
```

Examples:
- Run on a different port: `./run-docker.sh -p 8080`
- Run in background: `./run-docker.sh -d`
- Stop the application: `./run-docker.sh -s`
- View logs: `./run-docker.sh -l`

The application will be available at `http://localhost:7860`

### Manual Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
python run.py
```

### Using Make Commands

The project includes a Makefile with useful commands to streamline development:

```bash
# Install dependencies
make install

# Run the application
make run

# Run with development settings (hot-reloading)
make dev

# Build Docker container
make docker-build

# Run Docker container
make docker-run

# Or use the Docker wrapper script for more options
./run-docker.sh

# Run tests
make test

# Clean Python cache and build artifacts
make clean
```

## Basic Usage

1. Select source and target programming languages
2. Enter or upload source code
3. Choose AI model and temperature
4. Click "Convert" to translate the code
5. Use "Run" buttons to execute original or converted code
6. Download the results including compiled binaries (for compiled languages)

## Supported Languages

Currently supports 17 programming languages including Python, JavaScript, Java, C++, Julia, Go, Ruby, Swift, Rust, C#, TypeScript, R, Perl, Lua, PHP, Kotlin, and SQL.

See [Supported Languages](./docs/languages.md) for detailed information on each language.

## Documentation

For detailed documentation, please refer to the [docs](./docs) directory:

- [Supported Languages](./docs/languages.md) - Details on all supported programming languages
- [Configuration Guide](./docs/configuration.md) - How to configure the application
- [Development Guide](./docs/development.md) - Guide for developers extending the application
- [Contributing Guidelines](./docs/contributing.md) - How to contribute to the project
- [Project Structure](./docs/project_structure.md) - Overview of the codebase architecture
- [Architecture Diagram](./docs/architecture_diagram.md) - Visual representation of the application architecture

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude
- Google for Gemini
- DeepSeek and GROQ for their AI models
- The Gradio team for the web interface framework 