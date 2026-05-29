from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    grafana_url: str = ""
    grafana_api_token: str = ""
    capture_interface: str = "en0"
    port: int = 8000
    frontend_url: str = "http://localhost:5173"
    db_path: str = "data/netsight.db"

    @property
    def grafana_enabled(self) -> bool:
        return bool(self.grafana_url and self.grafana_api_token)

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


settings = Settings()
