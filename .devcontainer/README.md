# Dev Container Setup

This project includes a Dev Container configuration to help you easily set up and work within a consistent development environment using Docker and Visual Studio Code.

## Key Points

- **Simplified Setup:** The Dev Container provides an isolated and reproducible environment, making it easy to start developing without manually configuring your local machine.

- **Faster Environment Resolution with Mamba:** Instead of using `conda`, this setup uses **mamba**—a drop-in replacement that significantly speeds up environment resolution and package installation.

- **Accessing Host Services:** 
  When working inside the container, any services running on your host machine should be accessed via `host.docker.internal` rather than `localhost`.

  **Example:**
  If you're running [Ollama](https://ollama.com) on your host, you can access it inside the container at: [http://host.docker.internal:11434](http://host.docker.internal:11434) instead of [http://localhost:11434](http://localhost:11434)


## Getting Started

To use the Dev Container:

1. Make sure you have [Docker](https://www.docker.com/products/docker-desktop) and [Visual Studio Code](https://code.visualstudio.com/) with the **Dev Containers** extension installed.
2. Open the project folder in VS Code.
3. When prompted, reopen in the Dev Container environment.

You're now ready to start developing in a fully configured and isolated environment!
