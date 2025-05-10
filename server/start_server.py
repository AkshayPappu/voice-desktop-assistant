import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

if __name__ == "__main__":
    logger.info("Starting server with WebSocket endpoint at ws://localhost:8000/ws")
    uvicorn.run(
        "api:app",
        host="localhost",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info",
        ws="websockets"  # Explicitly enable WebSocket support
    ) 