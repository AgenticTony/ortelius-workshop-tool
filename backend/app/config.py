from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Workshop Tool API"
    # Debug must be opt-in — never the shipped default. A production app that
    # boots with debug=True leaks stack traces and verbose logs.
    debug: bool = False
    # Deployment tier. "production" enables fail-fast validation below; dev/test
    # stay permissive so the app imports without a .env (tests mock the Claude
    # client and override the DB session).
    app_env: str = "dev"
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

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        """Fail fast in production if essential configuration is missing.

        A production process that boots without a database URL or Claude key is
        silently half-broken (every analyse call 503s, no persistence). Refuse
        to start instead, so a misconfigured deploy is loud at boot, not after
        a user hits the first broken route.
        """
        if self.app_env == "production":
            missing = [
                name
                for name, val in (
                    ("DATABASE_URL", self.database_url),
                    ("CLAUDE_API_KEY", self.claude_api_key),
                )
                if not val
            ]
            if missing:
                raise ValueError(
                    "Missing required settings for production: "
                    + ", ".join(missing)
                    + ". Set them via environment / .env before booting."
                )
            if "*" in self.cors_origin_list:
                raise ValueError(
                    "CORS_ORIGINS='*' is not permitted in production; "
                    "list the exact frontend origins."
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
