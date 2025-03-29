.PHONY: install run dev docker-build docker-run test clean

# Install project dependencies
install:
	pip install -r requirements.txt

# Run the application
run:
	python run.py

# Run with development settings (enables hot-reloading)
dev:
	PYTHON_ENV=development python run.py

# Build Docker container
docker-build:
	docker build -t ai-code-converter .

# Run Docker container
docker-run:
	docker run -p 7860:7860 --env-file .env ai-code-converter

# Run tests
test:
	python -m pytest tests/

# Clean Python cache and build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

# Generate documentation diagrams
docs-diagrams:
	cd docs && python -c "import mermaid_generator; mermaid_generator.generate_diagrams()"