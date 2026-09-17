"""Application configuration loaded from environment variables.

Follows the twelve-factor pattern: all runtime configuration is sourced
from the environment (or a local .env for development) and never
hardcoded, so the same image is promotable across dev/stage/prod.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings.

    Attributes:
        app_name: Human-readable service name, used in logs and OpenAPI.
        environment: Deployment environment name (dev/stage/prod).
        entra_tenant_id: Azure Entra ID (Azure AD) tenant GUID.
        entra_client_id: Application (client) ID registered in Entra ID.
        entra_authority: OAuth 2.0 / OIDC authority base URL.
        jwt_audience: Expected `aud` claim on inbound access tokens.
        jwt_algorithms: Accepted JWS signing algorithms for Entra ID tokens.
        eventhub_connection_str: Azure Event Hubs namespace connection string.
        eventhub_name: Target Event Hub (topic-equivalent) name.
        kafka_bootstrap_servers: Kafka-compatible bootstrap servers (Event
            Hubs exposes a Kafka-compatible endpoint on port 9093).
        signalr_connection_str: Azure SignalR Service connection string.
        rust_engine_grpc_target: host:port of the Tonic gRPC risk engine.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="WES_")

    app_name: str = "wes-api"
    environment: str = "dev"

    entra_tenant_id: str = "00000000-0000-0000-0000-000000000000"
    entra_client_id: str = "00000000-0000-0000-0000-000000000000"
    entra_authority: str = "https://login.microsoftonline.com"
    jwt_audience: str = "api://wes-api"
    jwt_algorithms: list[str] = ["RS256"]

    eventhub_connection_str: str = ""
    eventhub_name: str = "wes-workstream-events"
    kafka_bootstrap_servers: str = "localhost:9093"

    signalr_connection_str: str = ""

    rust_engine_grpc_target: str = "localhost:50051"


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()
