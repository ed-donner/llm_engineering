# Dev Container Setup

This project includes a Dev Container configuration to help you easily set up and work within a consistent development environment using Docker and Visual Studio Code.

## Key Points

- **Simplified Setup:** The Dev Container provides an isolated and reproducible environment, making it easy to start developing without manually configuring your local machine.

- **Using Jupyter Notebooks:**  
  The Dev Container is configured to work seamlessly with Jupyter notebooks. You can run and edit notebooks directly within the container environment by navigating to the notebook files in the VS Code file explorer and opening them. 


- **Faster Environment Resolution with Mamba:** Instead of using `conda`, this setup uses **mamba**—a drop-in replacement that significantly speeds up environment resolution and package installation.

- **Accessing Host Services:** 
  When working inside the container, any services running on your host machine should be accessed via `host.docker.internal` rather than `localhost`.

  **Example:**
  If you're running [Ollama](https://ollama.com) on your host, you can access it inside the container at: [http://host.docker.internal:11434](http://host.docker.internal:11434) instead of [http://localhost:11434](http://localhost:11434)

- **Running System Commands from Notebooks:**  
  Some Jupyter notebooks may include shell commands that are meant to run on the **host machine**, not inside the container.

  **Example:**  
  Running the following in a notebook cell **will not work** inside the container:
  ```python
  !ollama pull llama3.2
  ```
  Instead, open a terminal on your host machine and run:
  ```bash
  ollama pull llama3.2
  ```

  Be sure to skip such blocks in notebooks when running inside the container, and execute them on the host when needed.

## Getting Started

To use the Dev Container:

1. Make sure you have [Docker](https://www.docker.com/products/docker-desktop) and [Visual Studio Code](https://code.visualstudio.com/) with the **Dev Containers** extension installed.
2. Open the project folder in VS Code.
3. When prompted, reopen in the Dev Container environment.

You're now ready to start developing in a fully configured and isolated environment!
