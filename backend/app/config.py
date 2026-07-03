from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Workshop Tool API"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000

    # Comma-separated list of allowed CORS origins (Flutter web/app URLs).
    # Defaults cover common local dev ports; override via CORS_ORIGINS env.
    # "*" is allowed for local dev but should never be used in production.
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:54687,http://127.0.0.1:54687"
    )

    claude_api_key: str = ""
    claude_base_url: str = "https://api.anthropic.com"
    # Model for idea clustering. Sonnet 4.5 balances quality and cost; swap
    # via CLAUDE_MODEL if Anthropic retires this dated ID.
    claude_model: str = "claude-sonnet-4-5-20250929"
    database_url: str = ""
    firebase_credentials_path: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
