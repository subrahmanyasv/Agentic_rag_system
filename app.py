"""ASGI entry point and local development server launcher."""

import logging
import os

from app.main import app

__all__ = ["app"]

LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure concise console logs when the application is run directly."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run() -> None:
    """Start the API server using environment-configurable settings."""
    configure_logging()
    host = os.getenv("SERVER_HOST", "127.0.0.1")

    try:
        port = int(os.getenv("SERVER_PORT", "8000"))
        LOGGER.info("Starting API server on http://%s:%s", host, port)

        import uvicorn

        uvicorn.run(app, host=host, port=port)
    except Exception:
        LOGGER.exception("API server failed to start or stopped unexpectedly")
        raise
    else:
        LOGGER.info("API server stopped")


if __name__ == "__main__":
    run()
