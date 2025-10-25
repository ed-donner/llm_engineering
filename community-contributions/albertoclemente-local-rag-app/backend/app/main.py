"""
Main FastAPI application entry point.
Configures the app, middleware, routes, and lifecycle events.
"""

import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from app.api_complete import router as api_router
from app.ws import router as ws_router
from app.settings import get_settings, Settings
from app.diagnostics import setup_logging, get_logger

# Import services for initialization
from app.storage import get_document_storage_service
from app.embeddings import get_embedder_service
from app.qdrant_index import get_qdrant_service
from app.retrieval import get_retrieval_service
from app.llm import get_llm_service

# Global logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management"""
    logger.info("Starting Local RAG WebApp...")
    
    # Initialize settings
    settings = get_settings()
    logger.info(f"Using profile: {settings.profile}")
    logger.info(f"Data directory: {settings.data_dir}")
    
    # Ensure data directories exist
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.library_raw_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.library_parsed_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.config_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)
    logger.info("Data directories created")
    
    # Initialize services
    try:
        # Initialize storage service
        logger.info("Initializing document storage...")
        storage_service = await get_document_storage_service()
        logger.info("✅ Document storage initialized")
        
        # Initialize embedding service
        logger.info("Initializing embedding service...")
        embedder_service = await get_embedder_service()
        logger.info("✅ Embedding service initialized")
        
        # Initialize Qdrant service
        logger.info("Initializing Qdrant vector database...")
        qdrant_service = await get_qdrant_service()
        qdrant_health = await qdrant_service.health_check()
        if qdrant_health.get("healthy", False):
            logger.info("✅ Qdrant service initialized and healthy")
        else:
            logger.warning("⚠️ Qdrant service initialized but may not be healthy")
        
        # Initialize retrieval service
        logger.info("Initializing retrieval service...")
        retrieval_service = await get_retrieval_service()
        logger.info("✅ Retrieval service initialized")
        
        # Initialize LLM service
        logger.info("Initializing LLM service...")
        llm_service = await get_llm_service()
        llm_health = await llm_service.health_check()
        if llm_health.get("healthy", False):
            model_name = llm_health.get("model", "unknown")
            logger.info(f"✅ LLM service initialized with model: {model_name}")
        else:
            logger.warning("⚠️ LLM service initialized but may not be healthy")
        
        logger.info("🚀 All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        logger.warning("Application will start but some features may not work")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Local RAG WebApp...")
    
    # Clean up services
    try:
        # Close LLM service connections
        llm_service = await get_llm_service()
        if hasattr(llm_service, 'close'):
            await llm_service.close()
        
        logger.info("✅ Services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Local RAG WebApp",
        description="Local-only Retrieval-Augmented Generation web application",
        version="1.0.0",
        docs_url=None,  # Disable default docs
        redoc_url="/api/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # CORS middleware for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    app.include_router(ws_router)
    
    # Custom Swagger UI with better styling (always available for local-only app)
    @app.get("/api/docs", include_in_schema=False, response_class=HTMLResponse)
    async def custom_swagger_ui_html():
        """Custom Swagger UI with overflow fixes"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{app.title} - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <style>
        /* Fix text overflow issues */
        .swagger-ui .response-col_description__inner div.markdown,
        .swagger-ui .response-col_description__inner div.renderedMarkdown,
        .swagger-ui .response-col_description__inner p,
        .swagger-ui .response-col_description__inner pre {{
            max-width: 100%;
            overflow-x: auto;
            word-wrap: break-word;
            white-space: pre-wrap;
        }}
        
        /* Fix code blocks */
        .swagger-ui pre {{
            max-width: 100%;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        /* Fix example responses */
        .swagger-ui .example,
        .swagger-ui .example pre {{
            max-width: 100%;
            overflow-x: auto;
        }}
        
        /* Fix long URLs */
        .swagger-ui .opblock-summary-path,
        .swagger-ui .opblock-body code {{
            word-break: break-all;
        }}
        
        /* Improve table responsiveness */
        .swagger-ui table {{
            display: block;
            max-width: 100%;
            overflow-x: auto;
        }}
        
        /* Better scrolling for responses */
        .swagger-ui .responses-inner {{
            max-width: 100%;
            overflow-x: auto;
        }}
        
        /* Container width control */
        .swagger-ui .wrapper {{
            max-width: 1460px;
            margin: 0 auto;
            padding: 0 20px;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        const ui = SwaggerUIBundle({{
            url: "{app.openapi_url}",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout",
            defaultModelsExpandDepth: 1,
            defaultModelExpandDepth: 1,
            docExpansion: "list",
            displayRequestDuration: true,
            filter: true,
            tryItOutEnabled: true,
        }})
    </script>
</body>
</html>
            """
    
    # Serve frontend static files (in production)
    if not settings.debug:
        frontend_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
        if frontend_dir.exists():
            app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "app": "Local RAG WebApp"}
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    
    return app


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    settings = get_settings()
    
    # Create app
    app = create_app()
    
    # Run server
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info" if settings.debug else "warning",
        reload=settings.debug,
        access_log=settings.debug
    )


# Create app instance with environment-aware initialization
# This prevents unwanted startup during test imports
import os
if os.environ.get('RAG_TEST_MODE') == '1':
    # In test mode, create a minimal app without full initialization
    from fastapi import FastAPI
    app = FastAPI(title="RAG Test Mode")
else:
    # Normal mode - full app creation
    app = create_app()


if __name__ == "__main__":
    main()
