"""Structured logging configured for Azure Monitor / App Insights ingestion.

Emits JSON lines to stdout so an Azure Monitor Agent / OpenTelemetry
Collector sidecar can ship them to Application Insights without any
code-level Azure SDK dependency -- keeping the service cloud-portable
while still satisfying the observability-consolidation goal in the JD.
"""
import logging
import sys

import structlog


def configure_logging(environment: str) -> None:
    """Configure structlog for JSON (prod) or console (dev) rendering.

    Args:
        environment: Deployment environment name; "dev" gets a human
            readable console renderer, anything else gets JSON suitable
            for Azure Monitor / Application Insights log ingestion.
    """
    renderer = (
        structlog.dev.ConsoleRenderer()
        if environment == "dev"
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            renderer,
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a structlog logger bound to `name`."""
    return structlog.get_logger(name)
