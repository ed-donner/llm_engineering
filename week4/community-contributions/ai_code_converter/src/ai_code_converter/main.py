"""Main entry point for the CodeXchange AI application."""

from src.ai_code_converter.app import CodeConverterApp
from src.ai_code_converter.utils.logger import setup_logger

def main():
    """Initialize and run the application."""
    # Initialize logger
    logger = setup_logger("ai_code_converter.main")
    
    try:
        logger.info("="*50)
        logger.info("Starting CodeXchange AI")
        logger.info("="*50)
        
        logger.info("Initializing application components")
        app = CodeConverterApp()
        
        logger.info("Starting Gradio interface")
        app.run(share=True)
        
    except Exception as e:
        logger.error("Application failed to start", exc_info=True)
        raise
    finally:
        logger.info("="*50)
        logger.info("Application shutdown")
        logger.info("="*50)

if __name__ == "__main__":
    main() 