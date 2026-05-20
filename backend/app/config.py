from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Workshop Tool API"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000

    claude_api_key: str = ""
    claude_base_url: str = "https://api.anthropic.com"
    database_url: str = ""
    firebase_credentials_path: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
